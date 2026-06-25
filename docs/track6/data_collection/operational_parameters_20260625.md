# Track6 데이터 수집 운영 파라미터(정책 상수) 기준

이 문서는 `docs/track6/data_collection/` 설계 문서 세트에서 "확정 필요"로 두었던
운영 파라미터(임계치·기간·정책값)를 **한 곳에 모은 단일 기준**이다.

- 각 설계 문서는 이 표의 **파라미터 키**(예: `FRESH-WARN-N`)를 참조한다. 값을 바꿀 때는 **이 문서만** 수정한다.
- 모든 값은 **초기 기본값**이다. "측정 후 조정" 표시가 있는 항목은 운영 첫 2~4주 실측 후 값을 갱신한다.
- 보안·역할 정책(인증 방식, required_role)은 조직 정책 확정 시 이 표를 갱신한다.

값 상태 표기: `기준`(바로 적용), `잠정`(측정/정책 확정 후 조정), `정책`(조직 결정 필요)

---

## A. 인증 / 권한 (auth)

| 키 | 항목 | 기본값 | 상태 | 근거 / 사용처 |
|----|------|--------|------|---------------|
| `AUTH-METHOD` | 어드민 인증 방식 | JWT 액세스 토큰 + 역할 claim | 정책 | stateless API에 표준적. `actor_id`는 토큰 claim에서 서버가 주입. user_admin_api §12 |
| `AUTH-TOKEN-TTL` | 액세스 토큰 만료 | 60분(액세스) / 14일(리프레시) | 정책 | 일반적 어드민 세션 수명. user_admin_api §12 |

### A-1. required_role 매핑 (엔드포인트 최소 권한)

역할 위계: 개발자 < 운영 담당자(운영자) < 데이터 분석가 < 데이터 관리자.
"최소 권한"은 해당 역할 **이상**을 의미한다(데이터 관리자는 하위 권한 포함).

| 엔드포인트/액션(절) | 최소 권한 |
|----------------------|-----------|
| 조회 전반(대시보드/큐/상세, GET) | 운영 담당자 |
| 수집 run 재수집 요청(5.4 `request_retry`) | 운영 담당자 |
| 원천 등록/수정(6.x) | 데이터 관리자 |
| 수동 CSV 업로드/매핑 확정(6.3/6.5) | 데이터 분석가 |
| 작품 품질 검수(8.2 approve/patch/hold/exclude) | 운영 담당자 |
| 작가명 검수(8.4 approve/add_alias/hold/reject) | 운영 담당자 |
| artist identity 연결 검수(8.6) | 데이터 관리자 |
| 신규 artist_key 생성 결정(8.8 decision) | 데이터 관리자 |
| snapshot 확정요청(9.3.1) | 운영 담당자 |
| snapshot 생성승인(9.3.2) | 데이터 관리자 |
| snapshot 서빙승인(9.3.3) | 데이터 관리자 |
| 모델 승격/롤백(7.3) | 데이터 관리자 |
| audit-logs 조회(10.1) | 데이터 관리자 |

---

## B. 크롤링 / 수집 (`source_registry`, periodic §5.1)

원천별로 다를 수 있으며 아래는 1원천 기준 기본값이다. 차단(429/403)·밴 발생 시 하향 조정한다.

| 키 | 컬럼/항목 | 기본값 | 상태 | 근거 / 사용처 |
|----|-----------|--------|------|---------------|
| `CRAWL-CONCURRENCY` | `max_concurrency` | 2 (해외 Artsy/Saatchi: 1) | 잠정 | 정중한 크롤링, 밴 회피. periodic §5.1 |
| `CRAWL-DELAY-SEC` | `request_delay_sec` | 1.0초 | 잠정 | 요청 간 최소 간격. periodic §5.1 |
| `CRAWL-DAILY-CAP` | `daily_request_cap` | 20,000회/일 | 잠정 | 주간 수집 카탈로그 규모 여유. 초과 시 다음 주기 이월. periodic §5.1 |
| `CRAWL-BACKOFF` | `backoff_policy_json` | `initial_delay_sec=2`, `max_retries=5`, `multiplier=2`, jitter ±20% | 기준 | 2→4→8→16→32초 지수 backoff. periodic §5.1 |
| `CRAWL-UA` | `user_agent` | `VestatBot/0.1 (+운영 연락처)` | 정책 | 식별 가능한 UA. periodic §5.1 |
| `CRAWL-ROBOTS` | `robots_policy` | 준수(robots.txt/ToS 위반 경로 미수집) | 정책 | 합법성. periodic §5.1, weekly §6.1 |

---

## C. 스케줄 / 락 / watchdog

| 키 | 항목 | 기본값 | 상태 | 근거 / 사용처 |
|----|------|--------|------|---------------|
| `WEEKLY-CRON` | 주간 수집 시각 | 매주 월 03:00 | 기준 | weekly §4 (이미 고정) |
| `RUN-WALLCLOCK-LIMIT` | run별 실행시간 상한 | 24시간 | 기준 | 주간 1원천 수집 여유 상한. 초과 시 강제 종료(`failed`). weekly §4.1 |
| `RUN-HEARTBEAT-INTERVAL` | run heartbeat 갱신 주기 | 60초 | 기준 | periodic §5.2.2 |
| `RUN-HEARTBEAT-TIMEOUT` | collector_run 좀비 회수 임계 | 2시간 | 기준 | heartbeat 미갱신 시 `failed` 회수. periodic §5.2.2, weekly §9 |
| `SNAP-HEARTBEAT-TIMEOUT` | snapshot_request(approved/generating) 회수 임계 | 1시간 | 기준 | 생성 작업은 더 짧게. periodic §5.14.1 |

---

## D. 보존 / 시크릿 (periodic §5.3, §5.20)

| 키 | 항목 | 기본값 | 상태 | 근거 / 사용처 |
|----|------|--------|------|---------------|
| `RAW-RETENTION` | raw payload(object storage)+DB raw row 보존기간 | 180일(6개월) | 정책 | 만료분 일괄 정리. 비가역 identity 결정·snapshot은 정리 제외(영구). periodic §5.3 |
| `SECRET-DENYLIST` | fingerprint/저장 시 마스킹할 비밀 파라미터 | `cafe24_app_key, api_key, access_token, token, secret, signature, sig, key, password` | 기준 | url_sanitized/fingerprint에서 제외. periodic §5.3 |
| `TRACKING-DENYLIST` | fingerprint에서 제거할 휘발성 파라미터 | `utm_source, utm_medium, utm_campaign, utm_term, utm_content, fbclid, gclid, _ga, ref` | 기준 | 동일 요청이 다른 hash 되는 것 방지. periodic §5.3 |
| `KEY-ROTATION` | 자격증명 회전 주기 | 90일 | 정책 | 신규 발급→무중단 교체→구 키 폐기. periodic §5.20 |

> fingerprint 규칙: `SECRET-DENYLIST`·`TRACKING-DENYLIST`만 제외하고 나머지 query/body 파라미터는 모두 포함(과분할은 안전, 과병합 우선 차단).

---

## E. 데이터 신선도 (freshness)

주간 수집(+검수 이월)이므로 사용자가 보는 값은 정상적으로 최대 약 1주 과거다. 아래는 그 위의 경고/차단 임계다.

| 키 | 항목 | 기본값 | 상태 | 근거 / 사용처 |
|----|------|--------|------|---------------|
| `FRESH-WARN-N` | 신선도 경고 임계(N일) | 10일 | 잠정 | 1수집주기(7일)+검수 여유. as_of가 N일 초과 시 경고. scenarios §2.1/2.6, user_admin_api §2.6 |
| `FRESH-HIDE-M` | 카드 숨김 임계(M일, M>N) | 21일 | 잠정 | 3주기. 구데이터 무한 노출 차단. scenarios §2.7, user_admin_api §2.6 |
| `FRESH-MODEL-GAP` | deployment-데이터 괴리 경고 임계 | 14일 | 잠정 | active deployment 학습 snapshot vs 최신 approved snapshot 괴리. user_admin_api §2.6 |

---

## F. 검수 큐 동시성

| 키 | 항목 | 기본값 | 상태 | 근거 / 사용처 |
|----|------|--------|------|---------------|
| `REVIEW-CLAIM-TTL` | 검수 항목 claim/lock 만료 | 30분 | 기준 | 같은 항목 동시 처리 방지, 방치 시 자동 해제. user_admin_api §2.7 |

---

## G. 품질 임계 — canary 절대 보유율 하한 (weekly §6.5 보강)

초기 잠정값이며 **운영 첫 2~4주 실측 후 확정**한다. 상대치(전주 대비) 경고와 병행 적용.

| 키 | 항목 | 기본값 | 상태 | 근거 / 사용처 |
|----|------|--------|------|---------------|
| `QUAL-PRICE-MIN` | 가격 숫자 보유율 하한 | 20% | 잠정 | 미달 시 가격 parser 점검 + snapshot 보류. weekly §canary |
| `QUAL-SIZE-MIN` | 크기(가로/세로 cm) 보유율 하한 | 30% | 잠정 | 미달 시 크기 parser 점검. weekly §canary |
| `QUAL-ARTIST-MIN` | 작가명 보유율 하한 | 90% | 잠정 | 작가명은 거의 항상 존재. 미달 시 추출 위치 변경 의심. weekly §canary |
| `UPGRADE-TRIGGER` | 주 2회 상향 후보 트리거 | 10% | 잠정 | 국내 사이트 최근 4회 정상 run 변경률 평균 임계. weekly §7 |

---

## H. API 기타 기본값

| 키 | 항목 | 기본값 | 상태 | 근거 / 사용처 |
|----|------|--------|------|---------------|
| `RETRY-SCOPE-DEFAULT` | `request_retry`의 `scope` 미지정 기본 | `failed_only` | 기준 | 운영 비용상 실패분만. user_admin_api §5.4 |
| `SUMMARY-DENOM` | 보유율 분모(모집단) | normalized 기준 | 기준 | user_admin_api §5.1 |

---

## 변경 이력

| 일자 | 변경 | 비고 |
|------|------|------|
| 2026-06-25 | 초기 기본값 일괄 확정 | 잠정 항목은 운영 실측 후 갱신 |
