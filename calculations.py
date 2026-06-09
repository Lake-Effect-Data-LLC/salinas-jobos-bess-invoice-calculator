GRID_SYSTEM_WAITING_PERIOD_HOURS = 80
FORCE_MAJEURE_WAITING_PERIOD_HOURS = 720

SCHEDULED_MAINTENANCE_ALLOWANCE_HOURS = 160

def calculate_included_hours(current_hours, prior_hours, annual_allowance_hours):
    if any(value < 0 for value in [current_hours, prior_hours, annual_allowance_hours]):
        raise ValueError("Hour values and annual allowances must be non-negative.")

    return min(current_hours, max(annual_allowance_hours - prior_hours, 0))


def calculate_included_GSEHRS(
    GSEHRS,
    prior_GSEHRS,
    annual_allowance_hours=GRID_SYSTEM_WAITING_PERIOD_HOURS,
):
    return calculate_included_hours(
        GSEHRS,
        prior_GSEHRS,
        annual_allowance_hours,
    )


def calculate_included_PFMHRS(
    PFMHRS,
    prior_PFMHRS,
    annual_allowance_hours=FORCE_MAJEURE_WAITING_PERIOD_HOURS,
):
    return calculate_included_hours(
        PFMHRS,
        prior_PFMHRS,
        annual_allowance_hours,
    )


def calculate_included_POHRS(
    POHRS,
    prior_POHRS,
    annual_allowance_hours=SCHEDULED_MAINTENANCE_ALLOWANCE_HOURS,
):
    return calculate_included_hours(
        POHRS,
        prior_POHRS,
        annual_allowance_hours,
    )



def calculate_FA_with_included_POHRS(
    currentPOHRS,
    prior_POHRS,
    BPHRS,
    UNAVHRS,
    UNAVPRODHRS,
    scheduled_maintenance_allowance_hours=SCHEDULED_MAINTENANCE_ALLOWANCE_HOURS,
):
    included_POHRS = calculate_included_POHRS(
        currentPOHRS,
        prior_POHRS,
        scheduled_maintenance_allowance_hours,
    )
    excess_POHRS = currentPOHRS - included_POHRS
    return calculate_FA(BPHRS, included_POHRS, UNAVHRS + excess_POHRS, UNAVPRODHRS)

def calculate_FA(BPHRS, POHRS, UNAVHRS, UNAVPRODHRS):
    # FAn = (BPHRSn - (POHRSn + UNAVHRSn + UNAVPRODHRSn))/(BPHRSn - POHRSn)
    # BPHRSn = total number of hours  for the Billing Period "n"
    # POHRSn = total number of permitted outage hours where the facility was unavailable to deliver Adjusted Duration Energy or unable to accept Charge Energy in the Billing Period
    # UNAVHRSn = total number of hours in which the Facility was unavailable to deliver Adjusted Duration Energy or unable to acdcept Charge Energy or unable to accept Charge Energy during the Billing Period
    # UNAVPRODHRSn = total number of hours in which the Facility was unable to provide Product other than energy due to an event that inhibits the Facility's ability to provide such other products but not its ability to deliver Energy

    # FAn = (BPHRSn - (POHRSn + UNAVHRSn + UNAVPRODHRSn)) / (BPHRSn - POHRSn)
    if BPHRS <= 0:
        raise ValueError("BPHRS must be greater than zero.")
    if any(value < 0 for value in [POHRS, UNAVHRS, UNAVPRODHRS]):
        raise ValueError("FA hour values must be non-negative.")
    if BPHRS - POHRS <= 0:
        raise ValueError("BPHRS minus POHRS must be greater than zero.")

    unavailable_hours = POHRS + UNAVHRS + UNAVPRODHRS
    if unavailable_hours > BPHRS:
        raise ValueError("Unavailable hours cannot exceed BPHRS.")

    return (BPHRS - unavailable_hours) / (BPHRS - POHRS)


def calculate_FAA(FA):
    # FAA = 100% if FA >= 98%; 100% - [(98% - FA) x 2] if 70% <= FA < 98%; 0% if FA < 70%.
    # The contract table leaves exactly 70% between rows; current interpretation
    # treats it as the last non-zero FAA point because the zero row says FA < 70%.
    if FA >= 0.98:
        return 1.0
    if FA >= 0.70:
        return 1.0 - ((0.98 - FA) * 2)
    return 0.0


def calculate_risk_adjustment_with_waiting_periods(
    BPHRS,
    GSEHRS,
    PFMHRS,
    IPHRS,
    prior_GSEHRS,
    prior_PFMHRS,
    grid_system_waiting_period_hours=GRID_SYSTEM_WAITING_PERIOD_HOURS,
    force_majeure_waiting_period_hours=FORCE_MAJEURE_WAITING_PERIOD_HOURS,
):
    
    # This function will calculate PRAi for billing period n based on the total number of hours for the Billing Period BPHRSn,the duration 
    # of a Grid System Event occurring in the Billing Period, provided that the number of GSEHRS in teh Billing Period when added to the number of GSEHRS in the preceding Billing Periods
    # shall not exceed the Grid System Waiting Period, and any excess GSEHRS shall not be included in the calculation of GSEHRSn
    # Duration of any Force Majeure affecting PREPA occurring in teh Billing Period, provided that the number of PFMHRS in the Billing Period when added to the number of PFMHRS in the preceding Billing Periods for the Year, shall not exceed
    # the Force Majeure Waiting Period, and any excess PFMHRS shall not be included in the calculation of PFMHRSn

    # PRAn = (BPHRSn - (GSEHRSn + PFMHRSn + IPHRSn)) / BPHRSn

    # IPHRSn duration of any event any event during the Billing Period in respect of which Resrouce Provider may recover insurance proceeds from any insurance policy that Resource Provider obtains in respect of PREPA Risk Events
    # PRAi = (BPn - (GSEHRSn + PFMHRSn + IPHRSn)) / BPn
    # PRAn = PREPA Risk Adjustment for the Billing Period; 
    # BPHRSn = total number of hours for the Billing Period;
    # GSEHRSn = the duration (in hours) of any Grid System Event (other than a Force
    # Majeure affecting PREPA) occurring in the Billing Period,
    # provided that the number of GSEHRS in the Billing Period when
    # added to the number of GSEHRS in the preceding Billing Periods
    # for the Year, shall not exceed the Grid System Waiting Period, and
    # any such excess GSEHRS shall not be included in the calculation
    # of GSEHRSn;
    # PFMHRSn = duration (in hours) of any Force Majeure affecting PREPA
    # occurring in the Billing Period, provided that the number of
    # PFMHRS in the Billing Period when added to the number of
    # PFMHRS in the preceding Billing Periods for the Year, shall not

    if BPHRS <= 0:
        raise ValueError("BPHRS must be greater than zero.")

    inputs = [
        GSEHRS,
        PFMHRS,
        IPHRS,
        prior_GSEHRS,
        prior_PFMHRS 
        ]

    if any(value < 0 for value in inputs):
        raise ValueError("Hour values and waiting periods must be non-negative.")

    included_GSEHRS = calculate_included_GSEHRS(
        GSEHRS,
        prior_GSEHRS,
        grid_system_waiting_period_hours,
    )
    included_PFMHRS = calculate_included_PFMHRS(
        PFMHRS,
        prior_PFMHRS,
        force_majeure_waiting_period_hours,
    )

    adjustment = (BPHRS - (included_GSEHRS + included_PFMHRS + IPHRS)) / BPHRS

    return max(adjustment, 0)







def calculate_performance_test_mcc(DDE, DDD, TDE):

    if DDD <= 0:
        raise ValueError("DDD must be greater than zero.")

    if TDE < 0.99 * DDE:
        return TDE / DDD

    return DDE / DDD


def calculate_degraded_duration_energy(
    design_duration_energy,
    annual_duration_energy_degradation_rate,
    agreement_year,
):
    # Source: DDE definition and Appendix J degradation schedule.
    # DDE equals Design Duration Energy adjusted by the Agreement Year's
    # duration-energy degradation rate. Qualifying upgrade/test upward
    # adjustments are still handled as input overrides, capped by contract.
    if design_duration_energy < 0:
        raise ValueError("Design Duration Energy must be non-negative.")
    if annual_duration_energy_degradation_rate < 0:
        raise ValueError("Annual Duration Energy Degradation Rate must be non-negative.")
    if agreement_year < 1:
        raise ValueError("Agreement Year must be at least 1.")

    degradation_factor = 1 - annual_duration_energy_degradation_rate
    if degradation_factor < 0:
        raise ValueError(
            "Annual Duration Energy Degradation Rate cannot exceed 100%."
        )

    return design_duration_energy * (degradation_factor ** (agreement_year - 1))


def calculate_annual_mcc(DDE, DDD, TR):
    # This function will calculate the Monthly Contract Capability (MCC) for each month in the billing period based on the agreement year, DDE, and TR.
    #MCCy = min[DDE/DDD,TR]
    #MCCy is the adjusted MCC for the agreement yewar
    #DDE is the Degraded Duration Energy for the Agreement Year
    #DDD is the Design Dmax Duration 
    #TR is the Tested Result, i.e, the MCC as adjusted to the most recent Peformance Test

    if DDD <= 0:
        raise ValueError("DDD must be greater than zero.")

    return min(DDE / DDD, TR)


def calculate_capabability_payment_price(cppf: float, cpppif: float) -> float:
    # This function will calculate the Capability Payment Price (CPP) for each month in the billing period based on the agreement year, CPPF, CPPPIF, CPP = CPPF + CPPPIF
    return cppf + cpppif

def calculate_monthly_fixed_payment(CPP, MCC, FAA, PRA):
    # MFPn = CPP x MCCn x FAAn x PRAn
    return CPP * MCC * FAA * PRA

def calculate_monthly_payment(MFP, ADJ):
    # MPn = MFPn - ADJn
    return MFP - ADJ

def calculate_liquidated_damages_rate(RER, CPP):
    # Source: Appendix P Sections 1-3.
    return RER - (CPP / (30.33 * 24))


def calculate_availability_liquidated_damages(TA, FA, DDE, RER, CPP):
    # Source: Appendix P Section 1(b), Availability Liquidated Damages.
    # ALD = Availability Liquidated Damages, expressed in dollars.
    # TA = Threshold Availability, expressed as a percentage.
    # FA = Facility Availability for the Billing Period, expressed as a percentage.
    # DDE = Degraded Duration Energy for the Agreement Year, expressed in MWh.
    # RER = Replacement Energy Rate, expressed in $/MWh.
    # CPP = Capability Payment Price for the Agreement Year, expressed in $/MW-Month.
    if any(value < 0 for value in [TA, FA, DDE, RER, CPP]):
        raise ValueError("ALD inputs must be non-negative.")

    availability_shortfall = max(TA - FA, 0)
    return availability_shortfall * DDE * calculate_liquidated_damages_rate(RER, CPP)


def calculate_capability_liquidated_damages_per_day(
    GC,
    TDE,
    RER,
    CPP,
    DDE=None,
):
    # Source: Appendix P Section 2(b), Capability Liquidated Damages.
    # Salinas visual source: docs/screenshots/CLD_06_Amend_(C-2-E)AES_Salinas_2023-0005_pg_230_220.png.
    # Jobos visual source provided in chat confirms no DDE multiplier in its CLD formula.
    # CLD = Capability Liquidated Damages per Day, expressed in dollars.
    # GC = Guaranteed Capability, expressed in MWh.
    # TDE = Tested Duration Energy, expressed in MWh.
    # RER = Replacement Energy Rate, expressed in $/MWh.
    # CPP = Capability Payment Price for the Agreement Year, expressed in $/MW-Month.
    # DDE = optional Salinas multiplier, expressed in MWh.
    inputs = [GC, TDE, RER, CPP]
    if DDE is not None:
        inputs.append(DDE)

    if any(value < 0 for value in inputs):
        raise ValueError("CLD inputs must be non-negative.")

    capability_shortfall = max(GC - TDE, 0)
    dde_multiplier = DDE if DDE is not None else 1.0
    return capability_shortfall * dde_multiplier * calculate_liquidated_damages_rate(
        RER,
        CPP,
    )


def calculate_actual_efficiency(DE, CE, AE_beg, AE_end):
    # Source: Appendix P Section 3(b), Actual Efficiency.
    if CE <= 0:
        raise ValueError("CE must be greater than zero.")
    if any(value < 0 for value in [DE, AE_beg, AE_end]):
        raise ValueError("Actual Efficiency inputs must be non-negative.")

    return (DE + (AE_end - AE_beg)) / CE


def calculate_efficiency_liquidated_damages(
    RER,
    CPP,
    CE,
    GE,
    DE,
    actual_efficiency,
    uses_ce_times_ge=True,
):
    # Source: Appendix P Section 3(c), Efficiency Liquidated Damages.
    # Salinas visual source: docs/screenshots/ELD_AES_Salinas_2023-00053_Pg_231_Pg_221.png.
    # Jobos visual source provided in chat confirms the CE x GE formula.
    # ELD = Efficiency Liquidated Damages, expressed in dollars.
    # CE = Charge Energy for the Billing Period, expressed in MWh.
    # GE = Guaranteed Efficiency, expressed as its decimal equivalent.
    # DE = Discharge Energy for the Billing Period, expressed in MWh.
    # RER = Replacement Energy Rate, expressed in $/MWh.
    # CPP = Capability Payment Price for the Agreement Year, expressed in $/MW-Month.
    if any(value < 0 for value in [RER, CPP, CE, GE, DE, actual_efficiency]):
        raise ValueError("ELD inputs must be non-negative.")

    if actual_efficiency >= GE:
        return 0.0

    if uses_ce_times_ge:
        energy_shortfall = (CE * GE) - DE
    else:
        energy_shortfall = (CE - GE) - DE

    energy_shortfall = max(energy_shortfall, 0)
    return calculate_liquidated_damages_rate(RER, CPP) * energy_shortfall
