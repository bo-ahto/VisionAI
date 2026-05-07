# VisionAI

Computer Vision & AI Platform

## Setup

권장: [uv](https://github.com/astral-sh/uv) 사용 — `uv.lock`이 의존성을 핀하여 OOF / 학습 결과 재현성을 보장합니다.

```bash
# uv로 sync (uv.lock 기준 — 권장)
uv sync --extra dev --extra price-engine-core --extra price-engine-exp

# price engine API까지 포함
uv sync --all-extras

# 잠금 파일 갱신 (의존성 변경 시)
uv lock

# 잠금 무결성 확인 (CI에서 사용)
uv lock --check
```

대안 (uv 사용하지 않을 때):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,train,price-engine-core,price-engine-exp,price-engine-api]"
```

## Development

```bash
# 린트
ruff check src/

# 포매팅
ruff format src/

# 타입 체크
mypy src/

# 테스트
pytest tests/
```

## Project Structure

```
src/visionai/    # 메인 패키지
tests/           # 테스트
scripts/         # 유틸리티 스크립트
docs/            # 문서
```

## Canonical artifact manifest

운영 v3 모델의 artifact provenance 기준 = `model_test_results/integrated_v3_filtered_tuned.provenance.json` (운영 서빙 모델 `v3_filtered_tuned` 32f 의 학습 dataset / hyperparameters / commit hash 등의 manifest).

본 파일을 운영 model variant 의 single source of truth 로 사용 — Track 1 freeze (`docs/track1_phase0_freeze_20260507.md`) + production spec (`docs/v3_6_plan.md` / `docs/v3_6_summary_report.md`) 의 reference anchor.

## 모델 기술 보고서

- v1 (이론·아키텍처·기본 provenance): `docs/model_technical_report.md` / `.html`
- **v2 (피드백 적용 후속편 / 운영 기준)**: `docs/model_technical_report_v2.md` / `.html` — 2026-04-07~28 콜론30 피드백 24건 → PR #19~#22 적용 변경/실험/실패한 시도 정리. 외부 공유 / 심사 패키지 anchor.
- 처음 읽는 독자는 **v1 → v2** 순서 권고.
