"""
AgriMarket Recommendation Feature
Phase 2: Collaborative Filtering Model (SVD)
Author: AJEICHEK ABEL NISSI (CT23A010)

Trains a matrix factorisation model using TruncatedSVD from Scikit-learn.
SVD decomposes the user-item matrix into latent factors that capture
hidden patterns like "users who buy mangoes also buy avocados".

Run:
    python train_model.py
    # Creates: models/model.pkl, models/evaluation_report.json
"""

import json
import os
import pickle
import time

import numpy as np
from scipy.sparse import load_npz
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import root_mean_squared_error


class AgriRecommender:
    """
    SVD-based collaborative filtering recommender.

    How it works:
      The user-item matrix R (users × products) is decomposed into:
          R ≈ U × Σ × Vᵀ
      U  = user latent factors  (what each user "likes")
      Σ  = singular values      (importance of each factor)
      Vᵀ = product latent factors (what each product "is")

      To recommend for user i:
          scores = U[i] @ (Σ · Vᵀ)
      Top-k products by score are the recommendations.
    """

    def __init__(self, n_factors: int = 10, random_state: int = 42):
        self.n_factors    = n_factors
        self.random_state = random_state
        self.svd          = TruncatedSVD(n_components=n_factors, random_state=random_state)
        self.user_factors  = None   # shape: (n_users, n_factors)
        self.item_factors  = None   # shape: (n_factors, n_products)
        self.is_trained   = False

    def fit(self, train_matrix):
        """Train on a scipy sparse CSR matrix (users × products)."""
        print(f"Training SVD with {self.n_factors} latent factors...")
        t0 = time.time()

        # U × Σ  (user latent matrix)
        self.user_factors = self.svd.fit_transform(train_matrix)

        # Σ · Vᵀ  (scaled item matrix — efficient for scoring)
        singular_values   = self.svd.singular_values_
        self.item_factors = np.diag(singular_values) @ self.svd.components_

        self.is_trained = True
        elapsed = time.time() - t0
        print(f"  Trained in {elapsed:.2f}s")
        print(f"  Explained variance: {self.svd.explained_variance_ratio_.sum():.1%}")
        return self

    def predict_scores(self, user_idx: int) -> np.ndarray:
        """Return predicted affinity scores for ALL products for one user."""
        if not self.is_trained:
            raise RuntimeError("Call fit() first")
        return self.user_factors[user_idx] @ self.item_factors

    def recommend(self, user_idx: int, top_k: int = 5,
                  already_seen: list = None) -> list:
        """
        Return top-k product indices (not IDs) for a user.

        Args:
            user_idx:     integer row index in the user matrix
            top_k:        number of recommendations to return
            already_seen: product indices to exclude (already purchased/viewed)
        """
        scores = self.predict_scores(user_idx)

        if already_seen:
            scores[already_seen] = -np.inf  # mask seen products

        top_indices = np.argsort(scores)[::-1][:top_k]
        return top_indices.tolist()

    def recommend_for_new_user(self, viewed_product_indices: list,
                               top_k: int = 5) -> list:
        """
        Cold-start: recommend for a user with no history yet.
        We create a temporary user vector from their viewed products
        and project it into the latent space.

        Args:
            viewed_product_indices: list of product idx the user has seen
            top_k: number of recommendations
        """
        if not self.is_trained:
            raise RuntimeError("Call fit() first")

        n_products = self.item_factors.shape[1]
        temp_row   = np.zeros(n_products)
        for idx in viewed_product_indices:
            temp_row[idx] = 1.0

        # Project into latent space: u_temp = temp_row @ Vᵀ.T × (1/Σ)
        # Simplified: use pseudo-inverse of item_factors
        u_temp = temp_row @ self.item_factors.T
        scores = u_temp @ self.item_factors

        # Exclude already-seen products
        scores[viewed_product_indices] = -np.inf

        return np.argsort(scores)[::-1][:top_k].tolist()


def evaluate(model, test_matrix) -> dict:
    """
    Compute RMSE on the test set.
    Only evaluates (user, product) pairs that appear in the test set.
    """
    print("Evaluating on test set...")
    test_coo = test_matrix.tocoo()

    y_true, y_pred = [], []
    for u_idx, p_idx, true_score in zip(test_coo.row, test_coo.col, test_coo.data):
        pred_scores = model.predict_scores(int(u_idx))
        y_true.append(true_score)
        y_pred.append(float(pred_scores[p_idx]))

    rmse = root_mean_squared_error(y_true, y_pred)
    mae  = float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))

    # Hit rate @ 5: what fraction of test products appear in top-5 recommendations?
    hits = 0
    users_tested = set(test_coo.row)
    for u_idx in list(users_tested)[:200]:   # sample 200 users for speed
        true_products = set(test_coo.col[test_coo.row == u_idx])
        recs = model.recommend(int(u_idx), top_k=5)
        if true_products & set(recs):
            hits += 1
    hit_rate = hits / min(200, len(users_tested))

    report = {
        "rmse":         round(rmse, 4),
        "mae":          round(mae, 4),
        "hit_rate_at_5": round(hit_rate, 4),
        "test_pairs":   len(y_true),
    }
    print(f"  RMSE:        {report['rmse']}")
    print(f"  MAE:         {report['mae']}")
    print(f"  Hit@5:       {report['hit_rate_at_5']:.1%}")
    return report


def train_and_save():
    # Load preprocessed matrices
    print("Loading data...")
    train_matrix = load_npz("data/train.npz")
    test_matrix  = load_npz("data/test.npz")

    # Train
    model = AgriRecommender(n_factors=10)
    model.fit(train_matrix)

    # Evaluate
    report = evaluate(model, test_matrix)

    # Save model
    os.makedirs("models", exist_ok=True)
    with open("models/model.pkl", "wb") as f:
        pickle.dump(model, f)
    print("\nSaved models/model.pkl")

    # Save evaluation report
    with open("models/evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("Saved models/evaluation_report.json")

    return model, report


if __name__ == "__main__":
    train_and_save()
