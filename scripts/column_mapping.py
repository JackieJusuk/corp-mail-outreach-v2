# -*- coding: utf-8 -*-
"""
엑셀 헤더(컬럼명)를 표준 필드명으로 정규화하는 매핑 테이블 및 함수.
requirements.md 2.3절 "컬럼 매핑(헤더 정규화) 규칙" 참조.

공공데이터포털/키프리스/나라장터 등 소스마다 헤더명이 제각각이므로,
자주 쓰이는 별칭을 표준 필드명에 매핑해준다. 매핑되지 않는 헤더는
import_excel.py가 목록으로 출력하며, 로컬 Claude Code가 사용자에게
물어본 뒤 --mapping-overrides 옵션으로 보완한다.
"""

# 표준 필드명 -> 흔히 쓰이는 엑셀 헤더 별칭 목록
FIELD_ALIASES = {
    "business_reg_no": ["사업자등록번호", "사업자번호", "등록번호", "사업자등록번호(법인번호)"],
    "region": ["지역", "소재지", "주소", "소재지주소"],
    "company_name": ["상호", "상호명", "업체명", "회사명", "법인명", "기업명"],
    "representative_name": ["대표자명", "대표자", "성명", "대표", "대표이사"],
    "email": ["이메일", "이메일주소", "e-mail", "email", "메일주소"],
}


def _normalize(text):
    """공백 제거 + 소문자화하여 별칭 비교를 느슨하게 만든다."""
    return str(text).strip().lower().replace(" ", "")


def build_alias_lookup():
    """정규화된 별칭 문자열 -> 표준 필드명 딕셔너리를 만든다."""
    lookup = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            lookup[_normalize(alias)] = field
    return lookup


def parse_kv_pairs(text):
    """
    "AM=email,C=business_reg_no" 형태의 문자열을 {"AM": "email", "C": "business_reg_no"}로 파싱한다.

    Windows PowerShell/cmd에서 JSON(중괄호+큰따옴표)을 커맨드라인 인자로 넘기면
    셸마다 따옴표 처리 방식이 달라 깨지기 쉽다. 이 형식은 따옴표가 전혀 필요 없어
    --mapping-overrides, --letter-overrides 양쪽에서 공통으로 사용한다.
    """
    result = {}
    text = (text or "").strip()
    if not text:
        return result
    for pair in text.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise ValueError(f"'key=value' 형식이 아닙니다: {pair!r}")
        key, value = pair.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def letter_to_index(letter):
    """엑셀 열 문자(A, B, ..., Z, AA, AM ...)를 0부터 시작하는 열 인덱스로 변환한다."""
    letter = letter.strip().upper()
    result = 0
    for ch in letter:
        if not ("A" <= ch <= "Z"):
            raise ValueError(f"잘못된 엑셀 열 문자입니다: {letter!r}")
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result - 1


def resolve_columns(headers, overrides=None, letter_overrides=None):
    """
    엑셀 헤더 목록을 표준 필드명에 매핑한다.

    Args:
        headers: 엑셀 첫 행의 헤더 문자열 목록
        overrides: {"원본헤더": "표준필드명"} 형태의 수동 매핑 (선택) — 헤더 텍스트 기준
        letter_overrides: {"AM": "email"} 형태의 수동 매핑 (선택) — 엑셀 열 문자 기준.
            헤더 텍스트가 특이해서 별칭 매핑이 어려울 때, "AM 컬럼이 이메일이다"처럼
            사용자가 눈으로 확인한 열 위치를 그대로 지정할 수 있다. overrides보다 우선한다.

    Returns:
        (mapping, unmapped)
        mapping: {헤더의 열 인덱스: 표준필드명}
        unmapped: 매핑에 실패한 원본 헤더 목록 (letter_overrides로 지정된 열은 제외)
    """
    lookup = build_alias_lookup()
    overrides = overrides or {}
    letter_overrides = letter_overrides or {}
    letter_index_map = {letter_to_index(letter): field for letter, field in letter_overrides.items()}

    mapping = {}
    unmapped = []

    for idx, header in enumerate(headers):
        if idx in letter_index_map:
            mapping[idx] = letter_index_map[idx]
        elif header in overrides:
            mapping[idx] = overrides[header]
        else:
            key = _normalize(header)
            if key in lookup:
                mapping[idx] = lookup[key]
            else:
                unmapped.append(header)

    return mapping, unmapped
