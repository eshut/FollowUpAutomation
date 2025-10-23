"""Framework: https://github.com/eshut/Framework-Python"""

import time
import random
from framework_inject.constants import DEFAULT_WAIT_TIME_SEC


def wait_time(sec=DEFAULT_WAIT_TIME_SEC):
    time.sleep(sec)


def wait_random_time(min_time=1, max_time=1):
    if min_time < 0 or max_time < 0:
        raise ValueError("Time values must be non-negative.")
    if min_time > max_time:
        raise ValueError("min_time must not be greater than max_time.")

    wait_time = random.uniform(min_time, max_time)
    time.sleep(wait_time)
    return wait_time


def get_current_time_sec():
    """Returns the current time in seconds since the epoch."""
    return time.time()


def has_minutes_passed(start_time, minutes):
    """Checks if a certain number of minutes have passed since start_time."""
    elapsed_time = time.time() - start_time
    return elapsed_time >= minutes * 60

