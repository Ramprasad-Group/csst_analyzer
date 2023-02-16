from datetime import datetime

def try_parsing_date(text):
    """Parse multiple date types or raise ValueError"""
    # remove excess whitespace between words
    # text = " ".join(text.split()) 
    for fmt in ['%m/%d/%Y %I:%M:%S %p', '%m/%d/%y %H:%M']:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError(f'{text} is not a valid datetime format')
