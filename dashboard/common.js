// Shared by the detailed and the executive view, so both use exactly the same data, calculations,
// wording and colours. Inlined into each page by dashboard/build.py.
const MW = (function () {
  const D = JSON.parse(document.getElementById("data").textContent);
  const L = D.latest, ALL = D.rows, T = D.thresholds;
  const $ = (id) => document.getElementById(id);
  const cs = getComputedStyle(document.documentElement), v = (n) => cs.getPropertyValue(n).trim();
  const MINUS = "−";
  const fmt = (x, d = 0) => x == null ? "–" : Number(x).toLocaleString("en-AU", { minimumFractionDigits: d, maximumFractionDigits: d }).replace("-", MINUS);
  const sgn = (x, d = 1) => x == null ? "–" : (x > 0 ? "+" : x < 0 ? MINUS : "") + fmt(Math.abs(x), d);
  const day = (iso) => new Date(iso + "T12:00:00").toLocaleDateString("en-AU", { weekday: "short", day: "numeric", month: "short" });
  const dm = (iso) => new Date(iso + "T12:00:00").toLocaleDateString("en-AU", { day: "numeric", month: "short" });

  // Arrow = direction; colour = interpretation. Modes (prompt v4, section 13):
  //   "neutral" no favourable reading · "market" ASX price direction (green up, red down)
  //   "lower-better" monitoring concern (green lower, red higher, with words) · "yield" subtle orange
  const delta = (x, d, unit, mode = "neutral", words = null) => {
    if (x == null) return `<span class="flat">–</span>`;
    const arrow = x > 0 ? "▲" : x < 0 ? "▼" : "■", num = `${arrow} ${fmt(Math.abs(x), d)}${unit}`;
    if (x === 0 || mode === "neutral") return `<span class="neutral">${num}</span>`;
    if (mode === "yield") return `<span class="yieldc">${num}</span>`;
    if (mode === "market") return `<span class="${x > 0 ? "up" : "down"}">${num}</span>`;
    const fav = mode === "lower-better" ? x < 0 : x > 0;
    return `<span class="${fav ? "concern-low" : "concern-high"}">${num}${words ? " · " + words[fav ? 0 : 1] : ""}</span>`;
  };
  const chip = (s) => `<span class="chip" data-s="${s}">${s}</span>`;
  const CHANGE = { 7: "1-week change", 30: "1-month change", 90: "90-day change", 365: "1-year change" };
  const RANGES = { 7: "week", 30: "month", 90: "90 days", 365: "year" };
  const MEANS = { Green: "Normal activity", Amber: "Heavy activity", Red: "Very heavy activity", Pending: "Volume not final yet", Excluded: "Invalid volume, excluded" };
  const provisional = L.end !== L.rag_date;
  const prev = ALL.filter((r) => r.trade_date_syd < L.end && r.close_pts != null).slice(-1)[0];
  const dayChg = prev ? (L.close / prev.close_pts - 1) * 100 : null;

  function slice(days) {
    const end = new Date(L.end + "T12:00:00"); const s = new Date(end); s.setDate(s.getDate() - (days - 1));
    return ALL.filter((r) => r.trade_date_syd >= s.toISOString().slice(0, 10));
  }
  function pearson(xs, ys) {
    const n = xs.length; if (n < 3) return null;
    const mx = xs.reduce((a, b) => a + b, 0) / n, my = ys.reduce((a, b) => a + b, 0) / n;
    let sxy = 0, sxx = 0, syy = 0; for (let i = 0; i < n; i++) { sxy += (xs[i] - mx) * (ys[i] - my); sxx += (xs[i] - mx) ** 2; syy += (ys[i] - my) ** 2; }
    return sxx && syy ? { r: sxy / Math.sqrt(sxx * syy), b: sxy / sxx, a: my - (sxy / sxx) * mx } : null;
  }
  function stats(R) {
    const closes = R.filter((r) => r.close_pts != null), first = closes[0], last = closes[closes.length - 1];
    const known = R.filter((r) => r.yield_same_day_pct != null);
    const fired = R.filter((r) => r.rag_status === "Amber" || r.rag_status === "Red");
    const count = (s) => R.filter((r) => r.rag_status === s).length;
    const pairs = R.filter((r) => r.asx_return_pct != null && r.yield_change_1d_bp != null);
    const pick = (arr, key, cmp) => arr.reduce((a, b) => (cmp(b[key], a[key]) ? b : a));
    const corr = R.filter((r) => r.corr20 != null).map((r) => r.corr20);
    return { R, first, last, n: R.length, chg: (last.close_pts / first.close_pts - 1) * 100,
      hi: pick(closes, "close_pts", (a, b) => a > b), lo: pick(closes, "close_pts", (a, b) => a < b),
      above: R.filter((r) => r.close_pts != null && r.ma20_pts != null && r.close_pts > r.ma20_pts).length,
      yFirst: known[0], yLast: known[known.length - 1], yBp: known.length > 1 ? (known[known.length - 1].yield_same_day_pct - known[0].yield_same_day_pct) * 100 : null,
      yHi: known.length ? pick(known, "yield_same_day_pct", (a, b) => a > b) : null,
      fired, amber: count("Amber"), red: count("Red"), green: count("Green"), pending: count("Pending"), excluded: count("Excluded"),
      top: fired.length ? pick(fired, "volume_vs_normal_pct", (a, b) => a > b) : null,
      pairs, fit: pearson(pairs.map((r) => r.yield_change_1d_bp), pairs.map((r) => r.asx_return_pct)),
      corrMin: corr.length ? Math.min(...corr) : null, corrMax: corr.length ? Math.max(...corr) : null, corrLast: corr.length ? corr[corr.length - 1] : null };
  }

  // ------------------------------------------------------------------------- wording
  const text = {
    highlights(S, days) {
      const y = S.yBp == null ? "no new RBA yields were published in this period"
        : `the Australian 10-year yield <b>${S.yBp >= 0 ? "rose" : "fell"} ${fmt(Math.abs(S.yBp), 0)} bp</b> (RBA data to ${dm(S.yLast.trade_date_syd)})`;
      return `Over the last ${RANGES[days]} the ASX 200 <b>${S.chg >= 0 ? "rose" : "fell"} ${fmt(Math.abs(S.chg), 1)}%</b>, while ${y}. ` +
        `<b>${S.amber + S.red}</b> of ${S.n} sessions triggered elevated-volume signals; the latest completed signal is <b>${L.rag_status}</b> (${day(L.rag_date)}).`;
    },
    corr(S) {
      if (S.corrLast == null) return "Too few paired days in this period for a 20-session correlation.";
      return (S.corrMax < 0 ? "Daily ASX returns and yield changes remained negatively correlated, although the strength varied over the period."
        : "Daily ASX returns and yield changes were not consistently negatively correlated over the period.") +
        ` Latest: ${sgn(S.corrLast, 2)}; range: ${sgn(S.corrMin, 2)} to ${sgn(S.corrMax, 2)}.`;
    },
    corrShort(S) {
      return S.corrLast == null ? "Too few paired days for a 20-session correlation"
        : `Rolling 20-session correlation (−1 to +1) · latest ${sgn(S.corrLast, 2)}, range ${sgn(S.corrMin, 2)} to ${sgn(S.corrMax, 2)}`;
    },
    scatterShort(S) {
      const F = S.fit; if (!F) return "Too few sessions with both figures";
      const st = Math.abs(F.r) >= 0.5 ? "Strong" : Math.abs(F.r) >= 0.3 ? "Moderate" : "Weak";
      return `${st} ${F.r < 0 ? "negative" : "positive"} association · +1 bp associated with ≈ ${sgn(F.b, 3)} pp · not causation`;
    },
    scatter(S) {
      const F = S.fit; if (!F) return "Too few sessions with both figures in this period.";
      const st = Math.abs(F.r) >= 0.5 ? "strong" : Math.abs(F.r) >= 0.3 ? "moderate" : "weak";
      return `Across ${S.pairs.length} matched sessions, daily ASX returns and yield changes showed a ${st} ${F.r < 0 ? "negative" : "positive"} association (r = ${sgn(F.r, 2)}). ` +
        `A +1 bp yield change was associated with approximately ${sgn(F.b, 3)} percentage points of ASX return; association, not causation.`;
    },
  };

  // ------------------------------------------------------------------------- charts
  const cfg = { displayModeBar: false, responsive: true };
  const lay = (o = {}, compact = false) => ({ margin: compact ? { l: 46, r: 12, t: 6, b: 24 } : { l: 52, r: 18, t: 10, b: 30 },
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { family: v("--sans"), size: compact ? 11 : 12, color: v("--ink-2") }, showlegend: false,
    hoverlabel: { bgcolor: v("--surface-2"), bordercolor: v("--axis"), font: { color: v("--ink"), family: v("--sans") } }, ...o });
  const yax = (t, o = {}) => ({ title: { text: t, font: { size: 11, color: v("--muted") } }, gridcolor: v("--grid"), zeroline: false, linecolor: v("--axis"), fixedrange: true, ...o });
  const xax = (R) => { const x = R.map((r) => r.trade_date_syd);
    return { type: "date", range: [x[0] + " 00:00", x[x.length - 1] + " 23:59"], rangebreaks: [{ bounds: ["sat", "mon"] }], showgrid: false, linecolor: v("--axis"),
      tickcolor: v("--axis"), ticks: "outside", tickformat: "%-d %b", fixedrange: true, rangeslider: { visible: false } }; };

  const keys = {
    base: `<span><i style="background:var(--asx)"></i>Close</span><span><i style="background:var(--avg)"></i>Teal — 20-session average</span><span><i class="sq" style="background:var(--above-wash)"></i>Above start</span><span><i class="sq" style="background:var(--below-wash)"></i>Below start</span>`,
    candle: `<span><i class="sq" style="background:var(--good)"></i>Green — Up day</span><span><i class="sq" style="background:transparent;border:1.5px solid var(--critical)"></i>Red — Down day</span><span><i style="background:var(--avg)"></i>Teal — 20-session average</span>`,
    vol: `<span><i class="sq" style="background:var(--bar)"></i>Normal day</span><span><i class="sq" style="background:var(--warning)"></i>Amber</span><span><i class="sq" style="background:var(--critical)"></i>Red</span><span><i style="background:var(--avg)"></i>Teal — 20-session normal</span>`,
  };

  const draw = {
    price(id, R, S, style, compact = false) {
      const x = R.map((r) => r.trade_date_syd), base = S.first.close_pts, closes = R.map((r) => r.close_pts), flat = x.map(() => base);
      const avg = { x, y: R.map((r) => r.ma20_pts), mode: "lines", line: { color: v("--avg"), width: 2.5 }, hovertemplate: "average %{y:,.1f}<extra></extra>" };
      let tr;
      if (style === "candle") {
        const C = R.filter((r) => r.open_pts != null);
        tr = [{ type: "candlestick", x: C.map((r) => r.trade_date_syd), open: C.map((r) => r.open_pts), high: C.map((r) => r.high_pts), low: C.map((r) => r.low_pts), close: C.map((r) => r.close_pts),
          increasing: { line: { color: v("--good"), width: 1.5 }, fillcolor: v("--good") }, decreasing: { line: { color: v("--critical"), width: 1.5 }, fillcolor: v("--surface") }, hoverinfo: "x+y" }, avg];
      } else {
        tr = [{ x, y: flat, mode: "lines", line: { width: 0 }, hoverinfo: "skip" },
          { x, y: closes.map((c) => (c == null ? null : Math.max(c, base))), mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: v("--above-wash"), hoverinfo: "skip" },
          { x, y: flat, mode: "lines", line: { width: 1, color: v("--axis") }, hoverinfo: "skip" },
          { x, y: closes.map((c) => (c == null ? null : Math.min(c, base))), mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: v("--below-wash"), hoverinfo: "skip" },
          avg, { x, y: closes, mode: "lines", line: { color: v("--asx"), width: 3.5 }, hovertemplate: "close %{y:,.1f}<extra></extra>" }];
      }
      Plotly.react(id, tr, lay({ hovermode: "x unified", xaxis: xax(R), yaxis: yax(compact ? "" : "Index points", { tickformat: ",.0f" }) }, compact), cfg);
    },
    volume(id, R, compact = false) {
      const x = R.map((r) => r.trade_date_syd);
      const col = R.map((r) => v(r.rag_status === "Red" ? "--critical" : r.rag_status === "Amber" ? "--warning" : r.volume == null ? "--pending" : "--bar"));
      let reds = R.filter((r) => r.rag_status === "Red");
      // compact (executive) view: on long periods label only the four largest Red sessions so labels stay legible
      if (compact && reds.length > 4) reds = reds.slice().sort((a, b) => b.volume_vs_normal_pct - a.volume_vs_normal_pct).slice(0, 4);
      const pend = R.filter((r) => r.volume == null);
      Plotly.react(id, [
        { x, y: R.map((r) => r.volume), type: "bar", marker: { color: col }, customdata: R.map((r) => [r.volume_vs_normal_pct, r.rag_status]),
          hovertemplate: "%{x|%-d %b}: %{y:,.0f} · %{customdata[0]:+.0f}% vs normal · %{customdata[1]}<extra></extra>" },
        { x, y: R.map((r) => r.volume_normal), mode: "lines", line: { color: v("--avg"), width: 3 }, hovertemplate: "normal %{y:,.0f}<extra></extra>" },
      ], lay({ bargap: 0.25, xaxis: xax(R), yaxis: yax(compact ? "" : "Volume", { tickformat: "~s" }),
        annotations: pend.map((r) => ({ x: r.trade_date_syd, y: 0, yanchor: "bottom", text: "pending", textangle: -90, showarrow: false, font: { size: 10, color: v("--muted") } }))
          .concat(reds.map((r) => ({ x: r.trade_date_syd, y: r.volume, yanchor: "bottom", text: `Red ${sgn(r.volume_vs_normal_pct, 0)}%`, showarrow: false, font: { size: 11, color: v("--ink") } }))) }, compact), cfg);
    },
    yield(id, R, S, compact = false) {
      const x = R.map((r) => r.trade_date_syd), lastRba = S.yLast ? S.yLast.trade_date_syd : null, endD = x[x.length - 1];
      const shapes = lastRba && lastRba < endD ? [{ type: "rect", xref: "x", yref: "paper", x0: lastRba + " 12:00", x1: endD + " 23:59", y0: 0, y1: 1, fillcolor: v("--band"), line: { width: 1, color: v("--band-edge"), dash: "dash" } }]
        : (!lastRba ? [{ type: "rect", xref: "paper", yref: "paper", x0: 0, x1: 1, y0: 0, y1: 1, fillcolor: v("--band"), line: { width: 0 } }] : []);
      Plotly.react(id, [
        { x, y: R.map((r) => r.yield_same_day_pct), mode: compact ? "lines" : "lines+markers", connectgaps: false, line: { color: v("--yield"), width: 3 }, marker: { size: 5, color: v("--yield") }, hovertemplate: "%{x|%-d %b}: %{y:.3f}%<extra></extra>" },
      ], lay({ xaxis: xax(R), yaxis: yax(compact ? "" : "% per year", { tickformat: ".2f" }), shapes,
        annotations: shapes.length ? [{ x: 0.995, xref: "paper", xanchor: "right", y: 1, yref: "paper", yanchor: "top", text: "Awaiting RBA release", showarrow: false, font: { size: 11, color: v("--ink-2") } }] : [] }, compact), cfg);
    },
    corr(id, R, compact = false) {
      const x = R.map((r) => r.trade_date_syd);
      Plotly.react(id, [
        { x, y: R.map((r) => r.corr20), mode: "lines", fill: "tozeroy", fillcolor: "rgba(144,133,233,.20)", line: { color: v("--corr"), width: 2.5 }, connectgaps: false, hovertemplate: "%{x|%-d %b}: %{y:+.2f}<extra></extra>" },
      ], lay({ xaxis: xax(R), yaxis: yax(compact ? "" : "Correlation", { range: [-1, 1], dtick: 0.5, zeroline: true, zerolinecolor: v("--muted"), zerolinewidth: 1 }),
        annotations: [{ x: 0.01, xref: "paper", xanchor: "left", y: 0.97, yanchor: "top", text: "Above 0: returns and yield changes tend to move in the same direction", showarrow: false, font: { size: 10, color: v("--muted") } },
                      { x: 0.01, xref: "paper", xanchor: "left", y: -0.97, yanchor: "bottom", text: "Below 0: returns and yield changes tend to move in opposite directions", showarrow: false, font: { size: 10, color: v("--muted") } }] }, compact), cfg);
    },
    scatter(id, S, compact = false) {
      const P = S.pairs, F = S.fit, xs = P.map((r) => r.yield_change_1d_bp);
      const tr = [{ x: xs, y: P.map((r) => r.asx_return_pct), mode: "markers", customdata: P.map((r) => dm(r.trade_date_syd)),
        marker: { size: compact ? 7 : 9, color: v("--asx"), opacity: 0.9, line: { color: v("--surface"), width: 2 } }, hovertemplate: "%{customdata}: yield %{x:+.1f} bp, ASX %{y:+.2f}%<extra></extra>" }];
      if (F) { const lo = Math.min(...xs), hi = Math.max(...xs); tr.push({ x: [lo, hi], y: [F.a + F.b * lo, F.a + F.b * hi], mode: "lines", line: { color: v("--avg"), width: 3 }, hoverinfo: "skip" }); }
      Plotly.react(id, tr, lay({ margin: compact ? { l: 46, r: 12, t: 6, b: 34 } : { l: 52, r: 18, t: 10, b: 40 },
        xaxis: { title: { text: "Yield change that day (bp)", font: { size: 11, color: v("--muted") } }, gridcolor: v("--grid"), zeroline: true, zerolinecolor: v("--axis"), linecolor: v("--axis"), fixedrange: true },
        yaxis: yax(compact ? "ASX 200 return (%)" : "ASX 200 return that day (%)", { zeroline: true, zerolinecolor: v("--axis") }),
        annotations: F ? [{ x: 0.98, xref: "paper", xanchor: "right", y: 0.98, yref: "paper", yanchor: "top", text: `r = ${sgn(F.r, 2)} · n = ${P.length}`, showarrow: false, font: { size: 12, color: v("--ink") } }] : [] }, compact), cfg);
    },
  };

  const triggeredRows = (S) => S.fired.length ? S.fired.slice().reverse().map((r) =>
      `<tr><td>${day(r.trade_date_syd)}</td><td>${chip(r.rag_status)}</td><td class="num"><span class="${r.rag_status === "Red" ? "down" : "amber"}">▲ ${fmt(r.volume_vs_normal_pct, 0)}% · ${r.rag_status === "Red" ? "Red alert" : "Amber"}</span></td></tr>`).join("")
    : `<tr><td colspan="3" class="flat">None in this period.</td></tr>`;
  const stripHtml = (R) => R.map((r) => `<span data-s="${r.rag_status}" title="${dm(r.trade_date_syd)}: ${r.rag_status}${r.volume_vs_normal_pct == null ? "" : " (" + sgn(r.volume_vs_normal_pct, 0) + "%)"}"></span>`).join("");
  const mixHtml = (S) => [["Green", S.green], ["Amber", S.amber], ["Red", S.red], ["Pending", S.pending], ["Excluded", S.excluded]]
    .filter((m) => m[0] !== "Excluded" || m[1]).map(([k, c]) => `<span data-s="${k}"><i></i>${k} ${c} (${fmt(S.n ? c / S.n * 100 : 0, 0)}%)</span>`).join("");

  return { D, L, ALL, T, $, v, fmt, sgn, day, dm, delta, chip, CHANGE, RANGES, MEANS, provisional, dayChg, slice, stats, text, draw, keys, triggeredRows, stripHtml, mixHtml };
})();
