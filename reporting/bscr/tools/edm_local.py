"""Local, read-only replay workflow for BSCR EDM exports.

The workflow is deliberately split into three commands::

    uv run --with duckdb --with sqlglot python edm_local.py import \
        --input export-directory --database edm.duckdb
    uv run --with duckdb --with sqlglot python edm_local.py query \
        --database edm.duckdb --sql "SELECT * FROM accgrp"
    uv run --with duckdb --with sqlglot python edm_local.py replay \
        --database edm.duckdb --query ../sql/bscr-output.sql \
        --output bscr-output.csv [--fx 1.35] [--entity HIG]

``import`` requires the six CSV files produced by the BSCR raw exporter and
creates a new DuckDB database.  ``query`` accepts one local SELECT statement
and writes RFC4180 CSV to stdout.  ``replay`` adapts the SQL Server script to
DuckDB, executes it read-only, and writes a CSV plus an adjacent provenance
JSON file.  The adapter is a local analysis aid; it is not certification of
SQL Server equivalence.

This module intentionally has no project dependency.  Install its two runtime
packages for a run with ``uv --with duckdb --with sqlglot``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, TextIO


TABLES = ("accgrp", "policy", "loc", "loccvg")
DATA_FILES = ("accgrp.csv", "policy.csv", "loc.csv", "loccvg.csv")
MANIFEST_COLUMNS = (
    "export_run_id",
    "source_server",
    "source_database",
    "export_started_utc",
    "isolation_mode",
    "table_name",
    "row_count",
    "scope",
)
SCHEMA_COLUMNS = (
    "table_name",
    "column_name",
    "data_type",
    "precision",
    "scale",
    "is_nullable",
)
REQUIRED_COLUMNS = {
    "accgrp": ("accgrpid", "userid1", "branchname", "uwritrname"),
    "policy": (
        "policyid",
        "accgrpid",
        "policytype",
        "partof",
        "blanlimamt",
        "undcovamt",
        "blandedamt",
    ),
    "loc": (
        "locid",
        "accgrpid",
        "locnum",
        "addrmatch",
        "state",
        "cntrycode",
        "country",
        "latitude",
        "longitude",
    ),
    "loccvg": (
        "locid",
        "peril",
        "deductamt",
        "deductcur",
        "valueamt",
        "valuecur",
        "limitamt",
        "limitcur",
    ),
}


class LocalError(Exception):
    """An expected input, SQL, or output error."""


@dataclass
class CsvData:
    headers: list[str]
    rows: list[list[str | None]]
    sha256: str
    path: Path
    row_count: int
    run_ids: set[str | None]


@dataclass
class SourceColumn:
    table: str
    name: str
    data_type: str
    precision: int | None
    scale: int | None
    nullable: str


@dataclass
class ImportSet:
    manifest: list[dict[str, str]]
    schema: list[SourceColumn]
    data: dict[str, CsvData]
    run_id: str
    manifest_sha256: str
    schema_sha256: str


def _require_duckdb() -> Any:
    try:
        import duckdb  # type: ignore
    except ImportError as exc:
        raise LocalError(
            "duckdb is required; run with uv --with duckdb --with sqlglot"
        ) from exc
    return duckdb


def _require_sqlglot() -> Any:
    try:
        import sqlglot  # type: ignore
        from sqlglot import exp  # type: ignore
    except ImportError as exc:
        raise LocalError(
            "sqlglot is required; run with uv --with duckdb --with sqlglot"
        ) from exc
    return sqlglot, exp


def _qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _casefold_map(values: Iterable[str], what: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key = value.casefold()
        if key in result:
            raise LocalError(f"{what} has duplicate column names: {value!r}")
        result[key] = value
    return result


def _read_csv(
    path: Path, *, expected_header: tuple[str, ...] | None = None, keep_rows: bool = True
) -> CsvData:
    if not path.is_file():
        raise LocalError(f"missing input file: {path}")
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    rows: list[list[str | None]] = []
    run_ids: set[str | None] = set()
    row_count = 0
    try:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, strict=True)
            headers = next(reader, None)
            if not headers or any(header == "" for header in headers):
                raise LocalError(f"{path.name} is empty or has an empty header")
            _casefold_map(headers, f"{path.name} header")
            if expected_header is not None and tuple(headers) != expected_header:
                raise LocalError(f"{path.name} header must be {list(expected_header)!r}; got {headers!r}")
            for line_number, row in enumerate(reader, 2):
                if len(row) != len(headers):
                    raise LocalError(
                        f"{path.name} line {line_number} has {len(row)} fields; expected {len(headers)}"
                    )
                row_count += 1
                if keep_rows:
                    rows.append([None if value == r"\N" else value for value in row])
                else:
                    run_ids.add(None if row[0] == r"\N" else row[0])
    except (UnicodeDecodeError, csv.Error) as exc:
        raise LocalError(f"invalid UTF-8 CSV in {path.name}: {exc}") from exc
    return CsvData(headers, rows, digest, path, row_count, run_ids)


def _nonempty(value: str | None, field: str) -> str:
    if value is None or value == "":
        raise LocalError(f"manifest/schema field {field} cannot be empty")
    return value


def _parse_optional_int(value: str | None, field: str) -> int | None:
    if value is None or value == "":
        return None
    if not re.fullmatch(r"[0-9]+", value):
        raise LocalError(f"{field} must be a non-negative integer, got {value!r}")
    return int(value)


def _parse_import_set(input_dir: Path) -> ImportSet:
    if not input_dir.is_dir():
        raise LocalError(f"input is not a directory: {input_dir}")
    manifest_data = _read_csv(
        input_dir / "manifest.csv", expected_header=MANIFEST_COLUMNS
    )
    schema_data = _read_csv(input_dir / "schema.csv", expected_header=SCHEMA_COLUMNS)
    data = {
        table: _read_csv(input_dir / f"{table}.csv", keep_rows=False)
        for table in TABLES
    }

    manifest: list[dict[str, Any]] = []
    for row_number, row in enumerate(manifest_data.rows, 2):
        record = dict(zip(MANIFEST_COLUMNS, row))
        table = _nonempty(record["table_name"], "table_name").casefold()
        if table not in TABLES:
            raise LocalError(f"manifest.csv has unexpected table_name {table!r}")
        record["table_name"] = table
        run_id = _nonempty(record["export_run_id"], "export_run_id")
        count = _nonempty(record["row_count"], "row_count")
        if not re.fullmatch(r"[0-9]+", count):
            raise LocalError(f"manifest row_count must be a non-negative integer: {count!r}")
        record["row_count"] = str(int(count))
        manifest.append(record)
    if len(manifest) != 4 or {row["table_name"] for row in manifest} != set(TABLES):
        raise LocalError("manifest.csv must contain exactly one row for each source table")
    run_ids = {row["export_run_id"] for row in manifest}
    if len(run_ids) != 1:
        raise LocalError("manifest.csv has inconsistent export_run_id values")
    run_id = next(iter(run_ids))

    schema: list[SourceColumn] = []
    seen_schema: dict[str, set[str]] = {table: set() for table in TABLES}
    for row_number, row in enumerate(schema_data.rows, 2):
        record = dict(zip(SCHEMA_COLUMNS, row))
        table = _nonempty(record["table_name"], "table_name").casefold()
        if table not in TABLES:
            raise LocalError(f"schema.csv has unexpected table_name {table!r}")
        name = _nonempty(record["column_name"], "column_name")
        key = name.casefold()
        if key == "_export_run_id":
            raise LocalError("_export_run_id is reserved and cannot be a source column")
        if key in seen_schema[table]:
            raise LocalError(f"schema.csv repeats {table}.{name}")
        seen_schema[table].add(key)
        data_type = _nonempty(record["data_type"], "data_type")
        precision = _parse_optional_int(record["precision"], "precision")
        scale = _parse_optional_int(record["scale"], "scale")
        nullable = _nonempty(record["is_nullable"], "is_nullable").upper()
        if nullable not in {"YES", "NO", "Y", "N", "1", "0", "TRUE", "FALSE"}:
            raise LocalError(f"schema.csv has invalid is_nullable {nullable!r}")
        schema.append(SourceColumn(table, name, data_type, precision, scale, nullable))
    if any(not seen_schema[table] for table in TABLES):
        raise LocalError("schema.csv must describe all four source tables")

    for table, csv_data in data.items():
        if not csv_data.headers or csv_data.headers[0] != "_export_run_id":
            raise LocalError(f"{table}.csv must have _export_run_id as its first column")
        header_map = _casefold_map(csv_data.headers[1:], f"{table}.csv header")
        if len(header_map) != len(csv_data.headers) - 1:
            raise LocalError(f"{table}.csv has a duplicate source column")
        schema_map = {column.name.casefold(): column.name for column in schema if column.table == table}
        unknown = sorted(set(header_map) - set(schema_map))
        if unknown:
            raise LocalError(f"{table}.csv has columns absent from schema.csv: {unknown}")
        missing = sorted(set(name.casefold() for name in REQUIRED_COLUMNS[table]) - set(header_map))
        if missing:
            raise LocalError(f"{table}.csv is missing required columns: {missing}")
        if csv_data.run_ids - {run_id}:
            raise LocalError(f"{table}.csv contains an export_run_id different from {run_id!r}")
        expected_count = next(
            int(row["row_count"]) for row in manifest if row["table_name"] == table
        )
        if csv_data.row_count != expected_count:
            raise LocalError(
                f"{table}.csv has {csv_data.row_count} rows; manifest says {expected_count}"
            )

    return ImportSet(
        manifest=manifest,
        schema=schema,
        data=data,
        run_id=run_id,
        manifest_sha256=manifest_data.sha256,
        schema_sha256=schema_data.sha256,
    )


def _duck_type(column: SourceColumn) -> str:
    kind = column.data_type.strip().casefold()
    base, separator, parameters = kind.partition("(")
    kind = base.strip()
    precision = column.precision
    scale = column.scale
    if separator:
        values = parameters.rstrip(")").split(",")
        if precision is None and values and values[0].strip().isdigit():
            precision = int(values[0].strip())
        if scale is None and len(values) > 1 and values[1].strip().isdigit():
            scale = int(values[1].strip())
    if kind in {"varchar", "char", "nvarchar", "nchar", "text", "ntext", "sysname", "xml"}:
        return "VARCHAR"
    if kind in {"tinyint"}:
        return "UTINYINT"
    if kind in {"smallint"}:
        return "SMALLINT"
    if kind in {"int", "integer"}:
        return "INTEGER"
    if kind in {"bigint"}:
        return "BIGINT"
    if kind in {"bit"}:
        return "BOOLEAN"
    if kind in {"decimal", "numeric"}:
        if precision is None or scale is None:
            raise LocalError(f"{column.table}.{column.name} numeric type lacks precision/scale")
        if not 1 <= precision <= 38 or not 0 <= scale <= precision:
            raise LocalError(f"{column.table}.{column.name} has invalid precision/scale")
        return f"DECIMAL({precision},{scale})"
    if kind in {"money"}:
        return "DECIMAL(19,4)"
    if kind in {"smallmoney"}:
        return "DECIMAL(10,4)"
    if kind in {"float"}:
        return "REAL" if precision is not None and precision <= 24 else "DOUBLE"
    if kind in {"real"}:
        return "REAL"
    if kind in {"date"}:
        return "DATE"
    if kind in {"datetime", "datetime2", "smalldatetime"}:
        return "TIMESTAMP"
    if kind in {"datetimeoffset"}:
        return "TIMESTAMPTZ"
    if kind == "time":
        return "TIME"
    if kind in {"uniqueidentifier"}:
        return "UUID"
    if kind in {"binary", "varbinary", "image", "rowversion", "timestamp"}:
        return "BLOB"
    raise LocalError(f"unsupported SQL Server data type {column.data_type!r} for {column.table}.{column.name}")


def _source_columns(source: ImportSet, table: str) -> list[SourceColumn]:
    exported = {name.casefold() for name in source.data[table].headers[1:]}
    return [
        column for column in source.schema
        if column.table == table and column.name.casefold() in exported
    ]


def _create_database(source: ImportSet, database: Path) -> None:
    duckdb = _require_duckdb()
    parent = database.parent
    if not parent.exists() or not parent.is_dir():
        raise LocalError(f"database parent directory does not exist: {parent}")
    if database.exists():
        raise LocalError(f"refusing to replace existing database: {database}")
    temporary = tempfile.TemporaryDirectory(prefix=f".{database.name}.", dir=parent)
    temp_path = Path(temporary.name) / "source.duckdb"
    try:
        connection = duckdb.connect(str(temp_path))
        try:
            connection.execute(
                "CREATE TABLE _edm_input_sha256 (file_name VARCHAR, sha256 VARCHAR NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE _edm_manifest ("
                "export_run_id VARCHAR, source_server VARCHAR, source_database VARCHAR, "
                "export_started_utc VARCHAR, isolation_mode VARCHAR, table_name VARCHAR, "
                "row_count BIGINT, scope VARCHAR)"
            )
            connection.execute(
                "CREATE TABLE _edm_schema ("
                "table_name VARCHAR, column_name VARCHAR, data_type VARCHAR, "
                "precision BIGINT, scale BIGINT, is_nullable VARCHAR)"
            )
            file_hashes = [("manifest.csv", source.manifest_sha256), ("schema.csv", source.schema_sha256)]
            file_hashes.extend((f"{table}.csv", source.data[table].sha256) for table in TABLES)
            connection.executemany("INSERT INTO _edm_input_sha256 VALUES (?, ?)", file_hashes)
            connection.executemany(
                "INSERT INTO _edm_manifest VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        row["export_run_id"],
                        row["source_server"],
                        row["source_database"],
                        row["export_started_utc"],
                        row["isolation_mode"],
                        row["table_name"],
                        int(row["row_count"]),
                        row["scope"],
                    )
                    for row in source.manifest
                ],
            )
            connection.executemany(
                "INSERT INTO _edm_schema VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (c.table, c.name, c.data_type, c.precision, c.scale, c.nullable)
                    for c in source.schema
                ],
            )

            for table in TABLES:
                csv_data = source.data[table]
                raw_name = f"raw_{table}"
                columns_sql = ", ".join(f"{_qident(name)} VARCHAR" for name in csv_data.headers)
                connection.execute(f"CREATE TABLE {_qident(raw_name)} ({columns_sql})")
                connection.execute(
                    f"COPY {_qident(raw_name)} FROM {_sql_literal(str(csv_data.path.resolve()))} "
                    "(FORMAT CSV, HEADER TRUE, DELIMITER ',', QUOTE '\"', ESCAPE '\"', NULL '\\N')"
                )
                with csv_data.path.open("rb") as imported:
                    if hashlib.file_digest(imported, "sha256").hexdigest() != csv_data.sha256:
                        raise LocalError(f"{table}.csv changed during import")
                loaded_count = connection.execute(f"SELECT COUNT(*) FROM {_qident(raw_name)}").fetchone()[0]
                if loaded_count != csv_data.row_count:
                    raise LocalError(f"{table}.csv imported row count differs from the validated CSV")
                source_cols = _source_columns(source, table)
                data_map = {name.casefold(): name for name in csv_data.headers[1:]}
                expressions: list[str] = []
                for column in source_cols:
                    duck_type = _duck_type(column)
                    raw_column = data_map[column.name.casefold()]
                    raw_reference = f"raw.{_qident(raw_column)}"
                    invalid: list[str] = []
                    if column.nullable in {"NO", "N", "0", "FALSE"}:
                        invalid.append(f"{raw_reference} IS NULL")
                    if duck_type != "VARCHAR":
                        invalid.append(
                            f"({raw_reference} IS NOT NULL AND TRY_CAST({raw_reference} AS {duck_type}) IS NULL)"
                        )
                    if invalid:
                        bad_value = connection.execute(
                            f"SELECT {raw_reference} FROM {_qident(raw_name)} AS raw "
                            f"WHERE {' OR '.join(invalid)} LIMIT 1"
                        ).fetchone()
                        if bad_value is not None:
                            raise LocalError(f"invalid typed value in {table}.{column.name}: {bad_value[0]!r}")
                    if duck_type == "VARCHAR":
                        expression = raw_reference
                    else:
                        expression = f"CAST(raw.{_qident(raw_column)} AS {duck_type})"
                    expressions.append(f"{expression} AS {_qident(column.name)}")
                connection.execute(
                    f"CREATE VIEW {_qident(table)} AS SELECT {', '.join(expressions)} "
                    f"FROM {_qident(raw_name)} AS raw"
                )
            connection.execute("CHECKPOINT")
        finally:
            connection.close()
        try:
            os.link(temp_path, database)
        except FileExistsError as exc:
            raise LocalError(f"refusing to replace existing database: {database}") from exc
    except LocalError:
        raise
    except Exception as exc:
        raise LocalError(f"could not create database {database}: {exc}") from exc
    finally:
        temporary.cleanup()


def _csv_cell(value: Any) -> str:
    return r"\N" if value is None else str(value)


def _write_csv_rows(stream: TextIO, description: Any, rows: Iterable[tuple[Any, ...]]) -> None:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow([item[0] for item in description])
    for row in rows:
        writer.writerow([_csv_cell(value) for value in row])


def _parse_single_select(sql: str, *, dialect: str) -> Any:
    sqlglot, _ = _require_sqlglot()
    if not sql.strip():
        raise LocalError("SQL is empty")
    try:
        statements = sqlglot.parse(sql, read=dialect)
    except Exception as exc:
        raise LocalError(f"SQL could not be parsed: {exc}") from exc
    if len(statements) != 1 or statements[0] is None:
        raise LocalError("only one SELECT statement is allowed")
    statement = statements[0]
    key = getattr(statement, "key", "")
    if key not in {"select", "union", "except", "intersect"}:
        raise LocalError("only a read-only SELECT statement is allowed")
    return statement


def _run_query(database: Path, sql: str, stream: TextIO) -> None:
    if not database.is_file():
        raise LocalError(f"database does not exist: {database}")
    _parse_single_select(sql, dialect="duckdb")
    duckdb = _require_duckdb()
    try:
        connection = duckdb.connect(str(database), read_only=True)
        try:
            result = connection.execute(sql)
            rows = (
                row
                for batch in iter(lambda: result.fetchmany(8192), [])
                for row in batch
            )
            _write_csv_rows(stream, result.description, rows)
        finally:
            connection.close()
    except LocalError:
        raise
    except Exception as exc:
        raise LocalError(f"query failed: {exc}") from exc


_DECLARATION_RE = re.compile(
    r"DECLARE\s+@(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+"
    r"(?P<type>[A-Za-z]+(?:\s*\([^;]*?\))?)"
    r"(?:\s*=\s*(?P<value>[^;]+?))?\s*;",
    re.IGNORECASE,
)


def _sql_default(value: str | None, name: str) -> Any:
    if value is None:
        raise LocalError(f"DECLARE @{name} has no default value")
    value = value.strip()
    if value.upper() == "NULL":
        return None
    if re.fullmatch(r"N?'(?:''|[^'])*'", value, re.IGNORECASE):
        quoted = value[1:] if value[:1].upper() == "N" else value
        return quoted[1:-1].replace("''", "'")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise LocalError(f"DECLARE @{name} default must be a literal") from exc


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)


def _replace_variables(sql: str, replacements: dict[str, str]) -> str:
    """Replace @variables outside SQL string and comment literals."""
    output: list[str] = []
    i = 0
    quote: str | None = None
    while i < len(sql):
        if quote:
            output.append(sql[i])
            if sql[i] == quote:
                if i + 1 < len(sql) and sql[i + 1] == quote:
                    output.append(sql[i + 1])
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if sql.startswith("--", i):
            end = sql.find("\n", i)
            end = len(sql) if end < 0 else end
            output.append(sql[i:end])
            i = end
            continue
        if sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            if end < 0:
                raise LocalError("unterminated SQL block comment")
            output.append(sql[i : end + 2])
            i = end + 2
            continue
        if sql[i] in "'\"":
            quote = sql[i]
            output.append(sql[i])
            i += 1
            continue
        if sql[i] == "@":
            match = re.match(r"@([A-Za-z_][A-Za-z0-9_]*)", sql[i:])
            if match:
                name = match.group(1).casefold()
                if name not in replacements:
                    raise LocalError(f"SQL references undeclared parameter @{match.group(1)}")
                output.append(replacements[name])
                i += len(match.group(0))
                continue
        output.append(sql[i])
        i += 1
    return "".join(output)


def _adapt_replay_sql(script: str, fx: Decimal | None, entity: str | None) -> tuple[str, dict[str, Any]]:
    declarations: dict[str, Any] = {}
    spans: list[tuple[int, int]] = []
    for match in _DECLARATION_RE.finditer(script):
        name = match.group("name").casefold()
        if name in declarations:
            raise LocalError(f"duplicate DECLARE @{name}")
        declarations[name] = _sql_default(match.group("value"), name)
        spans.append(match.span())
    declared_defaults = dict(declarations)
    body = script
    for start, end in reversed(spans):
        body = body[:start] + body[end:]
    if re.search(r"\bDECLARE\b", body, re.IGNORECASE):
        raise LocalError("unsupported DECLARE syntax")

    if fx is not None:
        declarations["gbp_to_usd"] = fx
    if entity is not None:
        declarations["bscr_entity"] = entity
    replacements: dict[str, str] = {}
    for name, value in declarations.items():
        replacements[name] = _sql_literal(value)
    body = _replace_variables(body, replacements)
    if re.search(r"\bOUTER\s+APPLY\b", body, re.IGNORECASE):
        raise LocalError("OUTER APPLY is not supported by the local replay adapter")
    body = re.sub(r"\bCROSS\s+APPLY\b", "CROSS JOIN LATERAL", body, flags=re.IGNORECASE)
    sqlglot, _ = _require_sqlglot()
    _parse_single_select(body, dialect="tsql")
    try:
        translated = sqlglot.transpile(body, read="tsql", write="duckdb")
    except Exception as exc:
        raise LocalError(f"SQL Server script could not be adapted to DuckDB: {exc}") from exc
    if len(translated) != 1:
        raise LocalError("replay script must contain exactly one final SELECT")
    adapted = translated[0]
    if re.search(r"\bCROSS\s+APPLY\b", adapted, re.IGNORECASE):
        adapted = re.sub(r"\bCROSS\s+APPLY\b", "CROSS JOIN LATERAL", adapted, flags=re.IGNORECASE)
    effective = {
        "gbp_to_usd": declarations.get("gbp_to_usd"),
        "qs_pct_retention": declarations.get("qs_pct_retention"),
        "srp_pct_retention": declarations.get("srp_pct_retention"),
        "bscr_entity": declarations.get("bscr_entity"),
    }
    missing = [name for name, value in effective.items() if value is None and name != "bscr_entity"]
    if missing:
        raise LocalError("replay is missing declared defaults: " + ", ".join(missing))
    return adapted, {
        "declared": declared_defaults,
        "effective": effective,
        "overrides": {"fx": fx, "entity": entity},
    }

def _exclusive_write(path: Path, writer: Any) -> None:
    if path.exists():
        raise LocalError(f"refusing to replace existing output: {path}")
    parent = path.parent
    if not parent.exists() or not parent.is_dir():
        raise LocalError(f"output parent directory does not exist: {parent}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        writer(temp_path)
        try:
            os.link(temp_path, path)
        except FileExistsError as exc:
            raise LocalError(f"refusing to replace existing output: {path}") from exc
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def _run_replay(database: Path, query_file: Path, output: Path, fx: Decimal | None, entity: str | None) -> None:
    if not query_file.is_file():
        raise LocalError(f"query file does not exist: {query_file}")
    try:
        script_bytes = query_file.read_bytes()
        script = script_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise LocalError(f"query file is not valid UTF-8: {exc}") from exc
    adapted, parameters = _adapt_replay_sql(script, fx, entity)
    duckdb = _require_duckdb()
    result_rows: list[tuple[Any, ...]]
    description: Any
    if not database.is_file():
        raise LocalError(f"database does not exist: {database}")
    try:
        connection = duckdb.connect(str(database), read_only=True)
        try:
            result = connection.execute(adapted)
            description = result.description
            result_rows = result.fetchall()
            manifest_result = connection.execute("SELECT * FROM _edm_manifest ORDER BY table_name")
            manifest_columns = [item[0] for item in manifest_result.description]
            source_manifest = [dict(zip(manifest_columns, row)) for row in manifest_result.fetchall()]
            input_hashes = dict(connection.execute("SELECT file_name, sha256 FROM _edm_input_sha256").fetchall())
        finally:
            connection.close()
    except Exception as exc:
        raise LocalError(f"replay failed: {exc}") from exc

    def write_output(path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as stream:
            _write_csv_rows(stream, description, result_rows)

    _exclusive_write(output, write_output)
    output_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    provenance_path = Path(str(output) + ".provenance.json")
    if provenance_path.exists():
        output.unlink()
        raise LocalError(f"refusing to replace existing provenance file: {provenance_path}")
    provenance = {
        "sql_sha256": hashlib.sha256(script_bytes).hexdigest(),
        "database": str(database.resolve()),
        "source_manifest": source_manifest,
        "input_sha256": input_hashes,
        "duckdb_version": duckdb.__version__,
        "sqlglot_version": _require_sqlglot()[0].__version__,
        "query_file": str(query_file.resolve()),
        "declared_parameters": _json_safe(parameters["declared"]),
        "effective_parameters": _json_safe(parameters["effective"]),
        "overrides": _json_safe(parameters["overrides"]),
        "output_sha256": output_hash,
        "dialect_adaptation_caveat": (
            "This output is a local DuckDB replay after sqlglot T-SQL adaptation "
            "and is not certification of SQL Server equivalence; collation and "
            "numeric aggregation may differ. Compare with the same-snapshot server output."
        ),
    }
    try:
        _exclusive_write_json(provenance_path, provenance)
    except Exception:
        output.unlink(missing_ok=True)
        raise


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


def _exclusive_write_json(path: Path, value: Any) -> None:
    def write(path_: Path) -> None:
        path_.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _exclusive_write(path, write)


def _decimal_arg(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"invalid decimal: {value!r}") from exc
    if not parsed.is_finite():
        raise argparse.ArgumentTypeError("decimal must be finite")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    import_parser = commands.add_parser("import", help="validate CSV export and build a fresh DuckDB database")
    import_parser.add_argument("--input", required=True, type=Path, help="directory containing manifest/schema and four data CSVs")
    import_parser.add_argument("--database", required=True, type=Path, help="new DuckDB database path; must not already exist")
    query_parser = commands.add_parser("query", help="run one read-only local SELECT and write CSV to stdout")
    query_parser.add_argument("--database", required=True, type=Path)
    query_parser.add_argument("--sql", required=True, help="one SELECT statement")
    replay_parser = commands.add_parser("replay", help="adapt and run a complete SQL Server BSCR script")
    replay_parser.add_argument("--database", required=True, type=Path)
    replay_parser.add_argument("--query", required=True, type=Path, help="SQL script containing DECLARE defaults and one SELECT")
    replay_parser.add_argument("--output", required=True, type=Path, help="new CSV path; must not already exist")
    replay_parser.add_argument("--fx", type=_decimal_arg, help="override declared @gbp_to_usd")
    replay_parser.add_argument("--entity", help="override declared @bscr_entity")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "import":
            _create_database(_parse_import_set(args.input), args.database)
            print(f"created {args.database}")
        elif args.command == "query":
            _run_query(args.database, args.sql, sys.stdout)
        elif args.command == "replay":
            _run_replay(args.database, args.query, args.output, args.fx, args.entity)
            print(f"created {args.output} and {args.output}.provenance.json")
        else:
            raise LocalError(f"unknown command {args.command!r}")
    except LocalError as exc:
        print(f"edm_local.py: error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
