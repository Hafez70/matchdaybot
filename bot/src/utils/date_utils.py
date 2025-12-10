"""Date utility functions"""
import jdatetime
from datetime import datetime


def to_persian_date(iso_datetime: str) -> str:
    """Convert ISO datetime to Persian date string"""
    try:
        dt = datetime.fromisoformat(iso_datetime)
        jdt = jdatetime.datetime.fromgregorian(datetime=dt)
        return jdt.strftime('%Y/%m/%d - %H:%M')
    except Exception:
        return iso_datetime

