# -*- coding: utf-8 -*-
"""
공개데이터 엑셀 파일을 파싱하여 SQLite DB(companies 테이블)에 적재하는 배치 스크립트.
requirements.md 2.3절(데이터 수집·저장 요구사항) 참조.

사용법:
    python scripts/import_excel.py --file <엑셀경로> [--db <DB경로>] \
        [--mapping-overrides '{"원본헤더":"표준필드명"}']

동작 순서:
    1. 엑셀 첫 행을 헤더로 읽고 표준 필드명으로 정규화한다 (column_mapping.py).
    2. 매핑되지 않은 헤더가 있으면 적재를 중단하고 목록을 출력한다.
       -> 로컬 Claude Code가 이 출력을 보고 사용자에게 해당 컬럼이 무엇인지 물어본 뒤,
          --mapping-overrides 옵션으로 다시 실행한다.
    3. 사업자등록번호(Primary Key)가 이미 DB에 있으면 해당 레코드는 건너뛴다 (skip, 갱신 없음).
    4. 이메일이 비어 있으면 email_status='missing'으로 저장한다 (발송 대상에서 자동 제외됨).
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))
from column_mapping import resolve_columns  # noqa: E402

REQUIRED_FIELDS = ["business_reg_no", "company_name"]
DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "corp_mail_outreach.db")


def parse_args():
    parser = argparse.ArgumentParser(description="공개데이터 엑셀 파일을 DB에 적재")
    parser.add_argument("--file", required=True, help="적재할 엑셀 파일 경로")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite DB 파일 경로")
    parser.add_argument(
        "--mapping-overrides",
        default="{}",
        help='매핑 실패 헤더에 대한 수동 매핑 JSON (헤더 텍스트 기준), 예: \'{"원본헤더":"company_name"}\'',
    )
    parser.add_argument(
        "--letter-overrides",
        default="{}",
        help='엑셀 열 문자 기준 수동 매핑 JSON, 예: \'{"AM":"email"}\' (헤더 텍스트가 특이할 때 사용, mapping-overrides보다 우선)',
    )
    return parser.parse_args()


def load_rows(file_path):
    """엑셀 파일을 읽어 (헤더 목록, 데이터 행 목록)을 반환한다."""
    wb = load_workbook(filename=file_path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    data_rows = rows[1:]
    return headers, data_rows


def clean(value):
    """엑셀 셀 값을 문자열로 정리한다 (앞뒤 공백 제거, 빈 값은 None)."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def main():
    args = parse_args()
    overrides = json.loads(args.mapping_overrides)
    letter_overrides = json.loads(args.letter_overrides)

    headers, data_rows = load_rows(args.file)
    if not headers:
        print("엑셀 파일에 데이터가 없습니다.")
        sys.exit(1)

    mapping, unmapped = resolve_columns(headers, overrides, letter_overrides)

    if unmapped:
        print("다음 컬럼을 표준 필드에 매핑하지 못했습니다. --mapping-overrides(헤더텍스트) 또는 --letter-overrides(열문자)로 지정해 다시 실행하세요:")
        for header in unmapped:
            print(f"  - {header!r}")
        sys.exit(2)

    mapped_fields = set(mapping.values())
    missing_required = [f for f in REQUIRED_FIELDS if f not in mapped_fields]
    if missing_required:
        print(f"필수 필드가 매핑되지 않았습니다: {missing_required}")
        sys.exit(2)

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    inserted, skipped_dup, skipped_no_key = 0, 0, 0

    for row in data_rows:
        record = {}
        for idx, field in mapping.items():
            record[field] = row[idx] if idx < len(row) else None

        business_reg_no = clean(record.get("business_reg_no"))
        if not business_reg_no:
            skipped_no_key += 1
            continue

        email = clean(record.get("email"))
        email_status = "present" if email else "missing"

        cur.execute(
            """
            INSERT OR IGNORE INTO companies
                (business_reg_no, region, company_name, representative_name, email, email_status, source_file)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                business_reg_no,
                clean(record.get("region")),
                clean(record.get("company_name")),
                clean(record.get("representative_name")),
                email,
                email_status,
                Path(args.file).name,
            ),
        )
        if cur.rowcount == 1:
            inserted += 1
        else:
            skipped_dup += 1

    conn.commit()
    conn.close()

    print(
        f"적재 완료: 신규 {inserted}건, 중복(기존 사업자번호) 스킵 {skipped_dup}건, "
        f"사업자등록번호 없음 스킵 {skipped_no_key}건"
    )


if __name__ == "__main__":
    main()
