"""
AgriMarket Recommendation Feature
Phase 2: Preprocessing Pipeline
Author: AJEICHEK ABEL NISSI (CT23A010)

Converts interaction_matrix.csv -> sparse user-item matrix
ready for collaborative filtering training.

Run:
    python preprocess.py
    # Creates: data/train.npz, data/test.npz, data/idx_to_product.json
"""

import json
import os

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, save_npz


def build_matrices(interactions_path: str = "data/interaction_matrix.csv"):
    print("Loading interactions...")
    df = pd.read_csv(interactions_path)

    # Use integer user_id and product_idx already in the CSV
    df["u_idx"] = df["user_id"].astype(int)
    df["p_idx"] = df["product_idx"].astype(int)

    n_users    = df["u_idx"].max() + 1
    n_products = df["p_idx"].max() + 1

    print(f"  Users:    {n_users}")
    print(f"  Products: {n_products}")
    print(f"  Interactions: {len(df):,}")

    # Normalise score per user (0-1 scale)
    mx_scores = df.groupby("u_idx")["score"].transform("max")
    df["score_norm"] = df["score"] / mx_scores

    # 80/20 train-test split per user
    rng = np.random.default_rng(42)
    df["split"] = "train"
    for uid, grp in df.groupby("u_idx"):
        if len(grp) <= 1:
            continue
        n_test   = max(1, int(len(grp) * 0.2))
        test_idx = rng.choice(grp.index, size=n_test, replace=False)
        df.loc[test_idx, "split"] = "test"

    train_df = df[df["split"] == "train"]
    test_df  = df[df["split"] == "test"]

    def to_sparse(frame, rows, cols):
        return csr_matrix(
            (frame["score_norm"].values,
             (frame["u_idx"].values, frame["p_idx"].values)),
            shape=(rows, cols)
        )

    train_matrix = to_sparse(train_df, n_users, n_products)
    test_matrix  = to_sparse(test_df,  n_users, n_products)

    os.makedirs("data", exist_ok=True)
    save_npz("data/train.npz", train_matrix)
    save_npz("data/test.npz",  test_matrix)

    # Save idx -> product_id mapping for the API
    products_df = pd.read_csv("data/products.csv")
    idx_to_product = {str(i): str(row["id"]) for i, row in products_df.iterrows()}
    with open("data/idx_to_product.json", "w") as f:
        json.dump(idx_to_product, f)

    print(f"\nTrain interactions: {len(train_df):,}")
    print(f"Test  interactions: {len(test_df):,}")
    print(f"\nSaved: data/train.npz, data/test.npz, data/idx_to_product.json")

    return train_matrix, test_matrix, idx_to_product


if __name__ == "__main__":
    build_matrices()
