# Phase 4 — Frontend Recommendation Widget
**AgriMarket Recommendation Feature**
Author: AJEICHEK ABEL NISSI | CT23A010

## What this phase builds

A self-contained JavaScript widget that injects a personalised product
recommendation carousel directly into the Agromarket homepage — no framework,
no build step, one script tag.

## Files

| File | Purpose |
|---|---|
| `agri-widget.js` | Main widget: fetches API, renders carousel, handles interactions |
| `agri-widget.css` | Scoped styles — all prefixed `.agri-rec__` to avoid conflicts |
| `demo.html` | Local test page with mock API and user-state simulator |
| `tests/widget.test.js` | Jest unit tests for pure JS functions |
| `package.json` | Test runner config |

## Installation on Agromarket

Add **two lines** to the Agromarket site's HTML, just before `</body>`:

```html
<link rel="stylesheet" href="https://your-server.com/static/agri-widget.css" />
<script src="https://your-server.com/static/agri-widget.js"></script>
```

That's it. The widget:
1. Reads the `agri_session` cookie (set by `agri-tracker.js` from Phase 1)
2. Reads the `agri_viewed` sessionStorage key (products viewed this session)
3. Calls `GET /api/v1/recommendations?session_id=...&viewed=...&top_k=5`
4. Renders a responsive product card carousel after `#featured-ads`
5. Handles fallback gracefully — hides itself if the API is down

## Local testing

```bash
# No install needed to view the demo — just open in browser:
open demo.html

# To run the unit tests:
npm install
npm test
```

The `demo.html` page mocks the Phase 3 API so you can test all user states
(new visitor, viewed fruits, viewed oils, known user) without a running server.

## Widget behaviour

### Auto-detection
Shows on homepage (`/en/`) and category pages (`/en/fruitsetlegumes/`).
Hidden on individual product pages (users are already on a product).

### Cold-start fallback chain
1. Has `agri_viewed` products in sessionStorage → projection-based personalisation
2. Has `agri_session` cookie matching a known user → full SVD scoring
3. Neither → popular products (globally highest average scores)

### Failure handling
If the API call fails or returns 0 results, the skeleton loader is removed
silently. The page looks exactly as it did before — no broken UI.

### Feedback signals
- Clicking a product card → sends `"positive"` signal + logs `ad_click` event
- Clicking "Not relevant?" → sends `"negative"` for all shown products + refreshes
- Clicking "Refresh" → re-fetches with same session (cache TTL may apply)

## Responsive behaviour

| Viewport | Grid columns |
|---|---|
| ≥ 600px | auto-fill, min 130px per card (typically 4-5 columns) |
| < 600px | 2 columns |
| < 360px | 1 column |

## Serving the static files

Copy `agri-widget.js` and `agri-widget.css` to the Phase 3 API's static folder:

```bash
cp agri-widget.js   ../phase3_api/static/
cp agri-widget.css  ../phase3_api/static/
```

Flask serves them automatically from `/static/`.

## Next step → Phase 5

Phase 5 wires everything together: Pytest + Jest in a GitHub Actions CI pipeline,
Jenkins deployment to a VPS, and a Docker Compose file to run all services.
