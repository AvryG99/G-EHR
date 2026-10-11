import re


def parse_sql_error(error_msg: str) -> dict:
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

    return {"type": "other", "message": error_msg}
