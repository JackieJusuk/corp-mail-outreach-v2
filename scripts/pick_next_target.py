# -*- coding: utf-8 -*-
"""
다음 발송 대상 1건을 선정하는 스크립트.
requirements.md 2.1(컴플라이언스), 2.5(발송 방식·페이싱), 2.6(실행 아키텍처) 참조.

로컬 Claude Code가 (Routine 등으로) 30분 간격 근처에 이 스크립트를 실행해
발송 가능 여부와 대상을 확인한다. 이 스크립트는 조회만 수행하며,
실제 Gmail 발송은 로컬 Claude Code가 Gmail MCP 커넥터로 직접 수행한다.
발송 후에는 log_send.py로 결과를 기록해야 한다.

발송 자격 조건 (모두 만족해야 함):
    - consent_status = 'opted_in'  (명시적 수신 동의)
    - email_status = 'present'     (이메일 보유)
    - 과거에 status='success'로 발송된 적 없는 대상 (동일 대상 중복 발송 금지)
    - 현재 시각이 평일(월~금) 09:00~18:00 (KST)
    - 가장 최근 성공 발송으로부터 30분 이상 경과 (30분당 1건 페이싱)

사용법:
    python scripts/pick_next_target.py [--db <DB경로>]

출력: JSON 1줄
    - 발송 가능: {"eligible": true, "target": {...}}
    - 발송 불가: {"eligible": false, "reason": "..."}
"""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "corp_mail_outreach.db")
KST = ZoneInfo("Asia/Seoul")
BUSINESS_START_HOUR = 9  # 09:00 이상
BUSINESS_END_HOUR = 18   # 18:00 미만
WEEKDAYS_ONLY = True     # 월(0)~금(4)만 발송, 토·일 제외
MIN_INTERVAL_SECONDS = 1800  # 30분당 1건


def parse_args():
    parser = argparse.ArgumentParser(description="다음 발송 대상 1건 선정")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite DB 파일 경로")
    return parser.parse_args()


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False))


def main():
    args = parse_args()
    now = datetime.now(KST)

    if WEEKDAYS_ONLY and now.weekday() >= 5:  # 5=토, 6=일
        emit({"eligible": False, "reason": "주말에는 발송할 수 없습니다 (평일 09:00~18:00 KST만 발송)."})
        return

    if not (BUSINESS_START_HOUR <= now.hour < BUSINESS_END_HOUR):
        emit({"eligible": False, "reason": "업무시간(평일 09:00~18:00 KST) 외에는 발송할 수 없습니다."})
        return

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 페이싱 확인: 마지막 성공 발송으로부터 30분이 지나야 함
    # 주의: SQLite의 datetime('now')는 UTC 기준이므로, 저장된 sent_at은 UTC로 해석해야 한다.
    # (KST로 잘못 해석하면 9시간 오차가 생겨 페이싱 체크가 무력화된다)
    cur.execute(
        "SELECT sent_at FROM send_log WHERE status = 'success' ORDER BY sent_at DESC LIMIT 1"
    )
    last = cur.fetchone()
    if last:
        last_sent_utc = datetime.fromisoformat(last["sent_at"]).replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - last_sent_utc).total_seconds()
        if elapsed < MIN_INTERVAL_SECONDS:
            wait_sec = int(MIN_INTERVAL_SECONDS - elapsed)
            emit({
                "eligible": False,
                "reason": f"마지막 발송 후 30분이 지나지 않았습니다. 약 {wait_sec}초 후 다시 확인하세요.",
            })
            conn.close()
            return

    # 발송 대상 조회: 동의완료 + 이메일보유 + 미발송
    cur.execute(
        """
        SELECT business_reg_no, company_name, representative_name, email
        FROM companies
        WHERE consent_status = 'opted_in'
          AND email_status = 'present'
          AND business_reg_no NOT IN (
              SELECT business_reg_no FROM send_log WHERE status = 'success'
          )
        ORDER BY created_at ASC
        LIMIT 1
        """
    )
    target = cur.fetchone()
    conn.close()

    if not target:
        emit({"eligible": False, "reason": "발송 가능한(동의완료·이메일보유·미발송) 대상이 없습니다."})
        return

    emit({
        "eligible": True,
        "target": {
            "business_reg_no": target["business_reg_no"],
            "company_name": target["company_name"],
            "representative_name": target["representative_name"],
            "email": target["email"],
        },
    })


if __name__ == "__main__":
    main()
