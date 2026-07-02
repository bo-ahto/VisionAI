# Cold Strict Harness Policy

이 문서는 Track6 Cold 실험에서 기본으로 적용할 strict 하네스 기준이다.

## 1. strict Cold 정의

strict Cold는 예측 대상 작가가 운영에서 기존 작가로 확정되지 않은 상황을 뜻한다.

따라서 모델은 작품 정보와 운영 시점에 수집 가능한 비가격성 작가 정보는 사용할 수 있지만, 작가 정체성 자체를 가격 예측 키로 쓰면 안 된다.

## 2. 허용

- 작품 크기, 면적, 비율, 3D 여부
- 매체, 지지체, 크기 bucket
- 비가격성 `artist_meta_*` 피처
- 인터넷 검색에서 만든 검색 문맥 피처
- 전시/갤러리 구조화 피처
- 검색 품질, 동명이인 위험, 수집 성공/실패 flag
- q10/q40/q50/q90 같은 모델 내부 예측값과 그 폭

## 3. 금지

- `artist_key`를 모델 입력 피처로 사용
- `artist_key`를 후처리 lookup key로 사용
- `search_delta_lookup[artist_key]`
- 같은 작가 가격 중앙값, 평균, 분위값
- 같은 작가 면적단가
- 같은 작가 학습 작품 수
- train에 같은 작가가 있는지 여부를 가격 보정에 직접 사용

## 4. 예외

artist_key lookup을 붙여 보는 실험은 가능하지만, strict Cold 실험이 아니다.

이 경우 실험명, 리포트, 요약 문서에 아래를 반드시 표시한다.

```text
non_strict_artist_lookup_diagnostic
strict_cold_compliant = false
신규 작가 Cold 운영 성능으로 인용 금지
```

## 5. 코드 기준

새 Cold 실험 스크립트는 `scripts/track6/cold_experiment_harness.py`를 사용한다.

strict Cold 실험에서는 아래 검사를 통과해야 한다.

```python
assert_strict_cold_features(features, context=...)
assert_no_artist_lookup_postprocess(uses_artist_key_lookup=False, context=...)
```

artist_key lookup 진단 실험은 기본 실행을 막고, 명시적 플래그를 요구한다.

```text
--allow-artist-key-lookup-diagnostic
```

## 6. 현재 해석 정리

- `PP-CMETA1`: strict Cold 하네스에 맞는 운영형 메타/검색 검증
- `PP-CMETA2`: artist_key lookup 효과를 확인한 비엄격 진단
- Cold v0.3 guard+search: 최고 성능 보고 기준이지만, artist_key lookup 가능한 조건을 포함하므로 strict 신규 작가 Cold 성능으로 인용하지 않는다.
