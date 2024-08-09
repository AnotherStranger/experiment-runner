"""
This module contains helper functions
"""

import math
from typing import Optional

import psutil


def nan_safe_float(number: float) -> float:
    """
    Returns infinite if a given float is not a number otherwise it returns number
    """
    return float("inf") if math.isnan(number) else number


def safe_float_cast(number: str) -> float:
    """
    Cast a given string to float (NaN if not possible).
    """
    try:
        return float(number)
    except ValueError:
        return float("nan")


def get_user_for_pid(pid) -> Optional[str]:
    """
    Returns a process by its id

    Args:
    pid: process id

    Returns:
    psutil.Process: The user of the process
    """
    try:
        return str(psutil.Process(pid).username())
    except psutil.Error:
        return None
