# -*- coding: utf-8 -*-
"""
SQLite DB를 초기화(테이블 생성)하는 스크립트.
requirements.md 2.7절(기술 스택: SQLite + Python) 참조.

사용법:
    python scripts/init_db.py [--db <DB파일경로>]

DB 파일 경로를 지정하지 않으면 레포 루트의 corp_mail_outreach.db 를 사용한다.
이미 테이블이 있으면 아무 것도 하지 않는다 (CREATE TABLE IF NOT EXISTS).
"""
import argparse
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "corp_mail_outreach.db"


def parse_args():
    parser = argparse.ArgumentParser(description="corp-mail-outreach SQLite DB 초기화")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite DB 파일 경로")
    return parser.parse_args()


def main():
    args = parse_args()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = sqlite3.connect(args.db)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    print(f"DB 초기화 완료: {args.db}")


if __name__ == "__main__":
    main()
