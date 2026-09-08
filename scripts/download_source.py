# -*- coding: utf-8 -*-
"""
사용자가 지정한 공개데이터 파일의 URL을 다운로드하는 스크립트.
requirements.md 2.3절 "다운로드 자동화" 참조.

주의: 이 스크립트는 여러 사이트를 돌아다니며 이메일 등을 긁어모으는
자동 수집기(크롤러)가 아니다. 사용자가 매번 특정 파일 하나의 URL을
직접 지정해야만 동작하며, 그 파일 하나만 로컬에 받아온다.
(정보통신망법 제50조의2가 금지하는 "이메일 주소 자동 수집 프로그램"과는
성격이 다르다 — 브라우저로 다운로드 버튼을 누르는 것을 대신 해주는 것에 가깝다.)

사용법:
    python scripts/download_source.py --url <파일URL> [--out-dir downloads] [--filename 저장할이름]

다운로드한 파일은 이어서 import_excel.py로 적재하면 된다.
"""
import argparse
import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlparse

DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "downloads"


def parse_args():
    parser = argparse.ArgumentParser(description="공개데이터 파일 다운로드 (사용자 지정 URL 1건)")
    parser.add_argument("--url", required=True, help="다운로드할 공개데이터 파일의 URL")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="저장할 로컬 폴더")
    parser.add_argument("--filename", default=None, help="저장할 파일명 (생략 시 URL에서 추정)")
    return parser.parse_args()


def guess_filename(url):
    """URL 경로에서 파일명을 추정한다. 추정 실패 시 기본값을 사용한다."""
    path = urlparse(url).path
    name = Path(path).name
    return name or "downloaded_file"


def _encode_url(url):
    """
    URL에 한글 등 비-ASCII 문자가 그대로 포함된 경우(공공데이터 링크에 흔함) 인코딩한다.
    이미 %XX로 인코딩된 부분은 그대로 보존한다 (safe에 '%' 포함).
    """
    return quote(url, safe="%/:?&=,+@")


def download(url, dest_path):
    request = urllib.request.Request(_encode_url(url), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        dest_path.write_bytes(response.read())


def main():
    args = parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = args.filename or guess_filename(args.url)
    dest = out_dir / filename

    try:
        download(args.url, dest)
    except Exception as exc:  # noqa: BLE001 - 원인 불문 다운로드 실패를 사용자에게 그대로 알림
        print(f"다운로드 실패: {exc}")
        sys.exit(1)

    print(f"다운로드 완료: {dest}")
    print("이어서 다음 명령으로 DB에 적재할 수 있습니다:")
    print(f'  python scripts/import_excel.py --file "{dest}"')


if __name__ == "__main__":
    main()
