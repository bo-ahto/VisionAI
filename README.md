# VisionAI

Computer Vision & AI Platform

## Setup

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -e ".[dev]"

# 학습용 의존성 포함
pip install -e ".[dev,train]"
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
