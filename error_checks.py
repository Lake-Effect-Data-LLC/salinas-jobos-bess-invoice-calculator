import sys

def input_validation(facility_csv, plant_csv, inverter_csv, prev_inverter_csv, prev_days_csv, prev_output_csv):

    # checks if filenames in data folder have the correct names
    def filename_validation():
        if not facility_csv.exists():
            sys.exit(
                "Facility info input file not found. "
                f"Expected file at: {facility_csv}"
            )
        elif not plant_csv.exists():
            sys.exit(
                "Plant input file not found. "
                f"Expected file at: {plant_csv}"
            )
        elif not inverter_csv.exists():
            sys.exit(
                "Inverter input file not found. "
                f"Expected file at: {inverter_csv}"
            )
        elif not prev_inverter_csv.exists():
            sys.exit(
                "Previous Inverter State input file not found. "
                f"Expected file at: {prev_inverter_csv}"
            )
        elif not prev_days_csv.exists():
            sys.exit(
                "Previous days input file not found. "
                f"Expected file at: {prev_days_csv}"
            )
        elif not prev_output_csv.exists():
            sys.exit(
                "Previous days input file not found. "
                f"Expected file at: {prev_output_csv}"
            )
        return

    # run checks
    filename_validation()
    return