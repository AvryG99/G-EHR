"""Schema inspection helpers backed by the canonical graph definition."""

from graph.tables import tables


def get_tables_like(name: str) -> list[str]:
    needle = name.lower()
    return sorted(table for table in tables if needle in table.lower())


def get_columns_like(name: str) -> list[dict[str, str]]:
    needle = name.lower()
    return [
        {"table_name": table_name, "column_name": column_name}
        for table_name, table_info in tables.items()
        for column_name in table_info["attributes"]
        if needle in column_name.lower()
    ]


def get_table_schema(table: str) -> list[dict[str, str]]:
    table_info = tables.get(table.lower())
    if not table_info:
        return []
    return [
        {"column_name": name, "data_type": info["datatype"]}
        for name, info in table_info["attributes"].items()
    ]
