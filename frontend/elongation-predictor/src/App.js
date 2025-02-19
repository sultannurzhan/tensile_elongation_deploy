import { useState } from "react";
import './App.css';
import axios from "axios";

export default function ElongationPredictor() {
  const [percentage, setPercentage] = useState("");
  const [confirmedPercentage, setConfirmedPercentage] = useState(null); 
  const [selectedType, setSelectedType] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleTypeSelection = (type) => {
    setSelectedType(type);
    setImageUrl(null);
    setError("");
  };

  const handlePercentageChange = (e) => {
    const value = e.target.value;
    setPercentage(value);

    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
      setError("Please enter a valid number");
    } else if (numValue < 5) {
      setError("Enter minimum 5%");
    } else if (numValue > 60) {
      setError("Enter maximum 60%");
    } else {
      setError("");
    }
  };

  const handleGenerateImage = async () => {
    if (!percentage || !selectedType || error) return;
    setLoading(true);
    setImageUrl(null);

    try {
      const response = await axios.post(
        "https://tensileelongationdeploy-production.up.railway.app/generate_image", 
        { percentage: parseFloat(percentage), type: selectedType },
        { headers: { "Content-Type": "application/json" }, responseType: "blob" }
      );

      const imageUrl = URL.createObjectURL(response.data);
      setImageUrl(imageUrl);
      setConfirmedPercentage(percentage); 
    } catch (error) {
      console.error("Error generating image", error);
    }

    setLoading(false);
};

  return (
    <div className="min-h-screen bg-darkPurple text-white flex flex-col items-center justify-center p-6">
      <h1 className="text-2xl font-bold mb-6">Tensile Elongation Predictor</h1>

      <div className="flex gap-6 mb-4">
        <button
          className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
          onClick={() => handleTypeSelection("kam")}
        >
          Generate KAM Image
        </button>
        <button
          className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
          onClick={() => handleTypeSelection("phase_map")}
        >
          Generate Phase Map
        </button>
      </div>

      {selectedType && (
        <div className="flex flex-col items-center">
          <div className="relative mb-4">
            <input
              type="text"
              inputMode="decimal"
              placeholder="Enter elongation percentage"
              value={percentage}
              onChange={handlePercentageChange}
              className="p-2 pr-8 border border-gray-300 rounded-lg text-black w-32 no-arrows"
              min="5"
              max="60"
            />
            <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-600">%</span>
          </div>

          {error && <p className="text-red-400 mb-2">{error}</p>}

          <button
            onClick={handleGenerateImage}
            disabled={loading || !percentage || error}
            className="px-6 py-2 bg-yellow-500 text-white rounded-lg disabled:bg-gray-400"
          >
            {loading ? "Generating..." : "Generate Image"}
          </button>
        </div>
      )}

      {imageUrl && (
        <div className="mt-6 flex flex-col items-center">
          <h2 className="text-lg font-semibold mb-2">
            Generated Image: ({confirmedPercentage}%)
          </h2>
          <img 
            src={imageUrl} 
            alt={`Generated Elongation ${confirmedPercentage}%`} 
            className="w-64 h-64 object-contain border-2 border-gray-300 rounded-lg mb-4" 
          />
          <a
            href={imageUrl}
            download={`elongation_${confirmedPercentage}.png`}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
          >
            Download Image
          </a>
        </div>
      )}
    </div>
  );
}