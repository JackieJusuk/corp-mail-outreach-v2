# -*- coding: utf-8 -*-
"""
이메일 도메인이 DNS상 완전히 사라졌는지(NXDOMAIN) 판정하는 공용 헬퍼.
requirements.md 2.3절(데이터 수집·저장 - 이메일 도메인 검증) 참조.

import_excel.py(적재 시점 검증)와 remove_dead_domain_companies.py(기존 DB 일괄 정리)
양쪽에서 공유해서 사용한다.

판정 기준: nslookup으로 MX 레코드를 조회했을 때 "Non-existent domain"(NXDOMAIN)
응답이 오는 경우. NXDOMAIN은 조회한 레코드 타입과 무관하게 그 도메인 자체가
DNS상에 존재하지 않음을 뜻하므로 MX 조회 1회로 충분하다. (주의: hanmal.net처럼
도메인은 살아있지만 메일 수신을 명시적으로 거부(null MX)하는 경우는 NXDOMAIN이
아니므로 여기서는 "사라진 도메인"으로 판정하지 않는다 - 별도 판단이 필요한 케이스)

DNS 조회는 일시적인 네트워크 오류로도 실패할 수 있으므로, 조회 자체가 안 되는
경우(타임아웃 등)는 True/False가 아닌 None(확인 불가)을 반환한다. 호출하는
쪽에서는 None을 "사라진 도메인이 아님"과 동일하게(보수적으로) 취급해야 한다.
"""
import subprocess

NSLOOKUP_TIMEOUT_SECONDS = 5


def domain_is_dead(domain):
    """사라진(NXDOMAIN) 도메인이면 True, 살아있으면 False, 확인 불가면 None."""
    try:
        result = subprocess.run(
            ["nslookup", "-type=MX", domain],
            capture_output=True,
            timeout=NSLOOKUP_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    # Windows nslookup은 NXDOMAIN 메시지를 stdout이 아니라 stderr로 출력한다.
    return b"Non-existent domain" in (result.stdout + result.stderr)
