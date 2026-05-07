# VisionAI

## Project Overview
Computer Vision & AI 플랫폼. 이미지/비디오 처리, 모델 학습, 추론 파이프라인을 제공한다.

## Tech Stack
- **Language**: Python 3.11+
- **Core**: PyTorch, torchvision, OpenCV
- **ML Ops**: Weights & Biases, ONNX
- **Data**: Pillow, albumentations, pandas
- **Testing**: pytest, pytest-cov
- **Linting**: ruff, mypy
- **Build**: pyproject.toml (PEP 621)

## Directory Structure
```
VisionAI/
├── src/visionai/       # 메인 소스 코드 (패키지)
├── tests/              # 테스트 코드
├── scripts/            # 유틸리티 스크립트
├── docs/               # 프로젝트 문서
├── data/               # 데이터셋 (git 미추적)
├── checkpoints/        # 모델 체크포인트 (git 미추적)
└── .claude/            # Claude Code 설정
    ├── commands/       # 프로젝트 전용 스킬
    └── agents/         # 프로젝트 전용 에이전트
```

## Coding Conventions
- **Style**: ruff 포매팅 (line-length=99)
- **Type hints**: 모든 public 함수에 타입 힌트 필수
- **Docstrings**: Google style
- **Naming**: snake_case (함수/변수), PascalCase (클래스)
- **Imports**: `from __future__ import annotations` 사용
- **Tests**: `tests/` 디렉토리, `test_` prefix

## Key Patterns
- 설정 관리: dataclass 또는 pydantic BaseModel
- 로깅: `logging` 모듈 (print 금지)
- 경로 처리: `pathlib.Path` 사용 (os.path 지양)
- 데이터 파이프라인: `torch.utils.data.Dataset` / `DataLoader`

## Commands
- `ruff check src/`: 린트 검사
- `ruff format src/`: 코드 포매팅
- `mypy src/`: 타입 체크
- `pytest tests/`: 테스트 실행
- `pytest tests/ --cov=src/visionai`: 커버리지 포함

## Project-Specific Agents
- `/agents:vision-engineer` — 컴퓨터 비전 전문가
- `/agents:ml-engineer` — ML 파이프라인 전문가
- `/agents:data-engineer` — 데이터 엔지니어링 전문가

## Project-Specific Skills
- `/project:train` — 모델 학습 워크플로우
- `/project:eval` — 모델 평가 및 메트릭
- `/project:data` — 데이터셋 준비/검증
- `/project:deploy` — 배포 준비 체크리스트

---

# Behavioral Guidelines (LLM-Specific)

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
