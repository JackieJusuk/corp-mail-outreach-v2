-- corp-mail-outreach SQLite 스키마
-- requirements.md 2.3(데이터 수집·저장), 2.4(발송 로그), 2.7(기술 스택) 참조

-- 기업 정보 테이블: 사업자등록번호를 Primary Key로 사용 (요구사항 2.3)
CREATE TABLE IF NOT EXISTS companies (
    business_reg_no TEXT PRIMARY KEY,       -- 사업자등록번호
    region TEXT,                            -- 지역(소재지)
    company_name TEXT NOT NULL,             -- 기업체 상호 (법인/개인사업자 포함)
    representative_name TEXT,               -- 대표자명
    email TEXT,                             -- 이메일 주소 (없을 수 있음)
    email_status TEXT NOT NULL DEFAULT 'missing'
        CHECK (email_status IN ('present', 'missing')),  -- 이메일 보유 여부
    consent_status TEXT NOT NULL DEFAULT 'unconfirmed'
        CHECK (consent_status IN ('unconfirmed', 'opted_in', 'opted_out')),  -- 수신 동의 상태
    source_file TEXT,                       -- 적재 시 사용한 엑셀 파일명 (출처 추적용)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 발송 로그 테이블: 발송 시마다 1건씩 기록 (요구사항 2.4)
CREATE TABLE IF NOT EXISTS send_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_reg_no TEXT NOT NULL REFERENCES companies(business_reg_no),
    sent_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'skipped')),
    template_used TEXT,                     -- 사용한 템플릿 파일명
    note TEXT                               -- 비고 (실패 사유 등)
);

CREATE INDEX IF NOT EXISTS idx_send_log_business_reg_no ON send_log(business_reg_no);
CREATE INDEX IF NOT EXISTS idx_send_log_sent_at ON send_log(sent_at);
