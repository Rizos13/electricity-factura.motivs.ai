from __future__ import annotations

from dataclasses import dataclass

from backend.app.tariff.constants import TariffConstants


@dataclass(frozen=True)
class OfferCost:
    monthly_potencia_eur: float
    monthly_energy_eur: float
    monthly_fixed_eur: float
    monthly_taxes_eur: float
    monthly_total_eur: float
    offer_effective_energy_eur_kwh: float


def estimate_offer_cost(
    importe_primera_factura_eur: float,
    user_potencia_kw: float,
    user_annual_kwh: float,
    tariff: TariffConstants,
    supplier_potencia_markup_factor: float = 0.0,
) -> OfferCost:
    eur_per_kwh = _derive_offer_eur_per_kwh(
        importe_primera_factura_eur,
        tariff,
        supplier_potencia_markup_factor,
    )
    return _cost_at_profile(
        user_potencia_kw,
        user_annual_kwh,
        eur_per_kwh,
        tariff,
        supplier_potencia_markup_factor,
    )


def _derive_offer_eur_per_kwh(
    importe: float,
    tariff: TariffConstants,
    pot_markup: float,
) -> float:
    ref_kwh_month = tariff.cnmc_ref_consumo_kwh_year / 12.0
    ref_potencia_month = _potencia_month(
        tariff.cnmc_ref_potencia_kw, tariff, pot_markup
    )
    base_with_ie_month = importe / (1.0 + tariff.iva_pct)
    base_without_meter = base_with_ie_month - tariff.alquiler_contador_eur_month
    subtotal_month = base_without_meter / (1.0 + tariff.impuesto_electricidad_pct)
    energy_subtotal_month = subtotal_month - ref_potencia_month
    if energy_subtotal_month <= 0 or ref_kwh_month <= 0:
        return 0.0
    return energy_subtotal_month / ref_kwh_month


def _cost_at_profile(
    user_kw: float,
    user_annual_kwh: float,
    eur_per_kwh: float,
    tariff: TariffConstants,
    pot_markup: float,
) -> OfferCost:
    potencia_month = _potencia_month(user_kw, tariff, pot_markup)
    energy_month = (user_annual_kwh / 12.0) * eur_per_kwh
    subtotal_month = potencia_month + energy_month
    ie_month = subtotal_month * tariff.impuesto_electricidad_pct
    fixed_month = tariff.alquiler_contador_eur_month
    base_iva = subtotal_month + ie_month + fixed_month
    iva_month = base_iva * tariff.iva_pct
    total_month = base_iva + iva_month
    taxes_month = ie_month + iva_month
    return OfferCost(
        monthly_potencia_eur=round(potencia_month, 2),
        monthly_energy_eur=round(energy_month, 2),
        monthly_fixed_eur=round(fixed_month, 2),
        monthly_taxes_eur=round(taxes_month, 2),
        monthly_total_eur=round(total_month, 2),
        offer_effective_energy_eur_kwh=round(eur_per_kwh, 5),
    )


def _potencia_month(kw: float, tariff: TariffConstants, markup: float) -> float:
    regulated_eur_kw_year = (
        tariff.regulated_potencia_p1_eur_kw_year
        + tariff.regulated_potencia_p2_eur_kw_year
    )
    eur_kw_year = regulated_eur_kw_year * (1.0 + markup)
    return kw * eur_kw_year / 12.0
