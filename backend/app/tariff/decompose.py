from __future__ import annotations

from dataclasses import dataclass

from backend.app.tariff.constants import TariffConstants


@dataclass(frozen=True)
class BillBreakdown:
    period_days: int
    monthly_potencia_eur: float
    monthly_energy_eur: float
    monthly_fixed_eur: float
    monthly_taxes_eur: float
    monthly_total_eur: float
    potencia_kw: float
    annual_kwh: float
    kwh_split_p1_p2_p3: tuple[float, float, float]
    regulated_potencia_eur_kw_year: float
    supplier_potencia_markup_eur_month: float
    effective_energy_eur_kwh: float


def decompose_bill(
    total_eur: float,
    period_days: int,
    potencia_kw: float,
    consumo_kwh_punta: float,
    consumo_kwh_llano: float,
    consumo_kwh_valle: float,
    tariff: TariffConstants,
) -> BillBreakdown:
    days = max(1, period_days)
    month_factor = 30.0 / days
    monthly_total = total_eur * month_factor

    kwh_total_period = max(0.0, consumo_kwh_punta + consumo_kwh_llano + consumo_kwh_valle)
    annual_kwh = kwh_total_period * (365.0 / days) if kwh_total_period > 0 else 0.0
    kwh_split = _safe_split(consumo_kwh_punta, consumo_kwh_llano, consumo_kwh_valle)

    regulated_pot_eur_year = (
        tariff.regulated_potencia_p1_eur_kw_year
        + tariff.regulated_potencia_p2_eur_kw_year
    )
    regulated_pot_eur_period = potencia_kw * regulated_pot_eur_year * (days / 365.0)

    monthly_fixed = tariff.alquiler_contador_eur_month
    fixed_period = monthly_fixed * (days / 30.0)

    subtotal_implied_period = total_eur / (1.0 + tariff.iva_pct) - fixed_period
    if subtotal_implied_period < 0:
        subtotal_implied_period = 0.0
    base_before_ie_period = subtotal_implied_period / (1.0 + tariff.impuesto_electricidad_pct)
    base_before_ie_period = max(0.0, base_before_ie_period)

    energy_share_period = max(0.0, base_before_ie_period - regulated_pot_eur_period)
    supplier_pot_markup_period = 0.0
    if energy_share_period == 0.0 and regulated_pot_eur_period > base_before_ie_period:
        supplier_pot_markup_period = 0.0
        regulated_pot_eur_period = base_before_ie_period

    kwh_period_eff = max(kwh_total_period, 1e-9)
    effective_energy_eur_kwh = energy_share_period / kwh_period_eff if kwh_total_period > 0 else 0.0

    taxes_period = total_eur - base_before_ie_period - fixed_period
    taxes_period = max(0.0, taxes_period)

    monthly_potencia = regulated_pot_eur_period * month_factor
    monthly_energy = energy_share_period * month_factor
    monthly_taxes = taxes_period * month_factor
    monthly_fixed_norm = fixed_period * month_factor

    return BillBreakdown(
        period_days=int(days),
        monthly_potencia_eur=round(monthly_potencia, 2),
        monthly_energy_eur=round(monthly_energy, 2),
        monthly_fixed_eur=round(monthly_fixed_norm, 2),
        monthly_taxes_eur=round(monthly_taxes, 2),
        monthly_total_eur=round(monthly_total, 2),
        potencia_kw=potencia_kw,
        annual_kwh=round(annual_kwh, 1),
        kwh_split_p1_p2_p3=kwh_split,
        regulated_potencia_eur_kw_year=regulated_pot_eur_year,
        supplier_potencia_markup_eur_month=round(supplier_pot_markup_period * month_factor, 2),
        effective_energy_eur_kwh=round(effective_energy_eur_kwh, 5),
    )


def _safe_split(p1: float, p2: float, p3: float) -> tuple[float, float, float]:
    total = p1 + p2 + p3
    if total <= 0:
        return (0.20, 0.40, 0.40)
    return (round(p1 / total, 4), round(p2 / total, 4), round(p3 / total, 4))
