import sys

def input_validation(contract_values_csv, yearly_inputs_csv, monthly_inputs_csv):
    if not contract_values_csv.exists():
        sys.exit(
            "BESS contract values input file not found. "
            f"Expected file at: {contract_values_csv}"
        )
    elif not yearly_inputs_csv.exists():
        sys.exit(
            "BESS yearly inputs file not found. "
            f"Expected file at: {yearly_inputs_csv}"
        )
    elif not monthly_inputs_csv.exists():
        sys.exit(
            "BESS monthly inputs file not found. "
            f"Expected file at: {monthly_inputs_csv}"
        )
        
    # run checks
    filename_validation()
    returns
    filename_validation()
    returns
    filename_validation()
    return