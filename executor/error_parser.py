import re


def parse_sql_error(error_msg: str) -> dict:
    if "exceeding the configured limit" in error_msg or "maximum bytes billed" in error_msg.lower():
        return {"type": "scan_budget", "message": error_msg}
    if "Unexpected token" in error_msg or "Syntax error" in error_msg or "Invalid expression" in error_msg:
        return {"type": "syntax", "message": error_msg}
    m = re.search(r"Unknown column '(.+?)'", error_msg)
    if m:
        return {"type": "unknown_column", "name": m.group(1)}

    m = re.search(r"Table '.+?\.(.+?)' doesn't exist", error_msg)
    if m:
        return {"type": "unknown_table", "name": m.group(1)}

    m = re.search(r"Unrecognized name: ([\w.]+)", error_msg)
    if m:
        return {"type": "unknown_column", "name": m.group(1).split(".")[-1]}

    m = re.search(r"Table not found: (?:[\w-]+\.)*([\w-]+)", error_msg)
    if m:
        return {"type": "unknown_table", "name": m.group(1)}

    m = re.search(r"Not found: Table [^: ]+:([\w]+)\.([\w]+)", error_msg)
    if m:
        return {"type": "unknown_table", "name": m.group(2)}

    return {"type": "other", "message": error_msg}
