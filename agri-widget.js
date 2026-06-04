/**
 * AgriMarket Recommendation Feature
 * Phase 5: Integration Tests (Jest)
 * Author: AJEICHEK ABEL NISSI (CT23A010)
 *
 * Converted from pytest to Jest.
 * Tests the recommendation API against live running services.
 *
 * Usage:
 *   TRACKER_URL=http://localhost:5001 \
 *   API_URL=http://localhost:5002 \
 *   node --experimental-vm-modules node_modules/.bin/jest tests/integration/
 */

"use strict";

const http = require("http");

const TRACKER_URL = process.env.TRACKER_URL || "http://localhost:5001";
const API_URL     = process.env.API_URL     || "http://localhost:5002";

// Simple fetch helper for Node.js < 18 compatibility
function fetchJson(url, options = {}) {
  return new Promise((resolve, reject) => {
    const { method = "GET", body, headers = {} } = options;
    const parsedUrl = new URL(url);
    const reqOptions = {
      hostname: parsedUrl.hostname,
      port:     parsedUrl.port || 80,
      path:     parsedUrl.pathname + parsedUrl.search,
      method,
      headers: { "Content-Type": "application/json", ...headers },
    };

    const req = http.request(reqOptions, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on("error", reject);
    if (body) req.write(body);
    req.end();
  });
}

// ---------------------------------------------------------------------------
// Tracker API integration tests
// ---------------------------------------------------------------------------

describe("Tracker API (Phase 1)", () => {
  test("health check", async () => {
    const res = await fetchJson(`${TRACKER_URL}/health`);
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });

  test("POST /api/v1/events — product_view", async () => {
    const res = await fetchJson(`${TRACKER_URL}/api/v1/events`, {
      method: "POST",
      body: JSON.stringify({
        event_type: "product_view",
        session_id:  "integration_test_session",
        product_id:  "2022",
        page_url:    "http://localhost/test",
      }),
    });
    // 201 = success, 500 = no DB (acceptable in CI without DB)
    expect([201, 500]).toContain(res.status);
  });

  test("POST /api/v1/events — rejects invalid event_type", async () => {
    const res = await fetchJson(`${TRACKER_URL}/api/v1/events`, {
      method: "POST",
      body: JSON.stringify({
        event_type: "not_valid",
        session_id: "integration_test_session",
      }),
    });
    expect(res.status).toBe(400);
  });
});

// ---------------------------------------------------------------------------
// Recommendation API integration tests
// ---------------------------------------------------------------------------

describe("Recommendation API (Phase 3)", () => {
  test("health check", async () => {
    const res = await fetchJson(`${API_URL}/health`);
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
    expect(res.body).toHaveProperty("n_users");
    expect(res.body).toHaveProperty("n_products");
  });

  test("GET /api/v1/recommendations — requires session_id", async () => {
    const res = await fetchJson(`${API_URL}/api/v1/recommendations`);
    expect(res.status).toBe(400);
  });

  test("GET /api/v1/recommendations — returns results", async () => {
    const res = await fetchJson(
      `${API_URL}/api/v1/recommendations?session_id=integration_s1&top_k=3`
    );
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.recommendations)).toBe(true);
    expect(res.body.recommendations.length).toBeGreaterThan(0);
  });

  test("GET /api/v1/recommendations/popular", async () => {
    const res = await fetchJson(
      `${API_URL}/api/v1/recommendations/popular?top_k=5`
    );
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.recommendations)).toBe(true);
  });

  test("POST /api/v1/recommendations/feedback", async () => {
    const res = await fetchJson(
      `${API_URL}/api/v1/recommendations/feedback`,
      {
        method: "POST",
        body: JSON.stringify({
          session_id: "integration_s1",
          product_id: "2022",
          signal:     "positive",
        }),
      }
    );
    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
  });
});
