from pathlib import Path

from compensation_calculator import calculate_monthly_results
from data_reader import load_bess_inputs
from data_writer import write_bess_monthly_results
from error_checks import input_validation


DATA_DIR = Path("data")


def main():
    contract_values_csv = DATA_DIR / "bess_contract_values_template.csv"
    yearly_inputs_csv = DATA_DIR / "bess_yearly_inputs_template.csv"
    monthly_inputs_csv = DATA_DIR / "bess_monthly_inputs_template.csv"

    input_validation(
        contract_values_csv,
        yearly_inputs_csv,
        monthly_inputs_csv,
    )

    contract_values, yearly_inputs, monthly_inputs = load_bess_inputs(
        contract_values_csv,
        yearly_inputs_csv,
        monthly_inputs_csv,
    )
    monthly_results = calculate_monthly_results(
        contract_values,
        yearly_inputs,
        monthly_inputs,
    )
    output_path = write_bess_monthly_results(monthly_results)

    print("BESS input files passed validation.")
    print(f"Wrote monthly results to {output_path}.")
    for result in monthly_results:
        print(
            f"{result.timestamp_month}: "
            f"agreement_year={result.agreement_year}, "
            f"MP=${result.mp:,.2f}"
        )


if __name__ == "__main__":
    main()
