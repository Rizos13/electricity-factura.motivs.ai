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
  els.userTotal.textContent = data.user_total_eur
    ? `· ${I18N.t("your_bill")}: ${formatEur(data.user_total_eur)}`
    : "";
  renderRecommendation(data.recommendation);
  renderDisclaimer(data);
  renderOffers(data.ranked_offers);
}

function renderDisclaimer(data) {
  const kwh = data.user_annual_kwh;
  if (!kwh) {
    els.disclaimer.hidden = true;
    return;
  }
  els.disclaimer.hidden = false;
  els.disclaimer.innerHTML = "";
  const title = document.createElement("div");
  title.className = "disclaimer-title";
  title.textContent = I18N.t("disclaimer_title");
  const body = document.createElement("div");
  body.className = "disclaimer-body";
  body.textContent = I18N.t("disclaimer_body").replace("{kwh}", Math.round(kwh));
  els.disclaimer.appendChild(title);
  els.disclaimer.appendChild(body);
  if (data.cnmc_snapshot_date) {
    const snap = document.createElement("div");
    snap.className = "disclaimer-snap";
    snap.textContent = `${I18N.t("snapshot_label")}: ${data.cnmc_snapshot_date}`;
    els.disclaimer.appendChild(snap);
  }
}

function renderRecommendation(rec) {
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
  els.recommendation.appendChild(reason);
  els.recommendation.appendChild(cta);
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
