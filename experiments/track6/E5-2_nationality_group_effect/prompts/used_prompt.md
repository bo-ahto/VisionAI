# E5-2 실험 프롬프트

- 실험명: 국적별 가격 차이와 오차 차이 확인
- 목적:
  - 국적 정보가 “있다/없다”만 보는 것이 아니라, 국적값 자체에 따라 가격대와 예측 오차가 어떻게 달라지는지 확인한다.
  - E5-1과 같은 작품 기본 조건을 사용해 국적 효과를 더 구체적으로 본다.

## 통제 조건

- 호수 구간
- 난트 재료 번호
- 난트 도구
- 난트 지지체

## 비교 대상

- 기준 모델:
  - `ln_estimated_ho`
  - `nant_material_idx`
  - `nant_tool`
  - `nant_support`
- 국적 추가 모델:
  - `ln_estimated_ho`
  - `nant_material_idx`
  - `nant_tool`
  - `nant_support`
  - `artist_meta_nationality`
  - `artist_meta_nationality_is_missing`

## 모델

- Warm: `Huber`
- Cold: `Quantile-LAD`
- 이유:
  - E5-1에서 각 scope의 MdAPE가 가장 낮았던 모델을 사용한다.

## 확인 내용

- 국적별 작품 수
- 국적별 실제 가격 중앙값
- 국적별 기준 모델 MdAPE
- 국적별 국적 추가 모델 MdAPE
- 국적 추가 후 MdAPE 개선량
- 같은 조건 묶음 안에서 국적별 가격대가 달라지는지

## 해석 기준

- 국적 추가 후 MdAPE가 낮아지면 해당 국적군에서 예측 개선 신호가 있다고 본다.
- 국적별 표본 수가 작으면 결론을 내리지 않고 참고로만 본다.
- 국적은 원인 변수로 단정하지 않는다.
- 국적은 시장/플랫폼/수집 편향이 섞인 대리 변수일 수 있다.
- `South Korean`, `Korean`, `Korea`, `Republic of Korea`처럼 같은 의미의 국적 표기는 분석 전에 하나로 정리한다.
- 모델 입력과 국적별 결과는 정규화된 `artist_meta_nationality_norm` 기준으로 본다.
