# Track 4 scripts

- Track 4 전용 실험 스크립트를 두는 폴더
- Track 3 스크립트는 수정하지 않고 필요한 경우 참고만 함
- 결과 파일은 `data/track4_*.json` 또는 `data/track4_*.csv`로 저장함

## 클렌징 파이프라인 실행

- 추가 1차 시장 데이터를 반영한 뒤 전체 클렌징을 재실행하려면 아래 명령을 사용함

```bash
python3 scripts/track4/run_cleaning_pipeline.py
```

- 실행 순서
- raw 통합 생성
- 가격 감사
- 크기 감사
- 작가명 감사
- 재료/지지체 감사
- 중복 감사
- 갤러리 메타 감사
- 출처 편향 감사
- `cleaned_v2` 생성
- Warm/Cold split 생성
- 컬럼별 값 정합성 재점검

- 상세 기준 문서
- `docs/track4_cleaning_pipeline.md`
