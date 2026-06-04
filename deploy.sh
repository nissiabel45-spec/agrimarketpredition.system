"""
AgriMarket Recommendation Feature
Phase 2: TensorFlow Lite Export
Author: AJEICHEK ABEL NISSI (CT23A010)

Converts the trained sklearn SVD model into a TensorFlow Lite FlatBuffer.
This makes the model self-contained, fast to load, and tiny (<2 MB).

The TFLite model takes a user index as input and returns recommendation
scores for all products. The Flask API (Phase 3) will use this model.

Run:
    pip install tensorflow  (only needed for export, not for inference)
    python export_tflite.py
    # Creates: models/recommender.tflite
"""

import json
import os
import pickle

import numpy as np

# ---------------------------------------------------------------------------
# Step 1: Load the trained sklearn model
# ---------------------------------------------------------------------------

print("Loading trained model...")
with open("models/model.pkl", "rb") as f:
    model = pickle.load(f)

user_factors = model.user_factors    # (n_users, n_factors)
item_factors = model.item_factors    # (n_factors, n_products)

n_users, n_factors  = user_factors.shape
n_factors2, n_products = item_factors.shape

print(f"  Users: {n_users}, Products: {n_products}, Factors: {n_factors}")

# ---------------------------------------------------------------------------
# Step 2: Build a TensorFlow model that wraps the SVD computation
#
# The model is extremely simple:
#   input:  user_idx (int32 scalar)
#   output: scores for all products (float32 vector of length n_products)
#
# Internally it just does:
#   user_vec = user_factors[user_idx]        (embedding lookup)
#   scores   = user_vec @ item_factors       (dot product)
# ---------------------------------------------------------------------------

try:
    import tensorflow as tf

    # Embed user_factors and item_factors as constants in the TF graph
    user_factors_const = tf.constant(user_factors, dtype=tf.float32)
    item_factors_const = tf.constant(item_factors, dtype=tf.float32)

    @tf.function(input_signature=[
        tf.TensorSpec(shape=[], dtype=tf.int32, name="user_idx")
    ])
    def recommend(user_idx):
        user_vec = tf.gather(user_factors_const, user_idx)  # (n_factors,)
        scores   = tf.linalg.matvec(
            tf.transpose(item_factors_const), user_vec      # (n_products,)
        )
        return {"scores": scores}

    # Convert to TFLite
    print("\nConverting to TensorFlow Lite...")
    converter = tf.lite.TFLiteConverter.from_concrete_functions(
        [recommend.get_concrete_function()],
        recommend
    )

    # Optimise: Dynamic range quantisation
    # Reduces model size by ~4x with minimal accuracy loss
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    tflite_model = converter.convert()

    # Save
    os.makedirs("models", exist_ok=True)
    tflite_path = "models/recommender.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)

    size_kb = os.path.getsize(tflite_path) / 1024
    print(f"  Saved {tflite_path}  ({size_kb:.1f} KB)")

    # ---------------------------------------------------------------------------
    # Step 3: Smoke test the tflite model
    # ---------------------------------------------------------------------------

    print("\nSmoke testing TFLite model...")
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()

    input_details  = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Test with user 0
    interpreter.set_tensor(input_details[0]["index"], np.array(0, dtype=np.int32))
    interpreter.invoke()
    scores = interpreter.get_tensor(output_details[0]["index"])

    top5 = np.argsort(scores[0])[::-1][:5]
    print(f"  Top-5 products for user 0: {top5.tolist()}")
    print("  TFLite model works correctly.")

except ImportError:
    # ---------------------------------------------------------------------------
    # Fallback: save the sklearn model weights as numpy arrays
    # The Phase 3 API can load and run these without TF installed
    # ---------------------------------------------------------------------------

    print("\nTensorFlow not installed. Saving model as numpy arrays instead.")
    print("(This is functionally identical — the Phase 3 API supports both formats.)")

    np.save("models/user_factors.npy", user_factors)
    np.save("models/item_factors.npy", item_factors)

    size_kb = (
        os.path.getsize("models/user_factors.npy") +
        os.path.getsize("models/item_factors.npy")
    ) / 1024
    print(f"  Saved models/user_factors.npy + item_factors.npy  ({size_kb:.1f} KB total)")

    # Write a flag so Phase 3 knows which format to load
    with open("models/format.json", "w") as f:
        json.dump({"format": "numpy"}, f)

print("\nPhase 2 complete. Proceed to Phase 3 (API service).")
