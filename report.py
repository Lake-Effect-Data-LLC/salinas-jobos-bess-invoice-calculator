from pathlib import Path
from datetime import datetime
import os

DATA_DIR = Path("data")

def format_currency(amount):
    """Format a number as USD currency, normalize -0.00"""
    if abs(amount) < 0.005:
        amount = 0.0
    return f"${amount:,.2f}"


def format_energy(kwh):
    """Format energy in kWh with thousands separator, normalize -0.00"""
    if abs(kwh) < 0.005:
        kwh = 0.0
    return f"{kwh:,.2f} kWh"


def format_percentage(value):
    """Format a decimal as percentage, normalize -0.00"""
    if abs(value) < 0.00005:
        value = 0.0
    return f"{value * 100:.2f}%"


def generate_report(facility_info, billing_data, calculations, start_date, end_date):
    """Generate a formatted monthly payment report per PPOA"""

    report = []
    report.append("=" * 80)
    report.append("MONTHLY PAYMENT REPORT")
    report.append("=" * 80)
    report.append("")

    # Facility Information
    report.append("FACILITY INFORMATION")
    report.append("-" * 80)
    report.append(f"Facility:             Jobos Solar (Clean Flexible Energy LLC)")
    report.append(f"Maximum Dispatch Limit: {facility_info.maximum_dispatch_limit_mw * 1000:,.0f} kW")
    report.append(f"Number of Inverters:  {facility_info.num_inverters}")
    report.append(f"Commercial Op Date:   {facility_info.commercial_operation_date.strftime('%Y-%m-%d')}")
    report.append(f"P50 Energy Yield:     {facility_info.P50_energy_yield:,.2f} kWh (current Agreement Year)")
    report.append("")

    # Billing Period Information
    report.append("BILLING PERIOD")
    report.append("-" * 80)
    report.append(f"Period:               {billing_data.period_id}")
    report.append(f"Start Date:           {start_date.strftime('%Y-%m-%d')}")
    report.append(f"End Date:             {end_date.strftime('%Y-%m-%d')}")
    report.append(f"Days in Period:       {(end_date - start_date).days + 1}")
    report.append("")

    # Energy Calculations
    report.append("ENERGY PRODUCTION & AVAILABILITY")
    report.append("-" * 80)
    report.append(f"Actual NEO (NEO_n):              {format_energy(calculations['NEO_n'])}")
    report.append(f"Expected NEO (ENEO_n):           {format_energy(calculations['ENEO_n'])}")
    report.append(f"Facility Availability (FA):      {format_percentage(calculations['FA'])}")
    report.append(f"Deemed NEO (DNEO_n):             {format_energy(calculations['DNEO_n'])}")
    report.append(f"Total Billable Energy:           {format_energy(calculations['NEO_n'] + calculations['DNEO_n'])}")
    report.append("")

    # Contract Rate Breakdown
    # Per Appendix F Section 2(b): Base Rate up to 110% of P50, then 80% BR for excess
    report.append("CONTRACT RATE DETERMINATION")
    report.append("-" * 80)
    p50_110_threshold = facility_info.P50_energy_yield * 1.10
    total_billable = calculations['NEO_n'] + calculations['DNEO_n']
    report.append(f"P50 Energy Yield (current yr):   {format_energy(facility_info.P50_energy_yield)}")
    report.append(f"110% of P50 Threshold:           {format_energy(p50_110_threshold)}")
    report.append(f"  Qty at Base Rate (<= 110% P50): {format_energy(min(total_billable, p50_110_threshold))}")
    if total_billable > p50_110_threshold:
        report.append(f"  Qty at 80% Base Rate (excess):  {format_energy(total_billable - p50_110_threshold)}")
    report.append(f"Base Rate (BR):                  ${calculations['BR']:.5f}/kWh")
    report.append(f"Effective Contract Rate (CR_n):  ${calculations['CR_n']:.5f}/kWh")
    report.append("")

    # Financial Calculations
    report.append("PAYMENT CALCULATION  (MP = ((NEO + DNEO) x CR) - OC)")
    report.append("-" * 80)
    energy_revenue = (calculations['NEO_n'] + calculations['DNEO_n']) * calculations['CR_n']
    oc = billing_data.other_credits
    report.append(f"Energy Revenue:                  {format_currency(energy_revenue)}")
    report.append(f"  ({format_energy(total_billable)}) x ${calculations['CR_n']:.5f}/kWh")
    report.append("")
    report.append(f"Other Credits / Deductions (OC): {format_currency(oc)}")
    report.append("")
    report.append("=" * 80)
    report.append(f"MONTHLY PAYMENT (MP):            {format_currency(calculations['MP'])}")
    report.append("=" * 80)
    report.append("")

    # Formula Summary
    report.append("CALCULATION FORMULA:")
    report.append("-" * 80)
    report.append("MP = ((NEO_n + DNEO_n) x CR_n) - OC_n")
    report.append("")
    report.append(f"MP = (({calculations['NEO_n']:,.2f} + {calculations['DNEO_n']:,.2f}) x {calculations['CR_n']:.5f})")
    report.append(f"     - {oc:,.2f}")
    report.append(f"   = {format_currency(calculations['MP'])}")
    report.append("")

    # Performance Guarantee / Shortfall Credits (Appendix Q)
    report.append("PERFORMANCE GUARANTEE")
    report.append("-" * 80)
    report.append("Guarantee: Facility must deliver >= 90% of P50 Energy Yield over each")
    report.append("           2-consecutive-Agreement-Year Rolling Period.")
    if 'shortfall_credits' in calculations and calculations['shortfall_credits'] > 0:
        sc = calculations['shortfall_credits']
        report.append(f"Shortfall Credit (SC) Applied:   {format_currency(sc)}")
        report.append(f"  SC = (RER - BR) x EQS")
        report.append(f"  RER (Replacement Energy Rate):  $0.17000/kWh")
        report.append(f"  BR:                             ${calculations['BR']:.5f}/kWh")
    else:
        report.append("Shortfall Credit (SC):           $0.00  (no shortfall in current Rolling Period)")
    report.append("")

    # Footer
    report.append("-" * 80)
    report.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)

    return "\n".join(report)


def save_report(report_text, output_file):
    """Save report to a text file"""
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_file)

    with open(output_path, 'w') as f:
        f.write(report_text)
    print(f"Report saved to {output_path}")