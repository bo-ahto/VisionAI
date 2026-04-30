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
