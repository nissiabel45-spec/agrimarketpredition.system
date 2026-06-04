# Phase 2 — Recommendation Engine
**AgriMarket Recommendation Feature**
Author: AJEICHEK ABEL NISSI | CT23A010

## What this phase builds

A collaborative filtering model that learns from user behaviour to recommend
relevant agricultural products. It uses SVD matrix factorisation — the same
family of techniques used by Netflix and Amazon — adapted for Agromarket's
small catalogue and low-resource deployment environment.

## Files

| File | Purpose |
|---|---|
| `generate_data.py` | Synthetic data generator (500 users × 20 products) |
| `load_real_data.py` | Load real Phase 1 events from MySQL |
| `preprocess.py` | Build user-item matrix, normalise, train/test split |
| `train_model.py` | SVD collaborative filtering + RMSE evaluation |
| `export_tflite.py` | Convert model to TFLite (or numpy fallback) |
| `tests/test_model.py` | 12 unit tests |

## How to run (full pipeline)

```bash
pip install -r requirements.txt

# Step 1: Generate data (use synthetic OR real)
python generate_data.py          # synthetic
# python load_real_data.py       # real Phase 1 events (needs .env)

# Step 2: Preprocess
python preprocess.py

# Step 3: Train
python train_model.py
# Output: models/model.pkl + models/evaluation_report.json

# Step 4: Export to TFLite
pip install tensorflow            # only for export
python export_tflite.py
# Output: models/recommender.tflite  (~50 KB)

# Step 5: Run tests
pytest tests/ -v
```

## How the model works

SVD (Singular Value Decomposition) factorises the user-item matrix:

```
R (500 users × 20 products)
  ↓ decompose
U (500 × 10)  ×  Σ (10 × 10)  ×  Vᵀ (10 × 20)
```

Each row of U is a user's "taste profile" in 10 latent dimensions.
Each column of Vᵀ is a product's "character" in the same space.

To recommend for a user: `scores = U[user] @ (Σ × Vᵀ)` — products
with high scores are likely to interest that user.

## Cold start strategy

New users with no history get recommendations based on whatever products
they have viewed in the current session. `recommend_for_new_user()` projects
those product vectors into the latent space on the fly.

## Expected evaluation metrics (synthetic data)

| Metric | Expected |
|---|---|
| RMSE | < 0.25 |
| MAE | < 0.20 |
| Hit rate @ 5 | > 40% |

## Next step → Phase 3

The trained model artifacts from `models/` are consumed by the Phase 3
Flask API. Copy the `models/` folder into `phase3_api/` before running Phase 3.
