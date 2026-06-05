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
  cPerm: document.getElementById("c-perm"),
  cFijo: document.getElementById("c-fijo"),
  userTotal: document.getElementById("user-total"),
  offersList: document.getElementById("offers-list"),
};

const FIELD_LABELS = {
  comercializadora_actual: "Tu comercializador",
  tarifa_acceso: "Tarifa de acceso",
  region: "Región",
  codigo_postal: "Código postal",
  potencia_p1_kw: "Potencia P1",
  consumo_kwh_punta: "Consumo punta",
  consumo_kwh_llano: "Consumo llano",
  consumo_kwh_valle: "Consumo valle",
  total_factura_eur: "Total factura",
  periodo_facturacion_dias: "Período facturación",
};

const FIELD_UNITS = {
  potencia_p1_kw: "kW",
  consumo_kwh_punta: "kWh",
  consumo_kwh_llano: "kWh",
  consumo_kwh_valle: "kWh",
  total_factura_eur: "€",
  periodo_facturacion_dias: "días",
};

let activeRunId = null;

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
    setError(err.message || "Error inesperado");
  }
});

[els.cVerde, els.cPerm, els.cFijo].forEach(el => {
  el.addEventListener("change", () => {
    if (activeRunId) loadResult();
  });
});

async function loadResult() {
  if (!activeRunId) return;
  const qs = new URLSearchParams({
    only_verde: els.cVerde.checked ? "true" : "false",
    no_permanencia: els.cPerm.checked ? "true" : "false",
    only_fijo: els.cFijo.checked ? "true" : "false",
    top_n: "10",
  });
  try {
    const res = await fetch(`${API_BASE}/api/result/${encodeURIComponent(activeRunId)}?${qs}`);
    if (res.status === 404) {
      showOnly(els.uploadView);
      setError("La sesión ha caducado. Sube tu factura de nuevo.");
      return;
    }
    if (!res.ok) throw new Error(`Error ${res.status}`);
    const data = await res.json();
    renderResult(data);
    markStep(els.stepRank, "done");
    showOnly(els.resultView);
  } catch (err) {
    setError(err.message || "Error al cargar resultado");
  }
}

function renderResult(data) {
  renderProfile(data.profile_summary, data.extraction);
  els.userTotal.textContent = data.user_total_eur
    ? `· tu factura: ${formatEur(data.user_total_eur)}`
    : "";
  renderOffers(data.ranked_offers);
}

function renderProfile(profile, extraction) {
  els.profileGrid.innerHTML = "";
  for (const [key, label] of Object.entries(FIELD_LABELS)) {
    const val = profile[key];
    if (val === null || val === undefined || val === "") continue;
    const row = document.createElement("div");
    row.className = "row";
    const k = document.createElement("div");
    k.className = "key";
    k.textContent = label;
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
    els.defaultedNote.textContent = `Estimados a partir del total: ${defaulted.join(", ")}.`;
  } else {
    els.defaultedNote.hidden = true;
  }
}

function renderOffers(offers) {
  els.offersList.innerHTML = "";
  if (!offers || offers.length === 0) {
    const p = document.createElement("p");
    p.className = "ranking-note";
    p.textContent = "Ninguna oferta coincide con los filtros seleccionados.";
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
    if (o.verde === "si") appendBadge(badges, "verde", "verde");
    if (o.penalizacion === "si") appendBadge(badges, "permanencia", "pen");

    body.appendChild(comer);
    body.appendChild(oferta);
    body.appendChild(badges);

    const money = document.createElement("div");
    money.className = "money";
    const imp = document.createElement("div");
    imp.className = "importe";
    imp.textContent = formatEur(o.importe_primera_factura_eur);
    const sav = document.createElement("div");
    sav.className = "savings";
    if (o.savings_vs_user_eur > 0) {
      sav.classList.add("pos");
      sav.textContent = `ahorra ${formatEur(o.savings_vs_user_eur)}`;
    } else if (o.savings_vs_user_eur < 0) {
      sav.classList.add("neg");
      sav.textContent = `+${formatEur(Math.abs(o.savings_vs_user_eur))} más`;
    } else {
      sav.textContent = "mismo precio";
    }
    money.appendChild(imp);
    money.appendChild(sav);

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
  if (t === "fijo") return "precio fijo";
  if (t === "flexible") return "flexible";
  if (t === "pvpc") return "pvpc";
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
  return n.toFixed(2).replace(".", ",") + " €";
}
function formatVal(key, val) {
  const unit = FIELD_UNITS[key];
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
