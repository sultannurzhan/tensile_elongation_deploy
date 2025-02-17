import os
import numpy as np
import pickle
import cv2
import skimage.feature as skf
import tensorflow as tf
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from keras._tf_keras.keras.losses import MeanSquaredError

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

phase_map_model = tf.keras.models.load_model("models/elongation_model_phase_maps_morphed.h5", custom_objects={'mse': MeanSquaredError})
kam_model = tf.keras.models.load_model("models/elongation_model_KAM_morphed.h5", custom_objects={'mse': MeanSquaredError})

with open("pca_scalers/pca_phase_map_model_final.pkl", "rb") as f:
    pca_phase = pickle.load(f)
with open("pca_scalers/phase_map_scaler.pkl", "rb") as f:
    scaler_phase = pickle.load(f)

with open("pca_scalers/pca_KAM_model_final.pkl", "rb") as f:
    pca_kam = pickle.load(f)
with open("pca_scalers/KAM_scaler.pkl", "rb") as f:
    scaler_kam = pickle.load(f)

def extract_features(image_path, pca, scaler):
    """Extracts features, applies scaling & PCA transformation"""
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

    return feature_vector_pca

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

    prediction = phase_map_model.predict(features)[0][0]
    os.remove(filepath)  
    return jsonify({"prediction": round(float(prediction), 2)})

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

    prediction = kam_model.predict(features)[0][0]
    os.remove(filepath)
    return jsonify({"prediction": round(float(prediction), 2)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
