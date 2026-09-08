# -*- coding: utf-8 -*-
"""
DB 현황을 요약해서 보여주는 진단 스크립트.

PowerShell에서 python -c로 따옴표 섞인 SQL을 직접 넘기면 계속 깨지는 문제가
있어서(중첩 따옴표 이스케이프 방식이 셸마다 다름), 이런 확인용 조회도 매번
별도 스크립트로 만들어둔다.

사용법:
    python scripts/check_db_summary.py [--db <DB경로>]
"""
import argparse
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "corp_mail_outreach.db")


def parse_args():
    parser = argparse.ArgumentParser(description="DB 현황 요약 출력")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite DB 파일 경로")
    return parser.parse_args()


def main():
    args = parse_args()
    conn = sqlite3.connect(args.db)

    total = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    with_email = conn.execute(
        "SELECT COUNT(*) FROM companies WHERE email_status = 'present'"
    ).fetchone()[0]
    opted_in = conn.execute(
        "SELECT COUNT(*) FROM companies WHERE consent_status = 'opted_in'"
    ).fetchone()[0]
    opted_out = conn.execute(
        "SELECT COUNT(*) FROM companies WHERE consent_status = 'opted_out'"
    ).fetchone()[0]
    unconfirmed = conn.execute(
        "SELECT COUNT(*) FROM companies WHERE consent_status = 'unconfirmed'"
    ).fetchone()[0]
    sent_success = conn.execute(
        "SELECT COUNT(*) FROM send_log WHERE status = 'success'"
    ).fetchone()[0]

    conn.close()

    print(f"전체 레코드: {total}건")
    print(f"이메일 보유: {with_email}건")
    print(f"동의 상태 - 미확인: {unconfirmed}건 / 동의완료(opted_in): {opted_in}건 / 수신거부(opted_out): {opted_out}건")
    print(f"발송 성공 누적: {sent_success}건")


if __name__ == "__main__":
    main()
