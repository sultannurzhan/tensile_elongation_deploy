import os
import numpy as np
import cv2
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import traceback

# Initialize Flask
app = Flask(__name__, static_folder="build", static_url_path="")

# CORS: Allow frontend to communicate with backend
CORS(app, origins=[
    "https://tensileelongationdeploy.vercel.app",  # Vercel Frontend
    "https://tensileelongationdeploy-production.up.railway.app",  # Railway Backend
    "https://maitai.ltd"
])

# Directories
PHASE_MAP_IMG_FOLDER = "phase_map_img"
KAM_IMG_FOLDER = "KAM_img"
MORPHED_OUTPUT_FOLDER = "morphed_outputs"

os.makedirs(MORPHED_OUTPUT_FOLDER, exist_ok=True)

# Predefined Percentages
predefined_percentages = [5, 7.5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

def find_closest_images(percentage, image_type):
    if percentage in predefined_percentages:
        closest_lower = closest_upper = percentage
    else:
        closest_lower = max([p for p in predefined_percentages if p <= percentage])
        closest_upper = min([p for p in predefined_percentages if p >= percentage])

    folder = PHASE_MAP_IMG_FOLDER if image_type == "phase_map" else KAM_IMG_FOLDER

    if image_type == "phase_map":
        img_lower_path = os.path.join(folder, f"phase_map_{closest_lower}.png")
        img_upper_path = os.path.join(folder, f"phase_map_{closest_upper}.png")
    else:  
        img_lower_path = os.path.join(folder, f"KAM_image_{closest_lower}.png") 
        img_upper_path = os.path.join(folder, f"KAM_image_{closest_upper}.png")  

    if not os.path.exists(img_lower_path) or not os.path.exists(img_upper_path):
        return None, None, None, None

    return img_lower_path, img_upper_path, closest_lower, closest_upper

def generate_morphed_image(percentage, image_type):
    img_lower_path, img_upper_path, lower_perc, upper_perc = find_closest_images(percentage, image_type)

    if not img_lower_path or not img_upper_path:
        return None  

    img_lower = cv2.imread(img_lower_path)
    img_upper = cv2.imread(img_upper_path)

    if img_lower is None or img_upper is None:
        return None

    # Resize both images to match
    target_size = (img_lower.shape[1], img_lower.shape[0])  # (width, height)
    img_upper = cv2.resize(img_upper, target_size)

    # Ensure both images have the same color channels
    if len(img_lower.shape) == 2:
        img_lower = cv2.cvtColor(img_lower, cv2.COLOR_GRAY2BGR)
    if len(img_upper.shape) == 2:
        img_upper = cv2.cvtColor(img_upper, cv2.COLOR_GRAY2BGR)

    alpha = (percentage - lower_perc) / (upper_perc - lower_perc) if upper_perc != lower_perc else 0
    morphed_img = cv2.addWeighted(img_lower, 1 - alpha, img_upper, alpha, 0)

    output_path = os.path.join(MORPHED_OUTPUT_FOLDER, f"generated_{percentage}.png")
    cv2.imwrite(output_path, morphed_img)

    return output_path

@app.route("/generate_image", methods=["POST"])
def generate_image():
    try:
        data = request.json
        percentage = data.get("percentage")
        image_type = data.get("type")

        if percentage is None or image_type not in ["phase_map", "kam"]:
            return jsonify({"error": "Invalid request. Provide percentage and type."}), 400

        image_path = generate_morphed_image(percentage, image_type)

        if image_path is None:
            return jsonify({"error": "Could not generate image"}), 500

        return send_file(image_path, mimetype="image/png", as_attachment=True, download_name=f"elongation_{percentage}.png")

    except Exception as e:
        traceback.print_exc()  
        return jsonify({"error": str(e)}), 500

# Serve React Frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve the React frontend from the build folder."""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# Start Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
