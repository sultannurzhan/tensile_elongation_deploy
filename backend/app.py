import os
import numpy as np
import pickle
import cv2
import skimage.feature as skf
import tensorflow.lite as tflite
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Initialize Flask
app = Flask(__name__, static_folder="build", static_url_path="")

# CORS: Allow frontend to communicate with backend
CORS(app, origins=[
    "https://tensileelongationdeploy.vercel.app",  # Vercel Frontend
    "https://tensileelongationdeploy-production.up.railway.app"  # Railway Backend
])

# Upload folder for processing images
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load TFLite models
phase_map_interpreter = tflite.Interpreter(model_path="models/elongation_model_phase_maps_morphed.tflite")
phase_map_interpreter.allocate_tensors()

kam_interpreter = tflite.Interpreter(model_path="models/elongation_model_KAM_morphed.tflite")
kam_interpreter.allocate_tensors()

# Load PCA scalers
with open("pca_scalers/pca_phase_map_model_final.pkl", "rb") as f:
    pca_phase = pickle.load(f)
with open("pca_scalers/phase_map_scaler.pkl", "rb") as f:
    scaler_phase = pickle.load(f)

with open("pca_scalers/pca_KAM_model_final.pkl", "rb") as f:
    pca_kam = pickle.load(f)
with open("pca_scalers/KAM_scaler.pkl", "rb") as f:
    scaler_kam = pickle.load(f)

# Feature Extraction
def extract_features(image_path, pca, scaler):
    img = cv2.imread(image_path)
    if img is None:
        return None
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (512, 512))

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
    lbp = skf.local_binary_pattern(gray, P=8, R=1, method="uniform")

    feature_vector = np.hstack([sobelx.flatten(), sobely.flatten(), lbp.flatten()])
    feature_vector = feature_vector.reshape(1, -1)

    feature_vector = scaler.transform(feature_vector)
    feature_vector_pca = pca.transform(feature_vector)

    return feature_vector_pca.astype("float32")

# TensorFlow Lite Prediction
def predict_with_tflite(interpreter, features):
    """Runs inference using a TFLite model."""
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]['index'], features)
    interpreter.invoke()
    prediction = interpreter.get_tensor(output_details[0]['index'])

    return prediction[0][0]

# API Route: Predict Phase Map
@app.route("/predict_phase_map", methods=["POST"])
def predict_phase_map():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    features = extract_features(filepath, pca_phase, scaler_phase)
    if features is None:
        return jsonify({"error": "Invalid image"}), 400

    prediction = predict_with_tflite(phase_map_interpreter, features)
    os.remove(filepath)
    return jsonify({"prediction": round(float(prediction), 2)})

# API Route: Predict KAM
@app.route("/predict_kam", methods=["POST"])
def predict_kam():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    features = extract_features(filepath, pca_kam, scaler_kam)
    if features is None:
        return jsonify({"error": "Invalid image"}), 400

    prediction = predict_with_tflite(kam_interpreter, features)
    os.remove(filepath)
    return jsonify({"prediction": round(float(prediction), 2)}))

# Serve React Frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    """Serves React static files from the build folder"""
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# Start Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
