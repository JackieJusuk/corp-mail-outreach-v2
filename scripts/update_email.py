# -*- coding: utf-8 -*-
"""
이메일 미확보 레코드에 대해 이메일 필드만 예외적으로 갱신하는 스크립트.
requirements.md 2.3절 "이메일 미확보 레코드 보강 정책" 참조.

원칙적으로 재적재 시 기존 사업자등록번호 레코드는 갱신하지 않고 건너뛰지만(skip),
전화 등 수동 확인으로 이메일을 알아낸 경우에는 이 스크립트로 이메일 필드만
예외적으로 갱신할 수 있다.

사용법:
    python scripts/update_email.py --business-reg-no <사업자등록번호> --email <이메일주소>
"""
import argparse
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "corp_mail_outreach.db")


def parse_args():
    parser = argparse.ArgumentParser(description="이메일 필드 예외적 갱신")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite DB 파일 경로")
    parser.add_argument("--business-reg-no", required=True)
    parser.add_argument("--email", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    cur.execute(
        "UPDATE companies SET email = ?, email_status = 'present' WHERE business_reg_no = ?",
        (args.email, args.business_reg_no),
    )
    conn.commit()
    changed = cur.rowcount
    conn.close()

    if changed:
        print(f"이메일을 갱신했습니다: {args.business_reg_no} -> {args.email}")
    else:
        print(f"해당 사업자등록번호를 찾을 수 없습니다: {args.business_reg_no}")


if __name__ == "__main__":
    main()
