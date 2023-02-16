from datetime import datetime

def try_parsing_date(text):
    """Parse multiple date types or raise ValueError"""
    for fmt in ('%m/%d/%Y %H:%M:%S %p', '%m/%d/%y %H:%M'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError(f'{text} is not a valid datetime format')
