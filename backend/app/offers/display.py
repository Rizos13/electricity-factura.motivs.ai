from __future__ import annotations

import re


_BRAND_INFO = {
    "TOTALENERGIES CLIENTES":                       ("TotalEnergies", "major", "https://www.totalenergies.es/particulares/electricidad-gas"),
    "TOTALENERGIES MERCADO ESPAÑA":                 ("TotalEnergies", "major", "https://www.totalenergies.es/particulares/electricidad-gas"),
    "ENDESA ENERGÍA":                               ("Endesa", "major", "https://www.endesa.com/es/luz"),
    "IBERDROLA CLIENTES":                           ("Iberdrola", "major", "https://www.iberdrola.es/luz"),
    "NATURGY CLIENTES":                             ("Naturgy", "major", "https://www.naturgy.es/hogar/luz"),
    "REPSOL COMERCIALIZADORA DE ELECTRICIDAD Y GAS": ("Repsol", "major", "https://www.repsol.es/particulares/luz-y-gas/"),
    "OCTOPUS ENERGY ESPAÑA":                        ("Octopus Energy", "major", "https://octopusenergy.es/"),
    "ENI PLENITUDE IBERIA":                         ("Eni Plenitude", "major", "https://www.plenitude.com/es/particulares/luz"),
    "IMAGINA ENERGIA":                              ("Imagina Energía", "major", "https://imaginaenergia.com/luz"),
    "ENERGYA VM GESTION DE ENERGÍA":                ("Energya VM", "niche", "https://www.energyavm.es/"),
    "DOMESTICA GAS Y ELECTRICIDAD":                 ("Doméstica", "niche", "https://www.domesticagasyelectricidad.com/"),
    "ENERGIA NUFRI":                                ("Energía Nufri", "niche", "https://www.energianufri.com/"),
    "FENIE ENERGIA":                                ("Fenie Energía", "niche", "https://www.fenieenergia.es/"),
    "TELECOR":                                      ("Telecor", "niche", "https://www.telecorenergia.es/"),
    "DAIMUZ ENERGÍA":                               ("Daimuz", "niche", "https://www.daimuzenergia.es/"),
    "ENERGYASSET COMERCIALIZADORA DE ENERGÍA":      ("Energyasset", "niche", "https://www.energyasset.es/"),
    "GAOLANIA SERVICIOS":                           ("Gaolania", "niche", "https://www.gaolaniaenergia.com/"),
    "COMPAÑIA LUMISA ENERGIAS":                     ("Lumisa Energías", "niche", "https://lumisa.es/"),
    "CATGAS ENERGIA":                               ("Catgas Energía", "niche", "https://www.catgasenergia.com/"),
    "WEKIWI":                                       ("Wekiwi", "niche", "https://wekiwi.es/"),
    "CIDE HCENERGÍA":                               ("CIDE HC", "niche", "https://www.cidehcenergia.com/"),
    "HIDROELECTRICA DE SILLEDA COMERCIALIZADORA":   ("Hidroeléctrica de Silleda", "niche", "https://www.hidrosilleda.com/"),
    "DISA ENERGIA ELECTRICA":                       ("DISA Energía", "niche", "https://www.disaenergia.es/"),
    "INER ENERGIA CASTILLA LA MANCHA":              ("INER Castilla La Mancha", "niche", "https://www.iner.es/"),
    "INER EUSKADI":                                 ("INER Euskadi", "niche", "https://www.iner.es/"),
    "NEXUS ENERGIA":                                ("Nexus Energía", "niche", "https://www.nexusenergia.com/"),
    "ENSTROGA":                                     ("Enstroga", "niche", "https://www.enstroga.es/"),
    "TRACTAMENT I SELECCIÓ DE RESIDUS":             ("TIRSA Energía", "niche", "https://www.tirsa.cat/"),
    "ESCANDINAVA DE ELECTRICIDAD":                  ("Escandinava de Electricidad", "niche", "https://www.escandinavaelectricidad.es/"),
    "NIBA":                                         ("niba", "niche", "https://www.nibaenergia.com/"),
    "COMERCIALIZADORA DE REFERENCIA":               ("Mercado regulado", "regulated", "https://www.cnmc.es/sectores/energia"),
}


_LEGAL_SUFFIX_RE = re.compile(
    r"[,]?\s*(S\.?\s*L\.?\s*U?\.?|S\.?\s*A\.?\s*U?\.?|SLU|SAU|SL|SA|UNIPERSONAL)\.?\s*$",
    re.IGNORECASE,
)


def display_comercializadora(raw: str | None) -> str:
    info = _resolve(raw)
    if info:
        return info[0]
    return _fallback_name(raw)


def brand_tier(raw: str | None) -> str:
    info = _resolve(raw)
    return info[1] if info else "niche"


def brand_url(raw: str | None) -> str:
    info = _resolve(raw)
    if info:
        return info[2]
    label = display_comercializadora(raw)
    return f"https://www.google.com/search?q=cambiar+tarifa+luz+{label.replace(' ', '+')}"


def _resolve(raw: str | None) -> tuple[str, str, str] | None:
    if not raw:
        return None
    no_suffix = _LEGAL_SUFFIX_RE.sub("", raw).strip().strip(",").strip()
    key = no_suffix.upper().strip()
    if key in _BRAND_INFO:
        return _BRAND_INFO[key]
    for known_key, info in _BRAND_INFO.items():
        if known_key in key:
            return info
    return None


def _fallback_name(raw: str | None) -> str:
    if not raw:
        return "—"
    no_suffix = _LEGAL_SUFFIX_RE.sub("", raw).strip().strip(",").strip()
    return _title_es(no_suffix)


def _title_es(text: str) -> str:
    words = text.split()
    out: list[str] = []
    for word in words:
        stripped = word.strip(",.")
        if len(stripped) <= 4 and stripped.isupper():
            out.append(word)
        else:
            out.append(word.capitalize())
    return " ".join(out)
