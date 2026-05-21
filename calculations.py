from datetime import datetime, time
from classes import InverterState
from itertools import islice


def is_last_interval_of_day(timestamp: datetime) -> bool:
    return timestamp.time() ==  time(23, 50, 0)  # Last 10-minute interval (23:50-00:00)


def calculate_FA(BPHRS, POHRS, UNAVHRS, UNAVPRODHRS):
    #FAn = (BPHRSn - (POHRSn + UNAVHRSn + UNAVPRODHRSn))/(BPHRSn - POHRSn)
    # BPHRSn = total number of hours  for the Billing Period "n"
    # POHRSn = total number of permitted outage hours where the facility was unavailable to deliver Adjusted Duration Energy or unable to accept Charge Energy in the Billing Period
    # UNAVHRSn = total number of hours in which the Facility was unavailable to deliver Adjusted Duration Energy or unable to acdcept Charge Energy or unable to accept Charge Energy during the Billing Period
    # UNAVPRODHRSn = total number of hours in which the Facility was unable to provide Product other than energy due to an event that inhibits the Facility's ability to provide such other products but not its ability to deliver Energy

    # FAn = (BPHRSn - (POHRSn + UNAVHRSn + UNAVPRODHRSn)) / (BPHRSn - POHRSn)
    if BPHRS <= 0:
        raise ValueError("BPHRS must be greater than zero.")
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


def simple_calculate_risk_adjustment(BPHRS, GSEHRS, PFMHRS, IPHRS):
    # PRAn = (BPHRSn - (GSEHRSn + PFMHRSn + IPHRSn)) / BPHRSn
    if BPHRS <= 0:
        raise ValueError("BPHRS must be greater than zero.")

    return (BPHRS - (GSEHRS + PFMHRS + IPHRS)) / BPHRS


def calculate_risk_adjustment_with_waiting_periods(
    BPHRS,
    GSEHRS,
    PFMHRS,
    IPHRS,
    prior_GSEHRS,
    prior_PFMHRS,
    GSE_waiting_period,
    PFM_waiting_period,
):
    
    # This function will calculate PRAi for billing period n based on the total number of hours for the Billing Period BPHRSn,the duration 
    # of a Grid System Event occurring in the Billing Period, provided that the number of GSEHRS in teh Billing Period when added to the number of GSEHRS in the preceding Billing Periods
    # shall not exceed the Grid System Waiting Period, and any excess GSEHRS shall not be included in the calculation of GSEHRSn
    #Duration of any Force Majeure affecting PREPA occurring in teh Billing Period, provided that the number of PFMHRS in the Billing Period when added to the number of PFMHRS in the preceding Billing Periods for the Year, shall not exceed
    # the Force Majeure Waiting Period, and any excess PFMHRS shall not be included in the calculation of PFMHRSn

    # PRAn = (BPHRSn - (GSEHRSn + PFMHRSn + IPHRSn)) / BPHRSn

    # IPHRSn duration of any event any event during the Billing Period in respect of which Resrouce Provider may recover insurance proceeds from any insurance policy that Resource Provider obtains in respect of PREPA Risk Events
    #PRAi = (BPn - (GSEHRSn + PFMHRSn + IPHRSn)) / BPn
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

    GSEHRS = min(GSEHRS, max(GSE_waiting_period - prior_GSEHRS, 0))
    PFMHRS = min(PFMHRS, max(PFM_waiting_period - prior_PFMHRS, 0))

    return (BPHRS - (GSEHRS + PFMHRS + IPHRS)) / BPHRS


#The date/effective-period rule should live outside this formula later: first choose which performance test applies to the billing period, then pass that test’s TDE into this function.

def calculate_monthly_contract_capability(DDE, DDD, TDE=None):
    # This function will calculate the Monthly Contract Capability (MCC) for each month in the billing period based on the agreement year, DDE, and TR.
    # MCCy = min[DDE/DDD,TR]
    #MCCy is the adjusted MCC for the agreement yewar
    #DDE is the Degraded Duration Energy for the Agreement Year
    #DDD is the Design Dmax Duration 
    #TR is the Tested Result, i.e, the MCC as adjusted to the most recent Peformance Test
        if TDE is not None and TDE < (0.99 * DDE):
            return TDE / DDD

        return DDE / DDD


def calculate_capabability_payment_price(cppf: float, cpppif: float) -> float:
    # This function will calculate the Capability Payment Price (CPP) for each month in the billing period based on the agreement year, CPPF, CPPPIF, CPP = CPPF + CPPPIF
    return cppf + cpppif

def calculate_monthly_fixed_payment(CPP, MCC, FAA, PRA):
    # MFPn = CPP x MCCn x FAAn x PRAn
        return CPP * MCC * FAA * PRA


def calculate_monthly_payment(MFP, ADJ):
    # MPn = MFPn - ADJn
    return MFP - ADJ


