from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BessContractValues:
    """Contract-defined values keyed by agreement year."""

    agreement_year: int
    cppf: float
    cpppif: float
    ddd: float
    ta: float = 0.70
    rer: float = 170.00
    ge: float = 0.97
    cld_uses_dde_multiplier: bool = False
    eld_uses_ce_times_ge: bool = True
    design_dmax: float = 0.0
    design_duration_energy: float = 0.0
    design_charge_energy: float = 0.0
    grid_system_waiting_period_hours: float = 80.0
    force_majeure_waiting_period_hours: float = 720.0
    scheduled_maintenance_allowance_hours: float = 160.0
    source_reference: str = ""
    notes: str = ""


@dataclass(frozen=True)
class BessYearlyInputs:
    """Yearly inputs needed for Monthly Contract Capability and capability LDs."""

    agreement_year: int
    dde: float
    tr: float
    gc: Optional[float] = None
    source_reference: str = ""
    notes: str = ""


@dataclass(frozen=True)
class BessMonthlyInputs:
    """Monthly inputs needed for ADJ, FA, FAA, and PRA calculations."""

    timestamp_month: str
    agreement_year: int
    adj: float
    bphrs: float
    pohrs: float
    unavhrs: float
    unavprodhrs: float
    gse: float
    pfm: float
    ip: float
    source_reference: str = ""
    notes: str = ""


@dataclass(frozen=True)
class BessPerformanceTest:
    """Section 6.9 performance test inputs used to derive MCC and guarantees."""

    test_id: str
    agreement_year: int
    test_type: str
    test_date: str
    requested_by: str
    tde: float
    measured_ramp_rate: float
    certified_by: str = ""
    prepa_approved: bool = False
    approval_date: str = ""
    cure_or_retest_date: str = ""
    replaces_test_id: str = ""
    source_reference: str = ""
    notes: str = ""


@dataclass(frozen=True)
class BessMonthlyPerformanceGuaranteeInputs:
    """Monthly metered inputs for Appendix P Efficiency Guarantee."""

    timestamp_month: str
    agreement_year: int
    ce: float
    de: float
    ae_beg: float
    ae_end: float
    source_reference: str = ""
    notes: str = ""


@dataclass(frozen=True)
class BessMonthlyResult:
    """Calculated monthly payment values for one billing month."""

    timestamp_month: str
    agreement_year: int
    cpp: float
    mcc: float
    fa: float
    faa: float
    pra: float
    mfp: float
    other_adj: float
    adj_total: float
    mp: float
    ald: float = 0.0
    cld: float = 0.0
    actual_efficiency: Optional[float] = None
    eld: float = 0.0

