from typing import Dict
import json
from datetime import datetime


def try_parsing_date(text):
    """Parse multiple date types or raise ValueError"""
    # remove excess whitespace between words
    # text = " ".join(text.split())
    for fmt in ["%m/%d/%Y %I:%M:%S %p", "%m/%d/%y %H:%M", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError(f"{text} is not a valid datetime format")


def json_dumps(data: Dict) -> str:
    """Generates json dumps string of data in a deterministic manner"""
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        indent=None,
        separators=(",", ":"),
    )


def remove_keys_with_null_values_in_dict(data: Dict) -> Dict:
    return {key: value for key, value in data.items() if value is not None}
