# -*- coding: utf-8 -*-
"""
수신 동의 상태를 수동으로 갱신하는 스크립트.
requirements.md 2.1절(컴플라이언스 요구사항 - 동의 상태 관리) 참조.

전화·이메일 회신 등으로 수신 동의(opted_in) 또는 수신거부(opted_out)를
직접 확인했을 때 사용한다. 신규 적재 레코드는 기본적으로 'unconfirmed'이며,
'opted_in' 상태인 레코드만 발송 대상이 된다 (pick_next_target.py 참조).

사용법:
    python scripts/set_consent.py --business-reg-no <사업자등록번호> \
        --status opted_in|opted_out|unconfirmed
"""
import argparse
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "corp_mail_outreach.db")


def parse_args():
    parser = argparse.ArgumentParser(description="수신 동의 상태 갱신")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite DB 파일 경로")
    parser.add_argument("--business-reg-no", required=True)
    parser.add_argument("--status", required=True, choices=["opted_in", "opted_out", "unconfirmed"])
    return parser.parse_args()


def main():
    args = parse_args()
    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    cur.execute(
        "UPDATE companies SET consent_status = ? WHERE business_reg_no = ?",
        (args.status, args.business_reg_no),
    )
    conn.commit()
    changed = cur.rowcount
    conn.close()

    if changed:
        print(f"동의 상태를 '{args.status}'(으)로 변경했습니다: {args.business_reg_no}")
    else:
        print(f"해당 사업자등록번호를 찾을 수 없습니다: {args.business_reg_no}")


if __name__ == "__main__":
    main()
