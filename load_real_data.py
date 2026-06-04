# AgriMarket Recommendation Feature — JavaScript Edition
**Author: AJEICHEK ABEL NISSI (CT23A010)**

This is the full conversion of the AgriMarket recommendation system from Python/Flask to **Node.js/Express**, with Vercel deployment support.

---

## What changed vs. what stayed the same

| Component | Original | Converted |
|---|---|---|
| Phase 1 tracking API | Python/Flask `app.py` | **Node.js/Express `app.js`** |
| Phase 3 recommendation API | Python/Flask `app.py` | **Node.js/Express `app.js`** |
| Phase 3 recommender service | Python `recommender_service.py` | **JavaScript `recommender_service.js`** |
| Phase 1 & 3 Dockerfiles | `python:3.11-slim` base | **`node:20-alpine` base** |
| Phase 1 & 3 Tests | pytest | **Jest + Supertest** |
| CI/CD workflow | Python test steps | **Node.js test steps** |
| **ML model** (matrix factorisation) | `.npy` numpy arrays | **UNCHANGED** — exported to `.json` for JS |
| Phase 2 (training) | Python | **UNCHANGED** |
| Phase 4 widget | JavaScript | **UNCHANGED** |
| Phase 5 Docker Compose | Python healthchecks | Updated healthchecks (wget) |
| Nginx config | — | **UNCHANGED** |

---

## Project structure

```
AgriMarket_JS/
├── phase1_tracking/
│   ├── api/
│   │   ├── app.js               ← Node.js tracking API (converted)
│   │   ├── package.json
│   │   ├── Dockerfile           ← node:20-alpine (converted)
│   │   └── static/
│   │       └── agri-tracker.js  ← unchanged
│   ├── db/
│   │   └── schema.sql           ← unchanged
│   └── tests/
│       └── test_tracking_api.test.js ← Jest tests (converted)
│
├── phase2_model/                ← UNCHANGED (Python ML training)
│   ├── train_model.py
│   ├── preprocess.py
│   ├── generate_data.py
│   ├── export_tflite.py
│   └── export_model_json.py     ← NEW: export .npy → .json for JS
│
├── phase3_api/
│   ├── app.js                   ← Node.js recommendation API (converted)
│   ├── recommender_service.js   ← JS port of recommender_service.py
│   ├── package.json
│   ├── Dockerfile               ← node:20-alpine (converted)
│   ├── vercel.json              ← NEW: Vercel deployment config
│   ├── models/
│   │   ├── user_factors.npy     ← original (kept for reference)
│   │   ├── item_factors.npy     ← original (kept for reference)
│   │   ├── user_factors.json    ← NEW: JS-readable model
│   │   └── item_factors.json    ← NEW: JS-readable model
│   ├── data/
│   │   ├── products.json        ← unchanged
│   │   └── idx_to_product.json  ← unchanged
│   └── tests/
│       └── test_api.test.js     ← Jest tests (converted)
│
├── phase4_widget/               ← UNCHANGED
│
└── phase5_cicd/
    ├── docker-compose.yml       ← updated for Node.js healthchecks
    ├── .github/workflows/
    │   └── ci-cd.yml            ← Node.js + Vercel deploy steps
    ├── nginx.conf               ← UNCHANGED
    └── .env.example             ← UNCHANGED
```

---

## Quick start

### 1 — Prepare model files (one-time after Phase 2 training)

```bash
cd phase2_model
pip install numpy
python export_model_json.py \
    --models-dir ../phase3_api/models \
    --output-dir ../phase3_api/models
```

> **Already done** — `user_factors.json` and `item_factors.json` are included.

### 2 — Run locally (recommendation API)

```bash
cd phase3_api
npm install
node app.js
# → http://localhost:5002/health
```

### 3 — Run locally (tracking API)

```bash
cd phase1_tracking/api
npm install
# Set DB credentials in .env
node app.js
# → http://localhost:5001/health
```

### 4 — Run all services with Docker Compose

```bash
cd phase5_cicd
cp .env.example .env   # fill in DB credentials
docker compose up -d
```

Services:
- `http://localhost:5001` — Tracking API
- `http://localhost:5002` — Recommendation API
- `http://localhost:80`   — Nginx (widget static files)

---

## Deploy to Vercel

The Phase 3 recommendation API deploys to Vercel as a serverless Node.js function.

```bash
cd phase3_api
npm install -g vercel
vercel --prod
```

The `vercel.json` routes all requests through `app.js`. The model files
(`models/`, `data/`) are included in the deployment bundle.

### Required Vercel environment variables (set in Vercel dashboard)

| Variable | Value |
|---|---|
| `MODELS_DIR` | `models` |
| `DATA_DIR` | `data` |

### GitHub Actions auto-deploy

Add these secrets to your GitHub repository:

| Secret | Where to get it |
|---|---|
| `VERCEL_TOKEN` | Vercel dashboard → Settings → Tokens |
| `VERCEL_ORG_ID` | `.vercel/project.json` after first `vercel` run |
| `VERCEL_PROJECT_ID` | `.vercel/project.json` after first `vercel` run |

---

## Run tests

```bash
# Phase 3 API tests
cd phase3_api && npm test

# Phase 1 tracking API tests
cd phase1_tracking/api && npm test

# Phase 4 widget tests (unchanged)
cd phase4_widget && npm test
```

---

## About the ML model

The recommendation engine uses **matrix factorisation** (collaborative filtering).
The model was trained in Phase 2 (Python/NumPy) and produces two factor matrices:

- `user_factors.json` — shape `(500, 10)`: 500 users × 10 latent factors
- `item_factors.json` — shape `(10, 20)`: 10 latent factors × 20 products

The JavaScript `recommender_service.js` implements the same scoring math:
- **Known user**: `scores = userFactors[userIdx] @ itemFactors`
- **Cold start**: project viewed products into latent space, then score
- **No context**: column mean across all user scores (most popular)

No Python, TensorFlow, or NumPy is required at runtime.
