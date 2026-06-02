GRID_SYSTEM_WAITING_PERIOD_HOURS = 80
FORCE_MAJEURE_WAITING_PERIOD_HOURS = 720

SCHEDULED_MAINTENANCE_ALLOWANCE_HOURS = 160

def calculate_included_hours(current_hours, prior_hours, annual_allowance_hours):
    if any(value < 0 for value in [current_hours, prior_hours, annual_allowance_hours]):
        raise ValueError("Hour values and annual allowances must be non-negative.")

    return min(current_hours, max(annual_allowance_hours - prior_hours, 0))


def calculate_included_GSEHRS(GSEHRS, prior_GSEHRS):
    return calculate_included_hours(
        GSEHRS,
        prior_GSEHRS,
        GRID_SYSTEM_WAITING_PERIOD_HOURS,
    )


def calculate_included_PFMHRS(PFMHRS, prior_PFMHRS):
    return calculate_included_hours(
        PFMHRS,
        prior_PFMHRS,
        FORCE_MAJEURE_WAITING_PERIOD_HOURS,
    )


def calculate_included_POHRS(POHRS, prior_POHRS):
    return calculate_included_hours(
        POHRS,
        prior_POHRS,
        SCHEDULED_MAINTENANCE_ALLOWANCE_HOURS,
    )



def calculate_FA_with_included_POHRS(currentPOHRS, prior_POHRS, BPHRS, UNAVHRS, UNAVPRODHRS):
    included_POHRS = calculate_included_POHRS(currentPOHRS, prior_POHRS)
    return calculate_FA(BPHRS, included_POHRS, UNAVHRS, UNAVPRODHRS)

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
    # FAA = 100% if FA >= 98%; 100% - [(98% - FA) x 2] if 70% < FA < 98%; 0% if FA < 70%.
    if FA >= 0.98:
        return 1.0
    if FA > 0.70:
        return 1.0 - ((0.98 - FA) * 2)
    return 0.0


def calculate_risk_adjustment_with_waiting_periods(BPHRS, GSEHRS, PFMHRS, IPHRS, prior_GSEHRS, prior_PFMHRS):
    
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

    included_GSEHRS = calculate_included_GSEHRS(GSEHRS, prior_GSEHRS)
    included_PFMHRS = calculate_included_PFMHRS(PFMHRS, prior_PFMHRS)

    adjustment = (BPHRS - (included_GSEHRS + included_PFMHRS + IPHRS)) / BPHRS

    return max(adjustment, 0)

# The function assumes prior_GSEHRS and prior_PFMHRS are year-to-date counted hours before this billing period. If those are raw prior event hours rather than prior included/capped hours, the result could be wrong.






def calculate_performance_test_mcc(DDE, DDD, TDE):

    if DDD <= 0:
        raise ValueError("DDD must be greater than zero.")

    if TDE < 0.99 * DDE:
        return TDE / DDD

    return DDE / DDD


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


def calculate_capability_liquidated_damages_per_day(GC, TDE, RER, CPP):
    # Source: Appendix P Section 2(b), Capability Liquidated Damages.
    # CLD = Capability Liquidated Damages per Day, expressed in dollars.
    # GC = Guaranteed Capability, expressed in MWh.
    # TDE = Tested Duration Energy, expressed in MWh.
    # RER = Replacement Energy Rate, expressed in $/MWh.
    # CPP = Capability Payment Price for the Agreement Year, expressed in $/MW-Month.
    if any(value < 0 for value in [GC, TDE, RER, CPP]):
        raise ValueError("CLD inputs must be non-negative.")

    capability_shortfall = max(GC - TDE, 0)
    return capability_shortfall * calculate_liquidated_damages_rate(RER, CPP)


def calculate_actual_efficiency(DE, CE, AE_beg, AE_end):
    # Source: Appendix P Section 3(b), Actual Efficiency.
    if CE <= 0:
        raise ValueError("CE must be greater than zero.")
    if any(value < 0 for value in [DE, AE_beg, AE_end]):
        raise ValueError("Actual Efficiency inputs must be non-negative.")

    return (DE + (AE_end - AE_beg)) / CE


def calculate_efficiency_liquidated_damages(RER, CPP, CE, GE, DE, actual_efficiency):
    # Source: Appendix P Section 3(c), Efficiency Liquidated Damages.
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

    energy_shortfall = max((CE * GE) - DE, 0)
    return calculate_liquidated_damages_rate(RER, CPP) * energy_shortfall
