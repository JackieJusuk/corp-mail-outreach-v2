# -*- coding: utf-8 -*-
"""
DB에 저장된 회사 목록을 조회해서 보여주는 스크립트.

사용법:
    python scripts/list_companies.py [--db <DB경로>] [--status unconfirmed|opted_in|opted_out] [--limit 50]
"""
import argparse
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "corp_mail_outreach.db")


def parse_args():
    parser = argparse.ArgumentParser(description="DB에 저장된 회사 목록 조회")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite DB 파일 경로")
    parser.add_argument(
        "--status",
        choices=["unconfirmed", "opted_in", "opted_out"],
        default=None,
        help="동의 상태로 필터링 (생략 시 전체)",
    )
    parser.add_argument("--limit", type=int, default=50, help="출력할 최대 건수 (기본 50)")
    return parser.parse_args()


def main():
    args = parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    if args.status:
        rows = conn.execute(
            "SELECT business_reg_no, company_name, region, email, consent_status "
            "FROM companies WHERE consent_status = ? ORDER BY company_name LIMIT ?",
            (args.status, args.limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT business_reg_no, company_name, region, email, consent_status "
            "FROM companies ORDER BY company_name LIMIT ?",
            (args.limit,),
        ).fetchall()

    conn.close()

    print(f"{'사업자등록번호':<15} {'상호':<25} {'지역':<20} {'이메일':<30} {'동의상태'}")
    for row in rows:
        print(
            f"{row['business_reg_no']:<15} {row['company_name']:<25} "
            f"{(row['region'] or ''):<20} {(row['email'] or ''):<30} {row['consent_status']}"
        )
    print(f"\n(최대 {args.limit}건까지 출력됨. 더 보려면 --limit 값을 늘리세요)")


if __name__ == "__main__":
    main()
