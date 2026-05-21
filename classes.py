from dataclasses import dataclass


@dataclass(frozen=True)
class BessContractValues:
    """Contract-defined values keyed by agreement year."""

    agreement_year: int
    cppf: float
    cpppif: float
    ddd: float
    source_reference: str = ""
    notes: str = ""


@dataclass(frozen=True)
class BessYearlyInputs:
    """Yearly inputs needed for Monthly Contract Capability."""

    agreement_year: int
    dde: float
    tr: float
    source_reference: str = ""
    notes: str = ""

@dataclass(frozen=True)
class BessMonthlyInputs:
    """Monthly inputs needed for ADJ, FA, FAA, and PRA calculations."""

    timestamp_month: str
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
