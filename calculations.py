from datetime import datetime, time
from classes import InverterState
from itertools import islice


def is_last_interval_of_day(timestamp: datetime) -> bool:
    return timestamp.time() ==  time(23, 50, 0)  # Last 10-minute interval (23:50-00:00)

# Calculate the rolling 30 day Facility Availabliity per interval
def calculate_FA_rolling():
    pass
