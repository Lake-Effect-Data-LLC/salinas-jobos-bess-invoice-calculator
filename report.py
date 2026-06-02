from datetime import datetime

import pandas as pd


def format_currency(value):
    if pd.isna(value):
        return "N/A"

    return f"${value:,.2f}"


def format_percentage(value):
    if pd.isna(value):
        return "N/A"

    return f"{value * 100:.2f}%"


def generate_bess_invoice_support_report(results_df, output_file):
    """Generate a Section 10.1-style BESS invoice support report."""

    lines = []
    lines.append("=" * 88)
    lines.append("SALINAS AND JOBOS BESS MONTHLY INVOICE SUPPORT REPORT")
    lines.append("=" * 88)
    lines.append("Source: Section 10.1 Payment & Billings invoice-content requirements")
    lines.append(f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}")
    lines.append("")

    for row in results_df.itertuples(index=False):
        lines.append("-" * 88)
        lines.append(
            f"Billing Period: {row.timestamp_month}    "
            f"Agreement Year: {row.agreement_year}"
        )
        lines.append("-" * 88)
        lines.append("")

        lines.append("Monthly Fixed Payment")
        lines.append(f"  CPP:  {format_currency(row.CPP)}")
        lines.append(f"  MCC:  {row.MCC:,.6f} MW")
        lines.append(f"  FA:   {format_percentage(row.FA)}")
        lines.append(f"  FAA:  {format_percentage(row.FAA)}")
        lines.append(f"  PRA:  {format_percentage(row.PRA)}")
        lines.append(f"  MFP:  {format_currency(row.MFP)}")
        lines.append("")

        lines.append("Other Payment Adjustments / Credits Owing to PREPA")
        lines.append(f"  Other_ADJ: {format_currency(row.Other_ADJ)}")
        lines.append(f"  ALD:       {format_currency(row.ALD)}")
        lines.append(
            f"  Actual Efficiency: "
            f"{format_percentage(getattr(row, 'Actual_Efficiency'))}"
        )
        lines.append(f"  ELD:       {format_currency(row.ELD)}")
        lines.append(f"  ADJ_Total: {format_currency(row.ADJ_Total)}")
        lines.append("")

        lines.append("Monthly Payment")
        lines.append("  MP = MFP - ADJ_Total")
        lines.append(f"  MP: {format_currency(row.MP)}")
        lines.append("")

        lines.append("Not Yet Populated / Itemized Separately")
        lines.append(
            "  Discharge Energy and Charge Energy detail: "
            "see monthly performance input file"
        )
        lines.append("  Ancillary Services: not provided in current input files")
        lines.append("  Green Credits: not provided in current input files")
        lines.append("  Balance: not provided in current input files")
        lines.append("  Insurance payments: not provided in current input files")
        lines.append("  CLD total: not allocated across Billing Periods yet")
        lines.append("")

    lines.append("=" * 88)
    lines.append("End of report")

    report_text = "\n".join(lines)
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(report_text)

    return report_text
