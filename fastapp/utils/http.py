def is_http_status_code_error(status_code):
    try:
        status_code = int(status_code)
    except ValueError:
        return True
    
    if not (200 <= status_code <= 299 or 300 <= status_code <= 399):
        return True
    else:
        return False