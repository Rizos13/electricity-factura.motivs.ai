const I18N_DICT = {
  es: {
    nav_about: "Cómo funciona",
    nav_upload: "Subir factura",
    hero_title: "Sube tu factura, te decimos a qué tarifa pasarte.",
    hero_lead: "Compara tu factura con todas las ofertas del comparador oficial de la CNMC. Sin cuenta, sin guardar nada, sin compartir tus datos personales.",
    verified_title: "Verificado por Motivs SRE",
    verified_sub: "Privacidad por diseño, nada se guarda, datos verificados del comparador oficial CNMC.",
    drop_title: "Suelta aquí tu factura",
    drop_sub: "o haz clic para seleccionar PDF, JPG o PNG (máx 8 MB)",
    submit_btn: "Comparar",
    loading_title: "Procesando tu factura",
    step_extract: "Extrayendo campos del documento",
    step_mask: "Anonimizando datos personales",
    step_pipeline: "Ejecutando gateway de seguridad SRE",
    step_rank: "Comparando con ofertas de la CNMC",
    profile_title: "Tu perfil (anonimizado)",
    constraints_title: "Filtra a tu gusto",
    c_verde: "Sólo energía verde",
    c_perm: "Sin permanencia",
    c_fijo: "Sólo precio fijo",
    catalog_verified_title: "Catálogo verificado por Motivs SRE",
    catalog_verified_sub: "Datos del comparador oficial CNMC validados por el gateway de seguridad.",
    ranking_title: "Top ofertas para tu perfil",
    ranking_note: "Cifras estimadas a partir del perfil medio del comparador CNMC. Tu ahorro real depende de tu consumo.",
    upload_another: "Subir otra factura",
    foot_data: "Datos:",
    foot_data_link: "comparador CNMC",
    foot_no_state: "Sin cuenta, sin historial, sin cookies de tracking.",
    your_bill: "tu factura",
    save_x: "ahorra",
    more_x: "más",
    same_price: "mismo precio",
    no_offers: "Ninguna oferta coincide con los filtros seleccionados.",
    defaulted_prefix: "Estimados a partir del total",
    session_expired: "La sesión ha caducado. Sube tu factura de nuevo.",
    error_unexpected: "Error inesperado",
    error_loading: "Error al cargar resultado",
    type_fijo: "precio fijo",
    type_flexible: "flexible",
    type_pvpc: "pvpc",
    badge_verde: "verde",
    badge_permanencia: "permanencia",
    field_comercializadora_actual: "Tu comercializador",
    field_tarifa_acceso: "Tarifa de acceso",
    field_region: "Región",
    field_codigo_postal: "Código postal",
    field_potencia_p1_kw: "Potencia P1",
    field_consumo_kwh_punta: "Consumo punta",
    field_consumo_kwh_llano: "Consumo llano",
    field_consumo_kwh_valle: "Consumo valle",
    field_total_factura_eur: "Total factura",
    field_periodo_facturacion_dias: "Período facturación",
    about_title: "Cómo funciona",
    about_h_source: "De dónde vienen las tarifas",
    about_p_source_1: "Todos los precios provienen del Comparador oficial de la CNMC (Comisión Nacional de los Mercados y la Competencia), el regulador español. El catálogo incluye unas 50 ofertas verificadas de más de 30 comercializadoras, entre ellas Endesa, Iberdrola, Naturgy, Repsol, Octopus, TotalEnergies, Holaluz, Imagina y otras.",
    about_p_source_2: "No usamos comparadores comerciales ni datos pagados por las comercializadoras. El ranking es determinístico: no hay LLM que decida qué oferta mostrarte, sólo un cálculo público y reproducible.",
    about_h_data: "Qué hacemos con tus datos",
    about_p_data_intro: "Tu factura pasa por nuestro gateway de seguridad SRE antes de cualquier análisis. En ese paso:",
    about_li_drop: "Eliminamos nombre, dirección, número de factura y número de contrato.",
    about_li_hash: "Anonimizamos tu CUPS, NIF e IBAN con HMAC (hash irreversible).",
    about_li_log: "Estos campos no llegan al motor de comparación, ni al log, ni se guardan.",
    about_p_data_outro: "El resto (consumo en kWh, potencia, tarifa de acceso) no es PII y sí se usa para la comparación.",
    about_h_session: "Sin cuenta, sin historial",
    about_p_session_1: "No hay registro. No hay inicio de sesión. No guardamos tu perfil más allá de 30 minutos en memoria volátil. Si vuelves mañana, tendrás que subir tu factura de nuevo, y eso es intencional.",
    about_p_session_2: "Si necesitas un seguimiento histórico, este no es el servicio correcto.",
    about_h_numbers: "Honestidad sobre las cifras",
    about_p_numbers_1: "El comparador CNMC calcula el importe de cada oferta para un perfil medio de hogar, no para tu consumo exacto. Por eso las cifras del ranking son estimaciones: tu ahorro real depende de tu consumo en kWh, tus periodos punta/llano/valle y tu potencia contratada.",
    about_p_numbers_2: "Para una simulación exacta, después de elegir una oferta visita el comparador de la CNMC directamente con tu consumo.",
  },
  en: {
    nav_about: "How it works",
    nav_upload: "Upload bill",
    hero_title: "Upload your bill, we'll tell you which tariff to switch to.",
    hero_lead: "Compare your bill against every offer in the official CNMC comparator. No account, nothing stored, nothing shared.",
    verified_title: "Verified by Motivs SRE",
    verified_sub: "Privacy by design, nothing stored, verified data from the official CNMC comparator.",
    drop_title: "Drop your bill here",
    drop_sub: "or click to choose PDF, JPG, or PNG (max 8 MB)",
    submit_btn: "Compare",
    loading_title: "Processing your bill",
    step_extract: "Extracting document fields",
    step_mask: "Masking personal data",
    step_pipeline: "Running the SRE security gateway",
    step_rank: "Comparing against CNMC offers",
    profile_title: "Your profile (anonymized)",
    constraints_title: "Filter as you like",
    c_verde: "Green energy only",
    c_perm: "No commitment",
    c_fijo: "Fixed price only",
    catalog_verified_title: "Catalogue verified by Motivs SRE",
    catalog_verified_sub: "Data from the official CNMC comparator validated by the security gateway.",
    ranking_title: "Top offers for your profile",
    ranking_note: "Estimated figures based on the CNMC comparator's average profile. Your actual savings depend on your consumption.",
    upload_another: "Upload another bill",
    foot_data: "Data:",
    foot_data_link: "CNMC comparator",
    foot_no_state: "No account, no history, no tracking cookies.",
    your_bill: "your bill",
    save_x: "save",
    more_x: "more",
    same_price: "same price",
    no_offers: "No offers match the selected filters.",
    defaulted_prefix: "Estimated from total",
    session_expired: "Session expired. Upload your bill again.",
    error_unexpected: "Unexpected error",
    error_loading: "Error loading result",
    type_fijo: "fixed price",
    type_flexible: "variable",
    type_pvpc: "pvpc",
    badge_verde: "green",
    badge_permanencia: "commitment",
    field_comercializadora_actual: "Your provider",
    field_tarifa_acceso: "Access tariff",
    field_region: "Region",
    field_codigo_postal: "Postal code",
    field_potencia_p1_kw: "Power P1",
    field_consumo_kwh_punta: "Peak consumption",
    field_consumo_kwh_llano: "Mid consumption",
    field_consumo_kwh_valle: "Off-peak consumption",
    field_total_factura_eur: "Bill total",
    field_periodo_facturacion_dias: "Billing period",
    about_title: "How it works",
    about_h_source: "Where the tariffs come from",
    about_p_source_1: "All prices come from the official CNMC Comparator (National Commission for Markets and Competition), the Spanish energy regulator. The catalogue holds around 50 verified offers from more than 30 retailers, including Endesa, Iberdrola, Naturgy, Repsol, Octopus, TotalEnergies, Holaluz, Imagina and others.",
    about_p_source_2: "We don't use commercial comparators or data paid for by retailers. The ranking is deterministic: no LLM decides which offer to show you, just a public, reproducible calculation.",
    about_h_data: "What we do with your data",
    about_p_data_intro: "Your bill goes through our SRE security gateway before any analysis. In that step:",
    about_li_drop: "We remove your name, address, bill number and contract number.",
    about_li_hash: "We anonymize your CUPS, NIF and IBAN with HMAC (irreversible hash).",
    about_li_log: "These fields don't reach the comparison engine, the logs, or any persistent store.",
    about_p_data_outro: "The rest (kWh consumption, power, access tariff) is not PII and is used for the comparison.",
    about_h_session: "No account, no history",
    about_p_session_1: "No signup. No login. We don't keep your profile beyond 30 minutes in volatile memory. If you come back tomorrow, you'll need to upload your bill again — that's intentional.",
    about_p_session_2: "If you need historical tracking, this isn't the right service.",
    about_h_numbers: "Honesty about the numbers",
    about_p_numbers_1: "The CNMC comparator calculates each offer's amount for an average household profile, not for your exact consumption. So the ranking figures are estimates: your real savings depend on your kWh consumption, peak/mid/off-peak periods, and contracted power.",
    about_p_numbers_2: "For an exact simulation, after choosing an offer visit the CNMC comparator directly with your consumption.",
  },
};

const I18N = {
  lang: null,
  listeners: [],
  init() {
    const stored = (typeof localStorage !== "undefined" && localStorage.getItem("lang")) || null;
    const fallback = (navigator.language || "es").startsWith("en") ? "en" : "es";
    this.lang = stored && I18N_DICT[stored] ? stored : fallback;
    document.documentElement.lang = this.lang;
  },
  t(key) {
    const table = I18N_DICT[this.lang] || I18N_DICT.es;
    return table[key] || key;
  },
  apply(root = document) {
    root.querySelectorAll("[data-i18n]").forEach(el => {
      el.textContent = this.t(el.getAttribute("data-i18n"));
    });
  },
  setLang(lang) {
    if (!I18N_DICT[lang] || lang === this.lang) return;
    this.lang = lang;
    try { localStorage.setItem("lang", lang); } catch (_) {}
    document.documentElement.lang = lang;
    this.apply();
    for (const fn of this.listeners) fn(lang);
    document.querySelectorAll("[data-lang-btn]").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-lang-btn") === lang);
    });
  },
  onChange(fn) {
    this.listeners.push(fn);
  },
};

I18N.init();

document.addEventListener("DOMContentLoaded", () => {
  I18N.apply();
  document.querySelectorAll("[data-lang-btn]").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-lang-btn") === I18N.lang);
    btn.addEventListener("click", e => {
      e.preventDefault();
      I18N.setLang(btn.getAttribute("data-lang-btn"));
    });
  });
});
