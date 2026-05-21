from pathlib import Path

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

    print("BESS input files passed validation.")


if __name__ == "__main__":
    main()
