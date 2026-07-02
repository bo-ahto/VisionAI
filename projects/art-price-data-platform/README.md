# Art Price Data Platform

작품 가격 예측 서비스의 데이터 수집, 표준화, 검수, snapshot, 모델 배포, 사용자/어드민 화면을 한 프로젝트 단위로 관리한다.

## Directory Layout

```text
art-price-data-platform/
  docs/        설계 문서, PRD, API/DB/프론트 명세
  src/         서비스 구현 코드
  scripts/     운영/마이그레이션/검증 스크립트
  tests/       프로젝트 전용 테스트
  fixtures/    API mock, E2E fixture, 샘플 입력
  config/      운영 seed, override, 정책 config
  models/      model card, manifest, small metadata only
```

## Development Entry Points

- 개발 순서: `docs/first_development_roadmap_20260625.md`
- 작업 단위: `docs/first_development_backlog_20260625.md`
- 개발 착수 전 확정값: `docs/development_prestart_decisions_20260625.md`
- API 기준: `docs/user_admin_api_plan_20260625.md`
- DB 기준: `docs/periodic_raw_collection_mysql_plan_20260623.md`
- ERD / 데이터 흐름: `docs/database_erd_data_flow_20260626.md`

## Git / Artifact Policy

- 이 repo는 제품 개발용 Git repo다. VisionAI의 연구/실험 산출물 전체를 가져오지 않는다.
- 대용량 raw/export/model artifact는 object storage 또는 artifact registry에 두고, Git에는 manifest와 checksum만 저장한다.
- 연구 근거와 VisionAI source commit/path는 `docs/research_references.md`에 남긴다.

## Naming

이 프로젝트의 관리 단위 명칭은 `art-price-data-platform`이다. 과거 실험 트랙명은 새 코드, route, image, fixture, 신규 artifact 경로에 사용하지 않는다.
