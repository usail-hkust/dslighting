from pathlib import Path
import shutil
import sqlite3

DB_FILENAME = "database.db"
GOLD_ROOT = Path(__file__).resolve().parents[2] / "raw_dacode" / "gold" / "data-wrangling-040"


def _copy_sqlite_schema(src: Path, dst: Path) -> None:
    if dst.exists():
        dst.unlink()
    src_conn = sqlite3.connect(src)
    dst_conn = sqlite3.connect(dst)
    try:
        objects = src_conn.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE sql IS NOT NULL
              AND type IN ('table', 'index', 'trigger', 'view')
            ORDER BY CASE type
                WHEN 'table' THEN 0
                WHEN 'index' THEN 1
                WHEN 'trigger' THEN 2
                WHEN 'view' THEN 3
                ELSE 4
            END, name
            """
        ).fetchall()
        for _, name, sql in objects:
            if name == "sqlite_sequence":
                continue
            dst_conn.execute(sql)
        dst_conn.commit()
    finally:
        src_conn.close()
        dst_conn.close()


def prepare(raw: Path, public: Path, private: Path):
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)

    for f in raw.iterdir():
        if f.is_file() and f.name != DB_FILENAME and not f.name.startswith("_"):
            shutil.copy2(f, public / f.name)

    gold = GOLD_ROOT / DB_FILENAME
    shutil.copy2(gold, private / DB_FILENAME)
    _copy_sqlite_schema(gold, public / DB_FILENAME)
