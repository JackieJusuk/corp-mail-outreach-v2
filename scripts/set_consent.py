# -*- coding: utf-8 -*-
"""
수신 동의 상태를 갱신하는 스크립트.
requirements.md 2.1절(컴플라이언스 요구사항 - 동의 상태 관리) 참조.

전화·이메일 회신 등으로 수신 동의(opted_in) 또는 수신거부(opted_out)를
확인했을 때 사용한다. 신규 적재 레코드는 기본적으로 'unconfirmed'이며,
'opted_in' 상태인 레코드만 발송 대상이 된다 (pick_next_target.py 참조).

동의 상태 판단의 근거(예: '전화로 동의 확보')는 --note로 남기며, 이는
사용자가 실제로 확인한 내용에 대한 진술을 기록해두기 위한 것으로,
데이터 출처·동의 확보의 적법성 자체는 requirements.md 2.2에 따라
사용자 책임이다.

사용법 (1건):
    python scripts/set_consent.py --business-reg-no <사업자등록번호> \
        --status opted_in|opted_out|unconfirmed --note "전화 동의 확보"

사용법 (전체 일괄, opted_out 레코드는 보호를 위해 대상에서 제외):
    python scripts/set_consent.py --all --status opted_in --note "전화 동의 확보"
"""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "corp_mail_outreach.db")


def parse_args():
    parser = argparse.ArgumentParser(description="수신 동의 상태 갱신")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite DB 파일 경로")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--business-reg-no", help="대상 사업자등록번호 1건")
    target.add_argument(
        "--all",
        action="store_true",
        help="전체 레코드 대상으로 일괄 변경 (이미 opted_out인 레코드는 명시적 수신거부이므로 보호를 위해 제외)",
    )
    parser.add_argument("--status", required=True, choices=["opted_in", "opted_out", "unconfirmed"])
    parser.add_argument(
        "--note",
        default=None,
        help="동의 상태 판단 근거 (예: '전화 동의 확보'). --all 사용 시 필수",
    )
    return parser.parse_args()


def _ensure_columns(conn):
    existing = {row[1] for row in conn.execute("PRAGMA table_info(companies)")}
    if "consent_note" not in existing:
        conn.execute("ALTER TABLE companies ADD COLUMN consent_note TEXT")
    if "consent_updated_at" not in existing:
        conn.execute("ALTER TABLE companies ADD COLUMN consent_updated_at TEXT")


def main():
    args = parse_args()
    if args.all and not args.note:
        raise SystemExit("--all 사용 시 --note로 동의 상태 판단 근거를 반드시 남겨야 합니다.")

    conn = sqlite3.connect(args.db)
    _ensure_columns(conn)
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if args.all:
        cur.execute(
            "UPDATE companies SET consent_status = ?, consent_note = ?, consent_updated_at = ? "
            "WHERE consent_status != 'opted_out'",
            (args.status, args.note, now),
        )
    else:
        cur.execute(
            "UPDATE companies SET consent_status = ?, consent_note = ?, consent_updated_at = ? "
            "WHERE business_reg_no = ?",
            (args.status, args.note, now, args.business_reg_no),
        )
    conn.commit()
    changed = cur.rowcount
    conn.close()

    if args.all:
        print(f"{changed}건의 동의 상태를 '{args.status}'(으)로 일괄 변경했습니다. (근거: {args.note})")
        print("(이미 opted_out으로 명시적 수신거부한 레코드는 보호를 위해 제외했습니다.)")
    elif changed:
        note_suffix = f" (근거: {args.note})" if args.note else ""
        print(f"동의 상태를 '{args.status}'(으)로 변경했습니다: {args.business_reg_no}{note_suffix}")
    else:
        print(f"해당 사업자등록번호를 찾을 수 없습니다: {args.business_reg_no}")


if __name__ == "__main__":
    main()
