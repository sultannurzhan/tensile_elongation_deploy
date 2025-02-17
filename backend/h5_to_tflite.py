import tensorflow as tf
from keras._tf_keras.keras.losses import MeanSquaredError

def convert_to_tflite(h5_model_path, tflite_model_path):
    model = tf.keras.models.load_model(h5_model_path, custom_objects={'mse': MeanSquaredError})

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]

    tflite_model = converter.convert()

    with open(tflite_model_path, "wb") as f:
        f.write(tflite_model)

    print(f"✅ Converted {h5_model_path} to {tflite_model_path}")

convert_to_tflite("models/elongation_model_phase_maps_morphed.h5", "models/elongation_model_phase_maps_morphed.tflite")

convert_to_tflite("models/elongation_model_KAM_morphed.h5", "models/elongation_model_KAM_morphed.tflite")
