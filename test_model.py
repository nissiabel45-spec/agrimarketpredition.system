"""
AgriMarket Recommendation Feature
Phase 2 → Phase 3: Export model to JSON for Node.js/Vercel deployment
Author: AJEICHEK ABEL NISSI (CT23A010)

Run this once after Phase 2 training to produce JSON files that
the Node.js recommender_service.js can load without numpy/TFLite.

Usage:
    python export_model_json.py \
        --models-dir ../phase3_api/models \
        --output-dir ../phase3_api/models

The ML model (matrix factorisation) is UNCHANGED — this script only
converts the storage format from .npy to .json so JavaScript can read it.
"""

import argparse
import json
import os
import numpy as np


def export(models_dir: str, output_dir: str):
    uf_path = os.path.join(models_dir, "user_factors.npy")
    if_path = os.path.join(models_dir, "item_factors.npy")

    if not os.path.exists(uf_path) or not os.path.exists(if_path):
        raise FileNotFoundError(
            f"user_factors.npy or item_factors.npy not found in {models_dir}. "
            "Run Phase 2 training first."
        )

    user_factors = np.load(uf_path)
    item_factors = np.load(if_path)

    os.makedirs(output_dir, exist_ok=True)

    out_uf = os.path.join(output_dir, "user_factors.json")
    out_if = os.path.join(output_dir, "item_factors.json")

    with open(out_uf, "w") as f:
        json.dump(user_factors.tolist(), f)
    with open(out_if, "w") as f:
        json.dump(item_factors.tolist(), f)

    print(f"Exported user_factors  {user_factors.shape} → {out_uf}")
    print(f"Exported item_factors  {item_factors.shape} → {out_if}")
    print("Done. These JSON files are loaded by recommender_service.js.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export numpy model to JSON for Node.js")
    parser.add_argument("--models-dir", default="models", help="Directory containing .npy files")
    parser.add_argument("--output-dir", default="models", help="Where to write .json files")
    args = parser.parse_args()
    export(args.models_dir, args.output_dir)
