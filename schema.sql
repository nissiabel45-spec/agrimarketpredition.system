/**
 * AgriMarket Recommendation Feature
 * Phase 3: Recommendation API (Node.js/Express)
 * Author: AJEICHEK ABEL NISSI (CT23A010)
 *
 * Converted from Python/Flask to Node.js/Express.
 * The underlying ML model (matrix factorisation) is UNCHANGED.
 *
 * Endpoints:
 *   GET  /health                           Health check
 *   GET  /api/v1/recommendations           Get personalised suggestions
 *   POST /api/v1/recommendations/feedback  Record a thumbs-up/down signal
 *   GET  /api/v1/recommendations/popular   Fallback: most popular products
 *
 * Run locally:
 *   npm install
 *   node app.js
 *
 * Deploy to Vercel:
 *   vercel --prod
 */

"use strict";

const express = require("express");
const cors = require("cors");
require("dotenv").config();

const { RecommenderService } = require("./recommender_service");

// ---------------------------------------------------------------------------
// App setup
// ---------------------------------------------------------------------------

const app = express();
app.use(express.json());

// CORS_ORIGINS env var lets the Vercel deployment URL be injected at runtime
// without code changes:  CORS_ORIGINS=https://agri-api.vercel.app,https://www.agromarket.cm
const ALLOWED_ORIGINS = process.env.CORS_ORIGINS
  ? process.env.CORS_ORIGINS.split(",").map((o) => o.trim())
  : [
      "https://www.agromarket.cm",
      "http://localhost:3000",
      "http://127.0.0.1:5500", // live-server for local widget testing
    ];

app.use(
  cors({
    origin: (origin, callback) => {
      // Allow requests with no origin (curl, server-to-server, Vercel health probes)
      if (!origin) return callback(null, true);
      // Allow any *.vercel.app preview URL for this project
      if (origin.endsWith(".vercel.app")) return callback(null, true);
      if (ALLOWED_ORIGINS.includes(origin)) return callback(null, true);
      callback(new Error(`CORS: origin ${origin} not allowed`));
    },
    methods: ["GET", "POST", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
    credentials: false,
  })
);

// Load model once at startup — not on every request
const MODELS_DIR = process.env.MODELS_DIR || "models";
const DATA_DIR = process.env.DATA_DIR || "data";

console.log("[AgriAPI] Loading recommendation model...");
const svc = new RecommenderService(MODELS_DIR, DATA_DIR);
console.log(
  `[AgriAPI] Model ready — ${svc.model.mode} backend, ` +
    `${svc.model.nUsers} users × ${svc.model.nProducts} products`
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Parse comma-separated query param → array of strings.
 * @param {string} value
 * @returns {string[]}
 */
function parseListParam(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean);
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

/**
 * GET /health
 * Health check used by Docker, Jenkins, and load balancers.
 */
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    model: svc.model.mode,
    n_users: svc.model.nUsers,
    n_products: svc.model.nProducts,
    timestamp: new Date().toISOString(),
  });
});

/**
 * GET /api/v1/recommendations
 * Return personalised product recommendations.
 *
 * Query parameters:
 *   session_id   (required) — browser session cookie value
 *   user_idx     (optional) — integer row index for known users
 *   viewed       (optional) — comma-separated Agromarket product IDs seen this session
 *   exclude      (optional) — comma-separated product IDs to suppress
 *   top_k        (optional) — number of results (default 5, max 10)
 */
app.get("/api/v1/recommendations", (req, res) => {
  const sessionId = (req.query.session_id || "").trim();
  if (!sessionId) {
    return res.status(400).json({ error: "session_id is required" });
  }

  // user_idx: integer if provided, else null (cold start)
  let userIdx = null;
  const rawUserIdx = (req.query.user_idx || "").trim();
  if (/^\d+$/.test(rawUserIdx)) userIdx = parseInt(rawUserIdx, 10);

  const viewed = parseListParam(req.query.viewed || "");
  const exclude = parseListParam(req.query.exclude || "");
  const topKRaw = req.query.top_k || "5";
  const topK = Math.min(/^\d+$/.test(topKRaw) ? parseInt(topKRaw, 10) : 5, 10);

  try {
    const recs = svc.recommend({
      sessionId,
      userIdx,
      viewedProductIds: viewed,
      topK,
      excludeProductIds: exclude,
    });

    console.log(
      `[AgriAPI] recommendations session=${sessionId} user_idx=${userIdx} ` +
        `viewed=${viewed} returned=${recs.length}`
    );

    return res.json({
      session_id: sessionId,
      count: recs.length,
      recommendations: recs,
    });
  } catch (err) {
    console.error("[AgriAPI] Error generating recommendations:", err);
    return res
      .status(500)
      .json({ error: "Internal server error", detail: err.message });
  }
});

/**
 * POST /api/v1/recommendations/feedback
 * Record explicit user feedback on a recommendation (thumbs up/down).
 *
 * Body:
 * {
 *   "session_id": "s_abc123",
 *   "product_id": "2022",
 *   "signal":     "positive" | "negative"
 * }
 */
app.post("/api/v1/recommendations/feedback", (req, res) => {
  const data = req.body || {};
  const sessionId = (data.session_id || "").trim();
  const productId = (data.product_id || "").trim();
  const signal = (data.signal || "").trim();

  if (!sessionId || !productId) {
    return res
      .status(400)
      .json({ error: "session_id and product_id are required" });
  }
  if (!["positive", "negative"].includes(signal)) {
    return res
      .status(400)
      .json({ error: "signal must be 'positive' or 'negative'" });
  }

  // Invalidate cache so next request re-scores with updated context
  if (signal === "negative") {
    svc.invalidateCache(sessionId);
  }

  // In production: persist to DB via Phase 1 event API
  // For now: log for offline analysis
  console.log(
    `[AgriAPI] feedback session=${sessionId} product=${productId} signal=${signal}`
  );

  return res.status(201).json({
    success: true,
    session_id: sessionId,
    product_id: productId,
    signal,
  });
});

/**
 * GET /api/v1/recommendations/popular
 * Fallback endpoint: returns globally popular products.
 */
app.get("/api/v1/recommendations/popular", (req, res) => {
  const topKRaw = req.query.top_k || "5";
  const topK = Math.min(
    /^\d+$/.test(topKRaw) ? parseInt(topKRaw, 10) : 5,
    10
  );

  const recs = svc.recommend({
    sessionId: "__popular__",
    userIdx: null,
    viewedProductIds: [],
    topK,
  });

  return res.json({ count: recs.length, recommendations: recs });
});

// ---------------------------------------------------------------------------
// Error handlers
// ---------------------------------------------------------------------------

app.use((req, res) => {
  res.status(404).json({ error: "Not found" });
});

// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: "Internal server error" });
});

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

// For Vercel: export the express app as the default export
// For Docker/local: also start the HTTP server
if (require.main === module) {
  const PORT = parseInt(process.env.PORT || "5002", 10);
  app.listen(PORT, "0.0.0.0", () => {
    console.log(`[AgriAPI] Recommendation API running on port ${PORT}`);
  });
}

module.exports = app; // Vercel serverless entry point
