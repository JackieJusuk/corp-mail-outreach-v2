# -*- coding: utf-8 -*-
"""
이메일 도메인 자체가 사라진(DNS에 더 이상 존재하지 않는) 회사를
발송 대상 DB(companies)와 관련 발송 로그(send_log)에서 함께 제거하는 스크립트.

배경 (2026-09-17): 발송 로그를 실제 Gmail 반송(bounce) 메일과 대조해보니
send_log에는 'success'로 기록됐지만 실제로는 도메인이 없어져 반송된 건이
다수 발견됨(예: lycos.co.kr, bibongehrb.com). 이런 회사는 앞으로도 영원히
발송이 불가능하므로 발송 대상 DB에서 제거한다.

"사라진 도메인"의 판정 기준: nslookup으로 MX 레코드를 조회했을 때
"Non-existent domain"(NXDOMAIN) 응답이 오는 경우. NXDOMAIN은 조회한
레코드 타입과 무관하게 그 도메인 자체가 DNS상에 존재하지 않음을 뜻하므로
MX 조회 1회로 충분하다. (주의: hanmal.net처럼 도메인은 살아있지만 메일
수신을 명시적으로 거부(null MX)하는 경우는 NXDOMAIN이 아니므로 이 스크립트의
삭제 대상이 아니다 - 별도 판단이 필요한 다른 케이스)

DNS 조회는 일시적인 네트워크 오류로도 실패할 수 있으므로, 조회 자체가
안 되는 경우(타임아웃 등)는 절대 삭제하지 않고 "확인 실패" 목록으로만
보고한다(보수적으로 처리 - 잘못 삭제하는 것을 방지).

사용법:
    python scripts/remove_dead_domain_companies.py [--db <DB경로>] [--dry-run]

    --dry-run: 삭제 없이 사라진 도메인/대상 회사 목록만 조회하고 종료
"""
import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dead_domain_check import domain_is_dead  # noqa: E402

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "corp_mail_outreach.db")
KST = timezone(timedelta(hours=9))


def parse_args():
    parser = argparse.ArgumentParser(description="사라진 이메일 도메인 회사를 발송 DB에서 제거")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite DB 파일 경로")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="삭제 없이 사라진 도메인/대상 회사 목록만 조회",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT business_reg_no, company_name, email FROM companies "
        "WHERE email_status = 'present' AND email IS NOT NULL AND email LIKE '%@%'"
    ).fetchall()

    domain_status_cache = {}
    dead_targets = []
    unresolved = []

    for row in rows:
        domain = row["email"].rsplit("@", 1)[1].strip().lower()
        if domain not in domain_status_cache:
            domain_status_cache[domain] = domain_is_dead(domain)
        status = domain_status_cache[domain]
        if status is True:
            dead_targets.append(row)
        elif status is None:
            unresolved.append((row, domain))

    print(f"이메일 보유 회사: {len(rows)}건 / 고유 도메인: {len(domain_status_cache)}개")
    print(f"사라진 도메인(NXDOMAIN)으로 확인된 회사: {len(dead_targets)}건")
    for r in dead_targets:
        print(f"  - {r['business_reg_no']} {r['company_name']} <{r['email']}>")

    if unresolved:
        print(f"조회 실패(타임아웃 등, 보수적으로 삭제 대상에서 제외): {len(unresolved)}건")
        for r, d in unresolved:
            print(f"  - {r['business_reg_no']} {r['company_name']} <{r['email']}> (domain={d})")

    if args.dry_run:
        print("(--dry-run 이므로 실제 삭제는 수행하지 않았습니다)")
        conn.close()
        return

    if not dead_targets:
        print("삭제할 대상이 없습니다.")
        conn.close()
        return

    db_path = Path(args.db)
    backup_path = db_path.with_name(
        f"{db_path.stem}_backup_{datetime.now(KST).strftime('%Y%m%d_%H%M%S')}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    print(f"삭제 전 DB 백업 완료: {backup_path.name}")

    reg_nos = [r["business_reg_no"] for r in dead_targets]
    placeholders = ",".join("?" * len(reg_nos))
    cur = conn.cursor()
    cur.execute(f"DELETE FROM send_log WHERE business_reg_no IN ({placeholders})", reg_nos)
    log_deleted = cur.rowcount
    cur.execute(f"DELETE FROM companies WHERE business_reg_no IN ({placeholders})", reg_nos)
    company_deleted = cur.rowcount
    conn.commit()
    conn.close()

    print(f"삭제 완료: companies {company_deleted}건, 관련 send_log {log_deleted}건 삭제")


if __name__ == "__main__":
    main()
