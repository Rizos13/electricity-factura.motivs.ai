const API_BASE = "";

const els = {
  uploadView: document.getElementById("upload-view"),
  loadingView: document.getElementById("loading-view"),
  resultView: document.getElementById("result-view"),
  form: document.getElementById("upload-form"),
  drop: document.getElementById("drop"),
  fileInput: document.getElementById("file"),
  fileName: document.getElementById("file-name"),
  submit: document.getElementById("submit"),
  error: document.getElementById("error"),
  stepExtract: document.getElementById("step-extract"),
  stepMask: document.getElementById("step-mask"),
  stepPipeline: document.getElementById("step-pipeline"),
  stepRank: document.getElementById("step-rank"),
  profileGrid: document.getElementById("profile-grid"),
  defaultedNote: document.getElementById("defaulted-note"),
  cVerde: document.getElementById("c-verde"),
  cMarcas: document.getElementById("c-marcas"),
  recommendation: document.getElementById("recommendation"),
  disclaimer: document.getElementById("disclaimer"),
  userTotal: document.getElementById("user-total"),
  offersList: document.getElementById("offers-list"),
};

const FIELD_KEYS = [
  "comercializadora_actual",
  "tarifa_acceso",
  "region",
  "codigo_postal",
  "potencia_p1_kw",
  "consumo_kwh_punta",
  "consumo_kwh_llano",
  "consumo_kwh_valle",
  "total_factura_eur",
  "periodo_facturacion_dias",
];

const FIELD_UNITS = {
  potencia_p1_kw: "kW",
  consumo_kwh_punta: "kWh",
  consumo_kwh_llano: "kWh",
  consumo_kwh_valle: "kWh",
  total_factura_eur: "€",
  periodo_facturacion_dias: { es: "días", en: "days" },
};

let activeRunId = null;
let lastResult = null;

function showOnly(view) {
  for (const v of [els.uploadView, els.loadingView, els.resultView]) {
    v.hidden = v !== view;
  }
}

function setError(msg) {
  if (!msg) {
    els.error.hidden = true;
    els.error.textContent = "";
    return;
  }
  els.error.hidden = false;
  els.error.textContent = msg;
}

function markStep(el, state) {
  el.classList.remove("active", "done");
  if (state) el.classList.add(state);
}

function setFile(file) {
  if (!file) {
    els.fileName.textContent = "";
    els.submit.disabled = true;
    return;
  }
  els.fileName.textContent = file.name;
  els.submit.disabled = false;
}

["dragenter", "dragover"].forEach(name => {
  els.drop.addEventListener(name, e => {
    e.preventDefault();
    els.drop.classList.add("dragover");
  });
});
["dragleave", "drop"].forEach(name => {
  els.drop.addEventListener(name, e => {
    e.preventDefault();
    els.drop.classList.remove("dragover");
  });
});
els.drop.addEventListener("drop", e => {
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    els.fileInput.files = e.dataTransfer.files;
    setFile(e.dataTransfer.files[0]);
  }
});
els.fileInput.addEventListener("change", () => {
  const file = els.fileInput.files && els.fileInput.files[0];
  setFile(file);
});

els.form.addEventListener("submit", async (e) => {
  e.preventDefault();
  setError("");
  const file = els.fileInput.files && els.fileInput.files[0];
  if (!file) return;

  showOnly(els.loadingView);
  markStep(els.stepExtract, "active");
  markStep(els.stepMask, null);
  markStep(els.stepPipeline, null);
  markStep(els.stepRank, null);

  setTimeout(() => { markStep(els.stepExtract, "done"); markStep(els.stepMask, "active"); }, 400);
  setTimeout(() => { markStep(els.stepMask, "done"); markStep(els.stepPipeline, "active"); }, 900);

  try {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: fd });
    if (!res.ok) {
      const detail = await safeJson(res);
      throw new Error(detail?.detail || `Error ${res.status}`);
    }
    const data = await res.json();
    activeRunId = data.run_id;
    markStep(els.stepPipeline, "done");
    markStep(els.stepRank, "active");
    history.replaceState(null, "", `/?run_id=${encodeURIComponent(activeRunId)}`);
    await loadResult();
  } catch (err) {
    showOnly(els.uploadView);
    setError(err.message || I18N.t("error_unexpected"));
  }
});

[els.cVerde, els.cMarcas].forEach(el => {
  el.addEventListener("change", () => {
    if (activeRunId) loadResult();
  });
});

I18N.onChange(() => {
  if (lastResult) renderResult(lastResult);
});

async function loadResult() {
  if (!activeRunId) return;
  const qs = new URLSearchParams({
    only_verde: els.cVerde.checked ? "true" : "false",
    solo_marcas_conocidas: els.cMarcas.checked ? "true" : "false",
    top_n: "10",
  });
  try {
    const res = await fetch(`${API_BASE}/api/result/${encodeURIComponent(activeRunId)}?${qs}`);
    if (res.status === 404) {
      showOnly(els.uploadView);
      setError(I18N.t("session_expired"));
      return;
    }
    if (!res.ok) throw new Error(`Error ${res.status}`);
    const data = await res.json();
    lastResult = data;
    renderResult(data);
    markStep(els.stepRank, "done");
    showOnly(els.resultView);
  } catch (err) {
    setError(err.message || I18N.t("error_loading"));
  }
}

function renderResult(data) {
  renderProfile(data.profile_summary, data.extraction);
  if (data.user_total_eur) {
    const days = data.user_period_days || 30;
    const monthly = data.user_monthly_eur || data.user_total_eur;
    els.userTotal.textContent = `· ${I18N.t("your_bill")}: ${formatEur(data.user_total_eur)} (${days} ${I18N.t("days_short")}, ≈${formatEur(monthly)}${I18N.t("monthly_suffix")})`;
  } else {
    els.userTotal.textContent = "";
  }
  renderRecommendation(data.recommendation, data);
  renderDisclaimer(data);
  renderOffers(data.ranked_offers);
}

function renderDisclaimer(data) {
  els.disclaimer.innerHTML = "";
  els.disclaimer.className = "disclaimer";
  const quality = data.extraction_quality || "high";
  let titleKey, bodyKey, body;
  if (quality === "low") {
    titleKey = "quality_low_title";
    bodyKey = "quality_low_body";
    els.disclaimer.classList.add("warning");
  } else if (quality === "medium") {
    titleKey = "quality_medium_title";
    bodyKey = "quality_medium_body";
    els.disclaimer.classList.add("warning");
  } else if (data.user_annual_kwh) {
    titleKey = "disclaimer_title";
    body = I18N.t("disclaimer_body").replace("{kwh}", Math.round(data.user_annual_kwh));
  } else {
    els.disclaimer.hidden = true;
    return;
  }
  els.disclaimer.hidden = false;
  const titleEl = document.createElement("div");
  titleEl.className = "disclaimer-title";
  titleEl.textContent = I18N.t(titleKey);
  const bodyEl = document.createElement("div");
  bodyEl.className = "disclaimer-body";
  bodyEl.textContent = body || I18N.t(bodyKey);
  els.disclaimer.appendChild(titleEl);
  els.disclaimer.appendChild(bodyEl);
  if (data.cnmc_snapshot_date) {
    const snap = document.createElement("div");
    snap.className = "disclaimer-snap";
    snap.textContent = `${I18N.t("snapshot_label")}: ${data.cnmc_snapshot_date}`;
    els.disclaimer.appendChild(snap);
  }
}

function renderRecommendation(rec, data) {
  els.recommendation.innerHTML = "";
  if (!rec) {
    els.recommendation.hidden = true;
    return;
  }
  els.recommendation.hidden = false;

  const title = document.createElement("div");
  title.className = "rec-title";
  title.textContent = I18N.t("recommendation_title");

  const brand = document.createElement("div");
  brand.className = "rec-brand";
  brand.textContent = rec.comercializadora;

  const oferta = document.createElement("div");
  oferta.className = "rec-oferta";
  oferta.textContent = rec.oferta || "";

  const savings = document.createElement("div");
  savings.className = "rec-savings";
  const annual = rec.savings_annual_eur || 0;
  if (annual > 0) {
    savings.classList.add("pos");
    savings.textContent = `${I18N.t("recommendation_save_year")}: ${formatEur(annual)}`;
  } else if (annual < 0) {
    savings.classList.add("neg");
    savings.textContent = `${I18N.t("recommendation_more_year")}: ${formatEur(Math.abs(annual))}`;
  }

  const reason = document.createElement("div");
  reason.className = "rec-reason";
  reason.textContent = I18N.t(rec.rationale_key);

  const cta = document.createElement("a");
  cta.className = "rec-cta";
  cta.href = rec.brand_url;
  cta.target = "_blank";
  cta.rel = "noopener";
  cta.textContent = `${I18N.t("visit_site")} →`;

  els.recommendation.appendChild(title);
  els.recommendation.appendChild(brand);
  if (rec.oferta) els.recommendation.appendChild(oferta);
  els.recommendation.appendChild(savings);
  if (data && annual !== 0) els.recommendation.appendChild(buildCalcBlock(rec, data));
  els.recommendation.appendChild(reason);
  els.recommendation.appendChild(cta);
}

function buildCalcBlock(rec, data) {
  const wrap = document.createElement("div");
  wrap.className = "rec-calc";
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "rec-calc-btn";
  btn.setAttribute("aria-expanded", "false");
  btn.textContent = I18N.t("rec_calc_btn");
  const panel = document.createElement("div");
  panel.className = "rec-calc-panel";
  panel.hidden = true;
  panel.appendChild(renderCalcPanel(rec, data));
  btn.addEventListener("click", () => {
    const open = panel.hidden;
    panel.hidden = !open;
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  });
  wrap.appendChild(btn);
  wrap.appendChild(panel);
  return wrap;
}

function renderCalcPanel(rec, data) {
  const ub = data.user_breakdown || {};
  const ob = rec.offer_breakdown || {};
  const userKw = data.user_potencia_kw || 0;
  const userKwh = data.user_annual_kwh || 0;
  const userMonthly = data.user_monthly_eur || 0;
  const offerMonthly = rec.importe_estimated_eur || 0;
  const monthSav = rec.savings_vs_user_eur || 0;
  const annualSav = rec.savings_annual_eur || 0;

  const frag = document.createDocumentFragment();
  frag.appendChild(calcGroup(I18N.t("rec_calc_h_bill"), [
    [I18N.t("rec_calc_row_potencia"), formatEur(ub.monthly_potencia_eur || 0), powerNote(userKw)],
    [I18N.t("rec_calc_row_energy"),   formatEur(ub.monthly_energy_eur || 0),   energyNote(userKwh, ub.effective_energy_eur_kwh)],
    [I18N.t("rec_calc_row_fixed"),    formatEur(ub.monthly_fixed_eur || 0),    ""],
    [I18N.t("rec_calc_row_taxes"),    formatEur(ub.monthly_taxes_eur || 0),    ""],
    [I18N.t("rec_calc_row_total"),    formatEur(userMonthly),                  "", true],
  ]));
  frag.appendChild(calcGroup(I18N.t("rec_calc_h_plan"), [
    [I18N.t("rec_calc_row_potencia"), formatEur(ob.monthly_potencia_eur || 0), powerNote(userKw)],
    [I18N.t("rec_calc_row_energy"),   formatEur(ob.monthly_energy_eur || 0),   energyNote(userKwh, ob.effective_energy_eur_kwh)],
    [I18N.t("rec_calc_row_fixed"),    formatEur(ob.monthly_fixed_eur || 0),    ""],
    [I18N.t("rec_calc_row_taxes"),    formatEur(ob.monthly_taxes_eur || 0),    ""],
    [I18N.t("rec_calc_row_total"),    formatEur(offerMonthly),                 "", true],
  ]));
  const savValue = `${formatEur(userMonthly)} − ${formatEur(offerMonthly)} = ${formatEur(monthSav)}${I18N.t("monthly_suffix")}\n${formatEur(monthSav)} × 12 = ${formatEur(Math.abs(annualSav))}${I18N.t("annual_suffix")}`;
  const savBlock = document.createElement("div");
  savBlock.className = "rec-calc-group rec-calc-save";
  const savTitle = document.createElement("div");
  savTitle.className = "rec-calc-group-title";
  savTitle.textContent = I18N.t("rec_calc_h_save");
  const savBody = document.createElement("div");
  savBody.className = "rec-calc-save-body";
  savBody.textContent = savValue;
  savBlock.appendChild(savTitle);
  savBlock.appendChild(savBody);
  frag.appendChild(savBlock);

  const foot = document.createElement("p");
  foot.className = "rec-calc-foot";
  foot.textContent = I18N.t("rec_calc_disclaimer");
  frag.appendChild(foot);
  return frag;
}

function powerNote(kw) {
  if (!kw) return "";
  return I18N.t("rec_calc_potencia_note").replace("{kw}", formatNumber(kw, 1));
}

function energyNote(kwh, eurKwh) {
  if (!kwh || !eurKwh) return "";
  return I18N.t("rec_calc_energy_note")
    .replace("{kwh}", formatKwh(kwh))
    .replace("{price}", formatNumber(eurKwh, 4));
}

function calcGroup(title, rows) {
  const block = document.createElement("div");
  block.className = "rec-calc-group";
  const head = document.createElement("div");
  head.className = "rec-calc-group-title";
  head.textContent = title;
  block.appendChild(head);
  for (const [label, amount, note, isTotal] of rows) {
    const row = document.createElement("div");
    row.className = isTotal ? "rec-calc-line rec-calc-total" : "rec-calc-line";
    const lab = document.createElement("div");
    lab.className = "rec-calc-line-label";
    lab.textContent = label;
    const val = document.createElement("div");
    val.className = "rec-calc-line-value";
    val.textContent = amount + I18N.t("monthly_suffix");
    const nt = document.createElement("div");
    nt.className = "rec-calc-line-note";
    nt.textContent = note;
    row.appendChild(lab);
    row.appendChild(val);
    row.appendChild(nt);
    block.appendChild(row);
  }
  return block;
}

function formatNumber(v, digits) {
  return Number(v).toLocaleString(I18N.lang === "en" ? "en-US" : "es-ES", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatKwh(v) {
  return Math.round(v).toLocaleString(I18N.lang === "en" ? "en-US" : "es-ES");
}

function renderProfile(profile, extraction) {
  els.profileGrid.innerHTML = "";
  for (const key of FIELD_KEYS) {
    const val = profile[key];
    if (val === null || val === undefined || val === "") continue;
    const row = document.createElement("div");
    row.className = "row";
    const k = document.createElement("div");
    k.className = "key";
    k.textContent = I18N.t(`field_${key}`);
    const v = document.createElement("div");
    v.className = "val";
    v.textContent = formatVal(key, val);
    row.appendChild(k);
    row.appendChild(v);
    els.profileGrid.appendChild(row);
  }
  const defaulted = extraction.defaulted_fields || [];
  if (defaulted.length > 0) {
    els.defaultedNote.hidden = false;
    els.defaultedNote.textContent = `${I18N.t("defaulted_prefix")}: ${defaulted.join(", ")}.`;
  } else {
    els.defaultedNote.hidden = true;
  }
}

function renderOffers(offers) {
  els.offersList.innerHTML = "";
  if (!offers || offers.length === 0) {
    const p = document.createElement("p");
    p.className = "ranking-note";
    p.textContent = I18N.t("no_offers");
    els.offersList.appendChild(p);
    return;
  }
  for (const o of offers) {
    const card = document.createElement("div");
    card.className = "offer";

    const rank = document.createElement("div");
    rank.className = "rank";
    rank.textContent = o.rank;

    const body = document.createElement("div");
    body.className = "body";

    const comer = document.createElement("div");
    comer.className = "comer";
    comer.textContent = o.comercializadora || "—";

    const oferta = document.createElement("div");
    oferta.className = "oferta";
    oferta.textContent = o.oferta || "";

    const badges = document.createElement("div");
    badges.className = "badges";
    appendBadge(badges, typeLabel(o.tipo_precio), typeClass(o.tipo_precio));
    if (o.verde === "si") appendBadge(badges, I18N.t("badge_verde"), "verde");
    if (o.is_promotional) appendBadge(badges, I18N.t("promo_label"), "promo");

    const commitment = document.createElement("div");
    commitment.className = "oferta commitment";
    commitment.textContent = I18N.t(o.commitment_key || "commitment_unknown");

    body.appendChild(comer);
    body.appendChild(oferta);
    if (commitment.textContent) body.appendChild(commitment);
    body.appendChild(badges);

    const money = document.createElement("div");
    money.className = "money";
    const imp = document.createElement("div");
    imp.className = "importe";
    imp.textContent = formatEur(o.importe_estimated_eur);
    const sav = document.createElement("div");
    sav.className = "savings";
    if (o.savings_vs_user_eur > 0) {
      sav.classList.add("pos");
      sav.textContent = `${I18N.t("save_x")} ${formatEur(o.savings_vs_user_eur)}`;
    } else if (o.savings_vs_user_eur < 0) {
      sav.classList.add("neg");
      sav.textContent = `+${formatEur(Math.abs(o.savings_vs_user_eur))} ${I18N.t("more_x")}`;
    } else {
      sav.textContent = I18N.t("same_price");
    }
    money.appendChild(imp);
    money.appendChild(sav);

    if (o.brand_url) {
      const visit = document.createElement("a");
      visit.className = "visit";
      visit.href = o.brand_url;
      visit.target = "_blank";
      visit.rel = "noopener";
      visit.textContent = `${I18N.t("visit_site")} →`;
      money.appendChild(visit);
    }

    card.appendChild(rank);
    card.appendChild(body);
    card.appendChild(money);
    els.offersList.appendChild(card);
  }
}

function appendBadge(container, text, cls) {
  const b = document.createElement("span");
  b.className = `badge ${cls}`;
  b.textContent = text;
  container.appendChild(b);
}

function typeLabel(t) {
  if (t === "fijo") return I18N.t("type_fijo");
  if (t === "flexible") return I18N.t("type_flexible");
  if (t === "pvpc") return I18N.t("type_pvpc");
  return t || "—";
}
function typeClass(t) {
  if (t === "fijo") return "fijo";
  if (t === "flexible") return "flex";
  if (t === "pvpc") return "pvpc";
  return "";
}
function formatEur(v) {
  const n = Number(v);
  if (Number.isNaN(n)) return "—";
  const decimal = I18N.lang === "en" ? "." : ",";
  return n.toFixed(2).replace(".", decimal) + " €";
}
function formatVal(key, val) {
  let unit = FIELD_UNITS[key];
  if (unit && typeof unit === "object") unit = unit[I18N.lang] || unit.es;
  if (unit === "€") return formatEur(val);
  if (typeof val === "number") return val + (unit ? " " + unit : "");
  return String(val);
}
async function safeJson(res) {
  try { return await res.json(); } catch { return null; }
}

const params = new URLSearchParams(location.search);
const incomingRunId = params.get("run_id");
if (incomingRunId) {
  activeRunId = incomingRunId;
  loadResult();
}

const bugModal = document.getElementById("bug-modal");
const bugOpen = document.getElementById("bug-open");
const bugForm = document.getElementById("bug-form");
const bugStatus = document.getElementById("bug-status");
if (bugOpen && bugModal) {
  bugOpen.addEventListener("click", () => { bugModal.hidden = false; });
  bugModal.querySelectorAll("[data-close]").forEach(el => {
    el.addEventListener("click", () => { bugModal.hidden = true; });
  });
}
const bugScreenshot = document.getElementById("bug-screenshot");
const bugScreenshotName = document.getElementById("bug-screenshot-name");
const BUG_SCREENSHOT_MAX = 5 * 1024 * 1024;
if (bugScreenshot && bugScreenshotName) {
  bugScreenshot.addEventListener("change", () => {
    const f = bugScreenshot.files && bugScreenshot.files[0];
    if (!f) { bugScreenshotName.hidden = true; bugScreenshotName.textContent = ""; return; }
    bugScreenshotName.hidden = false;
    bugScreenshotName.textContent = `${f.name} (${Math.round(f.size / 1024)} KB)`;
  });
}
if (bugForm) {
  bugForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    bugStatus.hidden = true;
    const description = document.getElementById("bug-desc").value.trim();
    const email = document.getElementById("bug-email").value.trim();
    const file = bugScreenshot && bugScreenshot.files && bugScreenshot.files[0];
    if (file && file.size > BUG_SCREENSHOT_MAX) {
      bugStatus.hidden = false;
      bugStatus.className = "modal-status err";
      bugStatus.textContent = I18N.t("bug_screenshot_too_big");
      return;
    }
    const fd = new FormData();
    fd.append("description", description);
    if (email) fd.append("email", email);
    if (file) fd.append("screenshot", file);
    try {
      const res = await fetch("/api/bug-report", { method: "POST", body: fd });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      bugStatus.hidden = false;
      bugStatus.className = "modal-status ok";
      bugStatus.textContent = I18N.t("bug_sent_ok");
      bugForm.reset();
      if (bugScreenshotName) { bugScreenshotName.hidden = true; bugScreenshotName.textContent = ""; }
    } catch (err) {
      bugStatus.hidden = false;
      bugStatus.className = "modal-status err";
      bugStatus.textContent = I18N.t("bug_sent_error");
    }
  });
}
