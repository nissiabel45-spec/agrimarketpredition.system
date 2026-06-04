/**
 * AgriMarket Recommendation Widget
 * Phase 4: Unit Tests
 * Author: AJEICHEK ABEL NISSI (CT23A010)
 *
 * Tests the widget's pure JS functions without a real browser.
 * Uses Jest + jsdom (standard Node test environment).
 *
 * Run:
 *   npm install
 *   npm test
 */

"use strict";

/* -----------------------------------------------------------------------
 * Inline the pure utility functions we want to test
 * (extracted from agri-widget.js to keep tests independent of DOM)
 * -------------------------------------------------------------------- */

/** Parse cookie string */
function getCookie(cookieStr, name) {
  var m = cookieStr.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return m ? m.pop() : null;
}

/** Build recommendations API URL */
function buildApiUrl(base, sessionId, viewedIds, topK) {
  var params = new URLSearchParams({ session_id: sessionId, top_k: topK });
  if (viewedIds.length > 0) params.set("viewed", viewedIds.join(","));
  return base + "/api/v1/recommendations?" + params.toString();
}

/** Clamp score to display percentage */
function scoreToPercent(score) {
  return Math.round(Math.min(Math.max(score * 100, 5), 99));
}

/** Category → emoji mapping */
var CATEGORY_EMOJI = {
  fruitsetlegumes: "🥬", agroalimentaire: "🫙",
  tubercules: "🌾", traitement: "🌿", plantations: "🌴",
  sylviculture: "🪵", elevage1: "🦐"
};
function getEmoji(category) {
  return CATEGORY_EMOJI[category] || "🌱";
}

/** Extract product ID from Agromarket URL */
function extractProductId(url) {
  var m = url.match(/\/en\/[^/]+\/[^/]+-(\d+)\.html/);
  return m ? m[1] : null;
}

/** Debounce */
function debounce(fn, delay) {
  var timer;
  return function () {
    var args = arguments;
    clearTimeout(timer);
    timer = setTimeout(function () { fn.apply(null, args); }, delay);
  };
}


/* -----------------------------------------------------------------------
 * Test suites
 * -------------------------------------------------------------------- */

describe("getCookie", () => {
  test("returns value when cookie exists", () => {
    expect(getCookie("foo=bar; baz=qux", "foo")).toBe("bar");
  });

  test("returns value for second cookie", () => {
    expect(getCookie("foo=bar; baz=qux", "baz")).toBe("qux");
  });

  test("returns null when cookie missing", () => {
    expect(getCookie("foo=bar", "missing")).toBeNull();
  });

  test("handles empty cookie string", () => {
    expect(getCookie("", "foo")).toBeNull();
  });

  test("returns session id from real cookie format", () => {
    expect(getCookie("agri_session=s_abc123_1700000000000; other=x", "agri_session"))
      .toBe("s_abc123_1700000000000");
  });
});


describe("buildApiUrl", () => {
  const BASE = "https://rec.example.com";

  test("includes session_id and top_k", () => {
    const url = buildApiUrl(BASE, "sess1", [], 5);
    expect(url).toContain("session_id=sess1");
    expect(url).toContain("top_k=5");
  });

  test("omits viewed param when array empty", () => {
    const url = buildApiUrl(BASE, "sess1", [], 5);
    expect(url).not.toContain("viewed");
  });

  test("includes viewed when products provided", () => {
    const url = buildApiUrl(BASE, "sess1", ["2022", "2026"], 5);
    expect(url).toContain("viewed=2022%2C2026");
  });

  test("uses correct base URL prefix", () => {
    const url = buildApiUrl(BASE, "s", [], 3);
    expect(url.startsWith(BASE + "/api/v1/recommendations")).toBe(true);
  });
});


describe("scoreToPercent", () => {
  test("converts score 1.0 to max 99", () => {
    expect(scoreToPercent(1.0)).toBe(99);
  });

  test("converts score 0.0 to min 5", () => {
    expect(scoreToPercent(0.0)).toBe(5);
  });

  test("converts score 0.75 to 75", () => {
    expect(scoreToPercent(0.75)).toBe(75);
  });

  test("clamps negative score to 5", () => {
    expect(scoreToPercent(-0.5)).toBe(5);
  });

  test("clamps score above 1 to 99", () => {
    expect(scoreToPercent(2.0)).toBe(99);
  });

  test("returns integer", () => {
    expect(Number.isInteger(scoreToPercent(0.333))).toBe(true);
  });
});


describe("getEmoji", () => {
  test("returns correct emoji for fruitsetlegumes", () => {
    expect(getEmoji("fruitsetlegumes")).toBe("🥬");
  });

  test("returns correct emoji for agroalimentaire", () => {
    expect(getEmoji("agroalimentaire")).toBe("🫙");
  });

  test("returns default emoji for unknown category", () => {
    expect(getEmoji("unknown_category")).toBe("🌱");
  });

  test("returns default emoji for empty string", () => {
    expect(getEmoji("")).toBe("🌱");
  });
});


describe("extractProductId", () => {
  test("extracts ID from standard Agromarket URL", () => {
    expect(extractProductId(
      "https://www.agromarket.cm/en/fruitsetlegumes/mangues-a-vendre-2022.html"
    )).toBe("2022");
  });

  test("extracts ID from multi-word slug", () => {
    expect(extractProductId(
      "https://www.agromarket.cm/en/agroalimentaire/noix-et-huile-de-coco-a-vendre-2452-2098.html"
    )).toBe("2098");
  });

  test("returns null for homepage URL", () => {
    expect(extractProductId("https://www.agromarket.cm/en/")).toBeNull();
  });

  test("returns null for category page URL", () => {
    expect(extractProductId("https://www.agromarket.cm/en/fruitsetlegumes/")).toBeNull();
  });

  test("returns null for empty string", () => {
    expect(extractProductId("")).toBeNull();
  });
});


describe("debounce", () => {
  jest.useFakeTimers();

  test("delays execution", () => {
    const fn = jest.fn();
    const debounced = debounce(fn, 200);
    debounced();
    expect(fn).not.toHaveBeenCalled();
    jest.advanceTimersByTime(200);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  test("only fires once for rapid calls", () => {
    const fn = jest.fn();
    const debounced = debounce(fn, 200);
    debounced(); debounced(); debounced();
    jest.advanceTimersByTime(300);
    expect(fn).toHaveBeenCalledTimes(1);
  });
});
