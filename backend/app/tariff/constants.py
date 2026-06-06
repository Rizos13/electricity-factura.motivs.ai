from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TariffConstants:
    label: str
    peajes_potencia_p1_eur_kw_year: float
    peajes_potencia_p2_eur_kw_year: float
    peajes_energia_p1_eur_kwh: float
    peajes_energia_p2_eur_kwh: float
    peajes_energia_p3_eur_kwh: float
    cargos_potencia_p1_eur_kw_year: float
    cargos_potencia_p2_eur_kw_year: float
    cargos_energia_p1_eur_kwh: float
    cargos_energia_p2_eur_kwh: float
    cargos_energia_p3_eur_kwh: float
    impuesto_electricidad_pct: float
    alquiler_contador_eur_month: float
    iva_pct: float
    cnmc_ref_potencia_kw: float
    cnmc_ref_consumo_kwh_year: float
    cnmc_ref_split_p1_p2_p3: tuple[float, float, float]

    @property
    def regulated_potencia_p1_eur_kw_year(self) -> float:
        return self.peajes_potencia_p1_eur_kw_year + self.cargos_potencia_p1_eur_kw_year

    @property
    def regulated_potencia_p2_eur_kw_year(self) -> float:
        return self.peajes_potencia_p2_eur_kw_year + self.cargos_potencia_p2_eur_kw_year

    @property
    def regulated_energia_p1_eur_kwh(self) -> float:
        return self.peajes_energia_p1_eur_kwh + self.cargos_energia_p1_eur_kwh

    @property
    def regulated_energia_p2_eur_kwh(self) -> float:
        return self.peajes_energia_p2_eur_kwh + self.cargos_energia_p2_eur_kwh

    @property
    def regulated_energia_p3_eur_kwh(self) -> float:
        return self.peajes_energia_p3_eur_kwh + self.cargos_energia_p3_eur_kwh


TARIFF_2_0TD_2026 = TariffConstants(
    label="2.0TD 2026",
    peajes_potencia_p1_eur_kw_year=22.988256,
    peajes_potencia_p2_eur_kw_year=0.539748,
    peajes_energia_p1_eur_kwh=0.027378,
    peajes_energia_p2_eur_kwh=0.020624,
    peajes_energia_p3_eur_kwh=0.000714,
    cargos_potencia_p1_eur_kw_year=7.202827,
    cargos_potencia_p2_eur_kw_year=0.270970,
    cargos_energia_p1_eur_kwh=0.009250,
    cargos_energia_p2_eur_kwh=0.006984,
    cargos_energia_p3_eur_kwh=0.002468,
    impuesto_electricidad_pct=0.0511,
    alquiler_contador_eur_month=0.81,
    iva_pct=0.21,
    cnmc_ref_potencia_kw=4.6,
    cnmc_ref_consumo_kwh_year=3500.0,
    cnmc_ref_split_p1_p2_p3=(0.20, 0.40, 0.40),
)
