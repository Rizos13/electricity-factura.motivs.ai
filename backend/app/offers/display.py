from __future__ import annotations

import re


_BRAND_MAP = {
    "TOTALENERGIES CLIENTES": "TotalEnergies",
    "TOTALENERGIES MERCADO ESPAÑA": "TotalEnergies",
    "ENDESA ENERGÍA": "Endesa",
    "IBERDROLA CLIENTES": "Iberdrola",
    "NATURGY CLIENTES": "Naturgy",
    "REPSOL COMERCIALIZADORA DE ELECTRICIDAD Y GAS": "Repsol",
    "OCTOPUS ENERGY ESPAÑA": "Octopus Energy",
    "ENERGYA VM GESTION DE ENERGÍA": "Energya VM",
    "DOMESTICA GAS Y ELECTRICIDAD": "Doméstica",
    "IMAGINA ENERGIA": "Imagina Energía",
    "ENI PLENITUDE IBERIA": "Eni Plenitude",
    "ENERGIA NUFRI": "Energía Nufri",
    "FENIE ENERGIA": "Fenie Energía",
    "TELECOR": "Telecor",
    "DAIMUZ ENERGÍA": "Daimuz",
    "ENERGYASSET COMERCIALIZADORA DE ENERGÍA": "Energyasset",
    "GAOLANIA SERVICIOS": "Gaolania",
    "COMPAÑIA LUMISA ENERGIAS": "Lumisa Energías",
    "CATGAS ENERGIA": "Catgas Energía",
    "WEKIWI": "Wekiwi",
    "CIDE HCENERGÍA": "CIDE HC",
    "HIDROELECTRICA DE SILLEDA COMERCIALIZADORA": "Hidroeléctrica de Silleda",
    "DISA ENERGIA ELECTRICA": "DISA Energía",
    "INER ENERGIA CASTILLA LA MANCHA": "INER Castilla La Mancha",
    "INER EUSKADI": "INER Euskadi",
    "NEXUS ENERGIA": "Nexus Energía",
    "ENSTROGA": "Enstroga",
    "TRACTAMENT I SELECCIÓ DE RESIDUS": "TIRSA Energía",
    "ESCANDINAVA DE ELECTRICIDAD": "Escandinava de Electricidad",
    "NIBA": "niba",
    "COMERCIALIZADORA DE REFERENCIA": "Mercado regulado",
}


_LEGAL_SUFFIX_RE = re.compile(
    r"[,]?\s*(S\.?\s*L\.?\s*U?\.?|S\.?\s*A\.?\s*U?\.?|SLU|SAU|SL|SA|UNIPERSONAL)\.?\s*$",
    re.IGNORECASE,
)


def display_comercializadora(raw: str | None) -> str:
    if not raw:
        return "—"
    no_suffix = _LEGAL_SUFFIX_RE.sub("", raw).strip().strip(",").strip()
    key = no_suffix.upper().strip()
    if key in _BRAND_MAP:
        return _BRAND_MAP[key]
    for known_key, brand in _BRAND_MAP.items():
        if known_key in key:
            return brand
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
