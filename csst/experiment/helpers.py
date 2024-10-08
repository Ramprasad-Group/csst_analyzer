from typing import Dict
import json
from datetime import datetime


def try_parsing_date(text):
    """Parse multiple date types or raise ValueError"""
    # remove excess whitespace between words
    valid_formats = [
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M %p",
        "%m/%d/%Y %H:%M",
    ]
    for fmt in valid_formats:
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


def make_name_searchable(name: str) -> str:
    """Runs regex over the name to parse hard to match characters"""
    search_name = name.strip()
    search_name = name.lower()
    search_name = search_name.translate({ord(i): None for i in ":{}- ()[],‐'\""})
    return search_name
