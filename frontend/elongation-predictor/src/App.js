import { useState } from "react";
import './App.css';
import axios from "axios";

export default function ElongationPredictor() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedType, setSelectedType] = useState(null); 

  const handleTypeSelection = (type) => {
    setSelectedType(type);
    setImage(null);
    setPreview(null);
    setPrediction(null);
  };

  const handleImageChange = (event) => {
    const file = event.target.files[0];
    setImage(file);
    setPreview(URL.createObjectURL(file));
  };

  const handleSubmit = async () => {
    if (!image || !selectedType) return;
    setLoading(true);
    setPrediction(null);

    const formData = new FormData();
    formData.append("file", image);

    const endpoint =
      selectedType === "phase_map"
        ? "http://127.0.0.1:5000/predict_phase_map"
        : "http://127.0.0.1:5000/predict_kam";

    try {
      const response = await axios.post(endpoint, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setPrediction(response.data.prediction);
    } catch (error) {
      console.error("Error uploading image", error);
      setPrediction("Error: Unable to get prediction");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-darkPurple text-white flex flex-col items-center justify-center p-6">
      <h1 className="text-2xl font-bold mb-6">Tensile Elongation Predictor</h1>

      {!selectedType ? (
        <div className="flex gap-6">
          <button
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
            onClick={() => handleTypeSelection("kam")}
          >
            Upload KAM Image
          </button>
          <button
            className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
            onClick={() => handleTypeSelection("phase_map")}
          >
            Upload Phase Map
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <button
            className="mb-4 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition"
            onClick={() => setSelectedType(null)}
          >
            ⬅ Back
          </button>
          <p className="mb-2 text-lg">
            Selected Model:{" "}
            <span className="font-bold text-yellow-400">
              {selectedType === "phase_map" ? "Phase Map" : "KAM"}
            </span>
          </p>
          <input
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            className="mb-4"
          />
          {preview && (
            <img
              src={preview}
              alt="Preview"
              className="w-64 h-64 object-contain mb-4 border-2 border-gray-300 rounded-lg"
            />
          )}
          <button
            onClick={handleSubmit}
            disabled={loading || !image}
            className="px-6 py-2 bg-yellow-500 text-white rounded-lg disabled:bg-gray-400"
          >
            {loading ? "Predicting..." : "Upload & Predict"}
          </button>
          {prediction && (
            <p className="mt-4 text-lg font-semibold">
              Predicted Elongation: {prediction}%
            </p>
          )}
        </div>
      )}
    </div>
  );
}