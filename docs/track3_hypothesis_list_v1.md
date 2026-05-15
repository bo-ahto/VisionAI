# Track 3 가설 설명 문서 v1

- 목적: Track 3에서 검토 중인 가설의 `배경`, `질문`, `현재 판단`, `다음 확인 포인트`를 설명하기 위한 문서
- 역할:
- 이 문서는 `상태판`이 아니라 `설명 문서`임
- 가설의 현재 상태는 별도 표 문서에서 관리함
- 관련 문서:
- 계획서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 가설 요약표
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- 가설 결과 종합표
- [`docs/track3_hypothesis_result_summary.md`](/Users/bo/VisionAI/docs/track3_hypothesis_result_summary.md:1)
- 참고 문서 검토 메모
- [`docs/track3_reference_review_artwork_price_plan_20260513.md`](/Users/bo/VisionAI/docs/track3_reference_review_artwork_price_plan_20260513.md:1)
- 실험 결과 요약표
- [`docs/track3_experiment_results_table.md`](/Users/bo/VisionAI/docs/track3_experiment_results_table.md:1)
- 개별 실험 기록
- [`docs/track3_experiments/README.md`](/Users/bo/VisionAI/docs/track3_experiments/README.md:1)

## 0. 가설 ID 표기 방식

- 이 문서에서는 각 가설을 `H1`, `H2`, `H3`처럼 표기함
- 여기서 `H`는 `Hypothesis`의 약자임
- 즉 `H1`은 첫 번째 가설, `H2`는 두 번째 가설을 뜻함
- 이 표기 방식은 가설 단위와 실제 실행 실험 단위를 구분해서 관리하기 위해 사용함
- 정리
- `H`
- 질문 또는 가설 단위
- `PR`
- 실제 실행 실험 또는 기록 단위

## 0.1 세부 연구 목표 표기 방식

- 각 가설은 궁극적으로 `작품 1건의 정보를 보고 가격을 예측하는 모델 구축`을 달성하기 위한 세부 목표와 연결함
- 세부 목표는 `G1`, `G2`, `G3`처럼 표기함
- 여기서 `G`는 `Goal`의 약자임
- 가설별 세부 목표 매핑은 가설 요약표에서 관리함
- 기준 문서:
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)

| 세부 목표 ID | 세부 목표 | 설명 |
|---|---|---|
| G1 | 기본 예측 가능성 확인 | 작품 구조 정보만으로 가격 예측 baseline이 성립하는지 확인 |
| G2 | Warm 성능 개선 | 이미 학습 데이터에 등장한 작가의 새 작품 가격을 더 잘 예측 |
| G3 | Cold 성능 개선 | 처음 보는 작가의 작품 가격을 더 안정적으로 예측 |
| G4 | 운영 가능 피처 선정 | 실제 서비스 입력에서 다시 만들 수 있는 변수만 남김 |
| G5 | 약점 구간 보완 | 2D/3D, 대형 작품, 특정 재료 등 오차가 큰 구간 개선 |
| G6 | 모델 안정성 확인 | 반복 학습, split 차이, 기준 변경에도 성능이 유지되는지 확인 |
| G7 | 결측/정보량/신뢰도 대응 | 정보 부족 상황, 예측 범위, 신뢰도 표시 가능성 확인 |
| G8 | 최종 후보 정책 결정 | Warm / Cold / Cold 3D 모델을 어떻게 나눠 쓸지 결정 |

## 1. 왜 가설 문서를 따로 두는가

- 계획서는 전체 원칙을 고정하는 문서임
- 가설 문서는 지금 무엇을 질문하고 있는지 설명하는 문서임
- 실험 기록은 실제 실행 결과를 남기는 문서임
- 이 셋을 분리하면 아래 장점이 있음
- 왜 이 실험을 하는지 분명해짐
- 같은 실험을 이름만 바꿔 반복하는 일을 줄일 수 있음
- 실패한 실험도 어떤 질문에 대한 실패였는지 남길 수 있음
- 특정 가설이 틀려도 계획서 전체를 롤백하지 않고 가설 단위로 정리할 수 있음

## 2. Track 3의 기본 순서

- Track 3에서는 아래 순서를 기본으로 함
- 1
- 가설 정리
- 2
- 실험 방법 결정
- 3
- 실험 실행
- 4
- 검증
- 5
- 결론 정리

## 3. 이 문서에서 보는 방법

- 이 문서는 각 가설에 대해 아래 4가지를 설명함
- 배경
- 왜 이 가설이 필요한가
- 세부 목표
- 이 가설이 어떤 연구 목표를 검증하기 위한 것인가
- 질문
- 정확히 무엇을 확인하려는가
- 현재 판단
- 지금까지 실험을 통해 어디까지 알게 되었는가
- 다음 확인 포인트
- 아직 남아 있는 검증 과제는 무엇인가

## 3.1 상위 가설과 후속 가설

- 일부 가설은 큰 목표를 보는 상위 가설로 관리함
- 일부 가설은 그 목표를 개선하기 위한 후속 또는 하위 가설로 관리함
- 예시
- H2는 `작가 정보 없이도 Cold 예측이 가능한가`를 보는 상위 가설임
- H13, H14, H15는 H2에서 남은 Cold 약점 구간을 보완하기 위한 후속 가설임
- 단, H13~H15가 H2와 연결된다고 해서 Cold만 평가한다는 뜻은 아님
- 재료, 크기, 결측처럼 Warm / Cold 모두에서 만들 수 있는 변수는 Warm과 Cold 모두에서 평가함
- Warm에서만 가능한 작가명 또는 작가 이력 피처는 Warm 전용으로 분리해서 해석함

## 4. Track 3 현재 가설

### H1. 크기 정보는 여러 원본 값을 모두 쓰기보다 대표 표현으로 정리하는 것이 더 안정적일 것이다

- 배경
- 작품의 크기는 실제로 하나의 고정된 물리적 특성임
- 그런데 현재 데이터에서는 `width_cm`, `height_cm`, `log_area`, `estimated_ho`처럼 여러 방식으로 표현되고 있음
- 이 값들을 모두 동시에 쓰면 같은 정보를 중복해서 넣고 있을 가능성이 있음
- 질문
- 크기 정보를 여러 방식으로 다 넣는 것보다, 대표 표현으로 줄이는 편이 더 단순하고 안정적인가
- 현재 판단
- 검증 완료
- 크기 변수 단순화는 Cold에서 거의 비슷했지만 전면 채택할 만큼 확실한 우위는 아니었음
- Warm confirm에서 대표 표현이 악화되어 전면 단순화는 기각함
- 현재 결론은 `width_cm`, `height_cm`, `log_area`, `estimated_ho`를 모두 쓰는 `V0_all` 유지임
- 다음 확인 포인트
- 추가 확인 없음
- 신규 크기 피처를 만들기 전까지 H1은 종결함

### H2. 작가 정보 없이도 작품 자체 정보만으로 Cold 예측이 가능할 것이다

- 배경
- Cold는 학습에 없던 신규 작가를 다루는 상황임
- 따라서 작가명이나 작가별 이력에 직접 의존하는 구조는 사용할 수 없음
- 이 가설은 Cold 예측 가능성을 확인하는 상위 가설임
- H13, H14, H15는 H2 이후 남은 약점 구간을 보완하기 위한 후속 가설로 연결함
- 질문
- 재료, 바탕, 크기, 깊이, 방향성 같은 구조 정보만으로도 충분히 의미 있는 Cold baseline을 만들 수 있는가
- 현재 판단
- 검증 완료
- 가능함
- 실제로 Cold에서는 작가 비의존 구조를 가진 robust 선형 계열이 가장 안정적이었음
- 다만 특정 source, medium, 대형 작품 구간 등 약점 slice는 남아 있음
- 다음 확인 포인트
- 구조 정보만으로 가능한 baseline은 확보됐다고 볼 수 있음
- 앞으로는 baseline 자체를 의심하기보다 약점 slice를 어떻게 제한적으로 보완할지 보는 단계에 가까움
- 약점 보완은 H7/H8/H13/H14/H15에서 별도로 다룸
- H13~H15는 H2의 후속 가설로 연결하되, 공통 피처는 Warm도 함께 확인함

### H3. Warm에서는 작가 정보를 포함할 때 성능이 유의미하게 좋아질 것이다

- 배경
- Warm은 이미 학습에 등장한 작가의 새 작품을 예측하는 상황임
- 따라서 작가 관련 정보가 가격 형성에 실질적인 도움이 될 가능성이 큼
- 질문
- `artist_name_ko`, `artist_works_log` 같은 정보가 Warm 성능 개선을 실제로 만드는가
- 현재 판단
- 검증 완료
- 그렇다고 보는 근거가 충분함
- Warm에서는 선형보다 트리 모델이 강했고
- `artist_works_log` 계열도 유지 가치가 확인됐음
- release split 직접 비교에서도 작가 정보 포함 모델이 작가 정보 제외 모델보다 좋았음
- 다음 확인 포인트
- Warm에서 작가 정보 자체의 필요성은 종결함
- 작가 DB 기반 추가 피처는 H10에서 별도로 검증함

### H4. 운영에서 다시 계산 가능한 파생 피처는 기본 피처 대비 추가 성능 개선을 줄 수 있을 것이다

- 배경
- 기본 변수만으로는 작품의 구조, 비율, 형태적 특성을 충분히 설명하지 못할 수 있음
- 그래서 `aspect_ratio`, `medium_ho_bucket`, `medium_support_combo` 같은 파생 피처를 검토해 왔음
- 질문
- 운영에서 다시 계산 가능한 파생 피처가 실제로 반복 가능한 개선을 주는가
- 현재 판단
- 검증 완료
- 일부 신호는 있었지만, 운영 채택까지 갈 만큼 강한 승자는 많지 않았음
- Warm에서는 `artist_works_log` 계열이 상대적으로 의미 있었고
- Cold에서는 `source`를 빼면 뚜렷한 승자가 약했음
- `medium_support_combo`, `max_side_cm`, `is_square_like`, `log_area_depth`는 현재 기준 채택 근거가 약함
- 다음 확인 포인트
- H4 자체는 종결함
- 신규 파생 피처는 H13/H14/H15처럼 별도 가설로만 추가 검증함

### H5. Warm에서는 비선형 트리 모델이 선형 계열보다 더 우세할 것이다

- 배경
- Warm은 작가 정보와 작품 정보가 함께 들어오므로 관계가 더 복잡할 가능성이 큼
- 질문
- Warm에서는 LightGBM 같은 비선형 트리 모델이 선형 계열보다 일관되게 우세한가
- 현재 판단
- 그렇다고 볼 수 있음
- Warm에서는 `tuned LightGBM`이 반복적으로 가장 좋은 성능을 보였고
- CatBoost와 XGBoost는 현재 기준에서 열세였음
- 다음 확인 포인트
- Warm에서 트리 모델 우세 자체는 더 크게 의심할 필요가 적음
- 앞으로는 Warm 모델 구조를 바꾸기보다 feature quality와 운영 안정성을 다듬는 쪽이 더 중요함

### H6. Cold에서는 복잡한 비선형 모델보다 robust 선형 계열이 더 안정적일 것이다

- 배경
- Cold는 작가 정보 없이 구조적 피처 중심으로 예측해야 함
- 이 경우 복잡한 비선형 모델이 항상 이득을 주지는 않을 수 있음
- 질문
- Cold에서는 LAD / Quantile / Huber 같은 robust 선형 계열이 트리 모델보다 더 안정적인가
- 현재 판단
- 그렇다고 보는 근거가 충분함
- 실제 재현 결과에서도 Cold는 LightGBM 튜닝까지 포함해 선형 계열을 이기지 못했음
- 다음 확인 포인트
- Cold 전체 모델을 트리 쪽으로 다시 크게 바꾸는 우선순위는 낮음
- 앞으로는 선형 baseline을 유지한 채 제한적 보완 구조를 검토하는 것이 더 적절함

### H7. 2D / 3D 분기는 전체 모델 교체보다 특정 약점 구간 보완용으로 더 적합할 것이다

- 배경
- Cold 약점 분석을 보면 모든 구간이 아니라 일부 slice에서 성능이 특히 약함
- depth 관련 실험에서는 `Cold 2D` 쪽에서만 반복적으로 개선 신호가 나타남
- 질문
- `2D / 3D` 분기를 전체 모델 교체로 쓰기보다, 특정 약점 구간 보완용으로 제한적으로 쓰는 것이 더 적절한가
- 현재 판단
- 검증 완료
- mini 실험에서는 그 가능성이 있었음
- `PR17`, `PR18`, `PR19`를 같이 보면
- `Cold 2D`는 개선 신호가 있지만
- `Cold 3D`와 `Warm`까지 포함하면 전면 채택 근거는 약함
- 후속 H8 release split 확인에서는 `Cold 2D` 한정 fallback도 악화됨
- 다음 확인 포인트
- 현재 2D / 3D 분기 실험선은 운영 채택하지 않음
- 추가 모델 분기보다 H13~H15의 공통 피처 기반 약점 보완으로 이동함

### H8. Cold 2D 한정 fallback은 전체 Cold 모델 교체보다 더 나은 비용 대비 효과를 낼 것이다

- 배경
- 현재까지의 depth / branch 실험은 전면 교체보다 제한적 적용이 더 현실적임을 시사함
- 질문
- `Cold 2D`에만 별도 expert 또는 fallback을 적용하고, 나머지는 기존 `Cold = LAD`를 유지하면 더 효율적인가
- 현재 판단
- 검증 완료
- release split 기준으로 악화됨
- 전체 Cold `median APE 0.3207 -> 0.3267`
- Cold 2D `median APE 0.3871 -> 0.4735`
- 따라서 Cold 2D 한정 fallback은 채택하지 않음
- 다음 확인 포인트
- 추가 확인 없음
- H8은 중단함

### H9. 일부 정보를 의도적으로 가리고 학습한 모델이 결측 상황에서 더 잘 버틸 것이다

- 배경
- 실제 예측 대상 작품에는 작가명, 재료, 제작연도, 이미지 같은 정보가 빠져 있을 수 있음
- 현재 Track 3는 결측 처리 자체는 다루고 있지만, `의도적 정보 제거 학습`은 아직 본격적으로 검증하지 않았음
- 질문
- 학습 단계에서 일부 정보를 일부러 가린 모델이, 실제 결측 상황 test에서 성능 저하를 덜 보이는가
- 현재 판단
- 검증 완료
- 크기 결측 상황에서는 일부 완화 효과가 있음
- 하지만 clean 성능과 재료 결측 성능이 악화되어 기본 학습 방식으로 채택하지 않음
- 다음 확인 포인트
- 전체 학습에 마스킹을 섞는 방식은 중단함
- 결측 대응은 별도 fallback 또는 입력 품질 경고 방식으로 검토함
- H15는 실제 운영 결측 데이터 확보 후 재검증함

### H10. 작가명 자체보다 거래 이력 기반 구조화 피처가 Warm에서 더 설명 가능하고 안정적일 것이다

- 배경
- 현재 Warm에서는 작가 정보가 중요한 것이 확인됐음
- 하지만 단순 `artist_name_ko`보다 구조화된 거래 이력 피처가 더 설명 가능하고 운영적으로 유리할 수 있음
- 질문
- 작가명 자체보다 `과거 중앙 거래가`, `거래 횟수`, `최근 거래 수준` 같은 구조화 피처가 Warm에서 더 좋은가
- 현재 판단
- 검증 완료
- 작가 이력 피처가 작가명 단독보다 Warm 성능을 크게 개선함
- `artist_name_ko + 작가 이력 피처` 조합이 가장 좋음
- 단, 현재 데이터에는 거래일이 없어 temporal-safe 검증은 아직 아님
- 다음 확인 포인트
- 거래일 이전 정보만 사용한 작가 이력 피처를 만들 수 있는지 확인
- H12 residual 구조에서 작가 기본 가격대와 작품별 편차를 분리해 검증함

### H11. 정보량에 따라 단일 가격보다 가격 범위와 신뢰도를 함께 주는 방식이 더 실용적일 것이다

- 배경
- 현재 Track 3는 point prediction 중심으로 평가하고 있음
- 하지만 운영에서는 정보가 부족할수록 더 넓은 범위와 낮은 신뢰도를 주는 방식이 더 정직할 수 있음
- 질문
- 정보량에 따라 예측 범위 폭과 신뢰도를 함께 제시하는 구조가 더 실용적인가
- 현재 판단
- 검증 완료
- 가격 범위 출력은 보조 정보로 의미가 있음
- 다만 Warm은 목표 coverage보다 실제 coverage가 낮고, Cold는 구간 폭이 너무 넓음
- 현재 방식은 바로 채택하지 않고 calibration 보완 후 재검토함
- 다음 확인 포인트
- Warm / Cold별 range calibration
- 가격대별 또는 작가 이력 정보량별 calibration
- 신뢰도 등급과 실제 coverage 관계 확인

### H12. 작가 기본 가격대를 먼저 추정하고 작품별 편차를 따로 예측하는 2단계 구조가 일부 Warm 상황에서 더 설명력 있을 것이다

- 배경
- 같은 작가 안에서도 작품별 가격 차이가 존재함
- 작가의 기본 가격대와 작품별 편차를 분리하면 설명력이 올라갈 수 있다는 아이디어가 있음
- 질문
- `작가 기본 가격대`와 `작품별 편차`를 분리해서 보는 2단계 구조가 일부 Warm 상황에서 더 해석 가능하고 유효한가
- 현재 판단
- 검증 완료
- 잔차 구조는 직접 작가 이력 모델과 거의 비슷한 성능을 냄
- 다만 직접 모델을 이기지는 못해 최종 성능 모델로는 보류함
- 설명용 보조 구조로는 가치가 있음
- 다음 확인 포인트
- 거래일 이전 작가 기본 가격대 정의
- H10 직접 모델과 함께 temporal-safe 방식으로 재검증

### H13. 재료를 더 세분화한 피처가 Cold 정확도를 개선할 것이다

- 배경
- 현재 `medium_category`는 작품 재료를 설명하는 핵심 변수임
- 하지만 `mixed`, `other`처럼 넓게 묶인 구간은 Cold 약점으로 반복 확인됐음
- H2 이후 남은 Cold 약점 구간을 보완하기 위한 후속 가설임
- 질문
- 재료를 더 세분화하거나 재료 특성을 별도 flag로 만들면 Cold 예측 정확도가 개선되는가
- 현재 판단
- 검증 완료
- 단순 재료 flag와 재료 희소도 bucket은 Cold를 개선하지 못함
- Warm에서는 오히려 악화됨
- 현재 방식의 재료 세분화 피처는 채택하지 않음
- 다음 확인 포인트
- 추가 확인 없음
- 재료 정보는 기존 `medium_category`, `medium_ho_bucket`을 유지함

### H14. 크기와 재료의 조합 효과가 단독 피처보다 가격을 더 잘 설명할 것이다

- 배경
- 같은 크기라도 재료에 따라 가격 구조가 다를 수 있음
- 예를 들어 큰 회화와 큰 판화는 시장 가격 의미가 다를 수 있음
- H2 이후 남은 Cold 약점 구간을 보완하기 위한 후속 가설이지만, 조합 피처는 Warm에도 영향을 줄 수 있음
- 질문
- 크기 피처와 재료 피처를 조합한 변수가 단독 변수보다 Warm / Cold 성능을 더 안정적으로 개선하는가
- 현재 판단
- 검증 완료
- 조합 flag는 Warm에서 소폭 개선됐지만 Cold에서는 개선되지 않음
- `medium_size_bucket`은 기존 `medium_ho_bucket` 대비 추가 가치가 거의 없음
- H14의 목적은 Cold 약점 보완이므로 현재 방식의 조합 피처는 채택하지 않음
- 다음 확인 포인트
- 추가 확인 없음
- 기존 `medium_ho_bucket`을 유지함

### H15. 결측 패턴 자체가 신뢰도와 가격 오차를 설명할 것이다

- 배경
- 실제 운영 입력에서는 작가명, 재료, 제작연도, 이미지 등 일부 정보가 빠질 수 있음
- 결측은 단순한 결함이 아니라 예측 신뢰도와 오차 크기를 설명하는 신호일 수 있음
- H2 이후 Cold 약점 보완과도 연결되지만, 정보량 피처는 Warm / Cold 모두에 영향을 줄 수 있음
- 질문
- 결측 개수와 결측 패턴을 피처로 넣으면 예측 정확도 또는 신뢰도 판단이 개선되는가
- 현재 판단
- 보류
- 현재 release split 기준 핵심 입력 변수의 결측이 0건임
- `missing_count`, `info_completeness_score` 같은 피처를 만들어도 값이 모두 같아져 학습 신호가 없음
- 따라서 현재 데이터로는 H15를 모델 실험으로 검증할 수 없음
- H9가 `정보를 일부러 가리고 학습하는 가설`이라면, H15는 `현재 입력의 정보량 자체를 피처화하는 가설`임
- 다음 확인 포인트
- 운영 입력 데이터에서 실제 결측 사례가 생기면 재검증함
- H9 masking 실험으로 결측 상황을 인위적으로 만든 뒤 보조 검증함

### H16. 작가 이력 피처는 거래일 기준으로 다시 계산할 수 있어야 운영 피처로 채택 가능하다

- 배경
- H10/H17에서 작가 이력 피처의 Warm 개선 효과가 큼
- 하지만 작가 이력은 예측 시점 이후 정보를 쓰면 누수가 됨
- 질문
- 현재 release split만으로 작가 이력 피처를 거래일 기준으로 재계산할 수 있는가
- 현재 판단
- 보류
- 현재 release split에는 거래일, 판매일, 등록일 역할을 하는 날짜 컬럼이 없음
- temporal-safe 재검증은 현재 데이터만으로 불가능함
- 다음 확인 포인트
- 원천 데이터에 거래일 또는 등록일 컬럼을 추가할 수 있는지 확인
- 날짜 컬럼 확보 후 H10/H12/H17을 다시 검증함

### H17. 작가 이력 피처의 Warm 개선 효과는 반복 학습에서도 안정적으로 유지될 것이다

- 배경
- H10 단일 실행에서 작가 이력 피처가 크게 개선됐음
- 단일 seed 결과가 우연인지 확인할 필요가 있음
- 질문
- seed를 바꿔도 작가 이력 피처의 개선 효과가 유지되는가
- 현재 판단
- 검증 완료
- 3개 seed 평균 기준 `artist_name_ko` 단독은 `0.2363`
- `artist_name_ko + 작가 이력 피처`는 `0.1147`
- 반복 학습에서도 개선 효과가 안정적으로 유지됨
- 다음 확인 포인트
- H16 조건이 해결되면 temporal-safe 방식으로 같은 안정성 검증을 다시 수행함

### H18. 예측 구간 calibration quantile을 조정하면 Warm coverage 부족을 줄일 수 있다

- 배경
- H11에서 Warm 예측 구간은 목표 coverage보다 낮았음
- Cold는 coverage는 충분했지만 구간 폭이 너무 넓었음
- 질문
- calibration quantile을 조정하면 Warm coverage 부족을 보완할 수 있는가
- 현재 판단
- 검증 완료
- Warm 80% 구간은 q 0.90을 쓰면 coverage `0.810`으로 목표를 넘김
- Warm 90% 구간은 q 0.975가 필요하지만 구간 폭이 커짐
- Cold는 q 0.80에서도 coverage `0.855`지만 구간 폭이 큼
- 다음 확인 포인트
- Warm은 80% 보조 구간 중심으로 검토
- Cold는 넓은 가격 범위보다 신뢰도 낮음 또는 경고 문구로 표현하는 방안 검토
- 최종 모델 확정 후 calibration을 다시 수행함

### H19. 호수 구간을 더 세분화하면 Warm/Cold 성능이 개선될 것이다

- 배경
- `estimated_ho`는 이미 핵심 크기 피처로 사용 중임
- 하지만 호수와 가격의 관계는 선형이 아닐 수 있음
- 질문
- `estimated_ho`를 더 세밀한 구간으로 나누면 Warm / Cold 성능이 개선되는가
- 현재 판단
- 검증 완료
- 연구 방법
- `ho_bucket_refined` 생성
- 예: `0-3`, `4-6`, `8-10`, `12-20`, `25-50`, `60+`
- 기존 `estimated_ho`, 기존 `medium_ho_bucket` 유지 여부를 비교함
- Warm / Cold 모두 평가함
- 검증 결과
- 관련 실험: `H19_H22_ho_feature_ablation`
- 상세 기록: [`2026-05-13_h19_h22_ho_feature_ablation.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h19_h22_ho_feature_ablation.md:1)
- `ho_bucket_refined` 추가 시 Cold median APE `0.3207 -> 0.3184`, Warm median APE `0.2056 -> 0.2039`
- 현재 판단
- 검증 완료
- 채택 후보

### H20. 큰 호수/초대형 호수 여부는 가격 예측에 별도 신호를 줄 것이다

- 배경
- 대형 작품은 일반 크기 작품과 가격 구조가 다를 수 있음
- 질문
- `is_large_ho`, `is_extra_large_ho` 같은 극단 크기 피처가 성능을 개선하는가
- 현재 판단
- 검증 완료
- 연구 방법
- `estimated_ho >= 50`
- `estimated_ho >= 100`
- 같은 기준으로 대형/초대형 flag를 추가해 Warm / Cold 성능과 큰 오차 변화를 확인함
- 검증 결과
- 관련 실험: `H19_H22_ho_feature_ablation`
- 상세 기록: [`2026-05-13_h19_h22_ho_feature_ablation.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h19_h22_ho_feature_ablation.md:1)
- 대형/초대형 flag 추가 시 Cold median APE `0.3207 -> 0.3178`
- Warm은 `0.2056 -> 0.2056`으로 변화 없음
- 현재 판단
- 검증 완료
- Cold 채택 후보

### H21. 실제 면적과 추정 호수의 불일치 정도가 가격 오차를 설명할 것이다

- 배경
- 같은 호수라도 실제 입력된 가로/세로 면적과 어긋날 수 있음
- 호수 추정값과 실제 면적이 일관되지 않으면 모델이 혼란스러울 수 있음
- 질문
- `estimated_ho`와 `log_area`의 불일치 정도를 피처로 넣으면 성능 또는 오차 설명력이 개선되는가
- 현재 판단
- 검증 완료
- 연구 방법
- `area_per_ho`
- `ho_per_area`
- `ho_size_consistency`
- 위 피처를 추가해 Warm / Cold 전체 성능과 큰 오차 작품 변화를 확인함
- 검증 결과
- 관련 실험: `H19_H22_ho_feature_ablation`
- 상세 기록: [`2026-05-13_h19_h22_ho_feature_ablation.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h19_h22_ho_feature_ablation.md:1)
- 일관성 피처 단독 추가 시 Cold median APE `0.3207 -> 0.3370`으로 악화
- Warm은 `0.2056 -> 0.2047`로 소폭 개선
- 현재 판단
- 검증 완료
- 단독 채택 보류
- 전체 조합에서는 개선에 기여했을 가능성이 있어 H30 slice 분석에서 재확인

### H22. 호수는 선형값보다 로그값이나 구간값으로 쓰는 것이 더 안정적일 것이다

- 배경
- 큰 호수의 영향이 선형값으로는 과도하게 반영될 수 있음
- 질문
- `estimated_ho` 원값보다 `log_ho` 또는 `ho_bucket_refined`가 더 안정적인가
- 현재 판단
- 검증 완료
- 연구 방법
- V0: 기존 `estimated_ho`
- V1: `log_ho`
- V2: `ho_bucket_refined`
- V3: `log_ho + ho_bucket_refined`
- Warm / Cold median APE와 반복 안정성을 비교함
- 검증 결과
- 관련 실험: `H19_H22_ho_feature_ablation`
- 상세 기록: [`2026-05-13_h19_h22_ho_feature_ablation.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h19_h22_ho_feature_ablation.md:1)
- `log_ho` 단순 추가는 Cold를 `0.3207 -> 0.3364`로 악화
- `estimated_ho`를 `log_ho + ho_bucket_refined`로 대체하면 Cold `0.3195`, Warm `0.2039`로 성능 유지 또는 소폭 개선
- 전체 호수 피처 조합은 Cold `0.3163`, Warm `0.1958`로 가장 좋음
- 현재 판단
- 검증 완료
- 대체 표현 가능성 확인
- 최종 채택 전 반복 안정성 확인 필요

### H23. 크기 구간/극단 크기 피처가 Warm/Cold 성능을 개선할 것이다

- 배경
- 작품 크기는 가격에 중요하지만 연속값만으로는 구간 효과를 놓칠 수 있음
- 질문
- 소형, 중형, 대형, 초대형 같은 크기 구간 피처가 성능을 개선하는가
- 현재 판단
- 검증 완료
- 중단
- 연구 방법
- `size_bucket`
- `is_tiny_work`
- `is_very_large`
- `log_area` 기준 또는 `estimated_ho` 기준으로 구간화해 Warm / Cold를 함께 평가함
- 검증 결과
- 관련 실험: `H23_H25_size_3d_relative_ablation`
- 상세 기록: [`2026-05-13_h23_h25_size_3d_relative_ablation.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h23_h25_size_3d_relative_ablation.md:1)
- Cold median APE `0.3163 -> 0.3173`
- Warm median APE `0.1958 -> 0.2080`
- 크기 구간 피처는 Warm / Cold 모두 개선하지 못함

### H24. 3D 작품은 면적보다 부피/긴 변 피처가 더 설명력이 있을 것이다

- 배경
- 3D 작품은 2D 면적보다 부피, 깊이, 가장 긴 변이 가격과 더 관련 있을 수 있음
- H8에서 2D/3D 모델 분기는 실패했지만, 피처 추가 방식은 별도로 검토할 수 있음
- 질문
- `volume_log`, `max_side_log`, `min_side_log`가 3D 작품 slice에서 성능을 개선하는가
- 현재 판단
- 검증 완료
- Cold 채택 후보
- 연구 방법
- 모델을 분기하지 않고 피처만 추가함
- 전체 Warm / Cold와 3D slice를 함께 확인함
- 검증 결과
- 관련 실험: `H23_H25_size_3d_relative_ablation`
- 상세 기록: [`2026-05-13_h23_h25_size_3d_relative_ablation.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h23_h25_size_3d_relative_ablation.md:1)
- Cold median APE `0.3163 -> 0.2824`
- Cold 3D slice `0.2936 -> 0.2364`
- Warm median APE `0.1958 -> 0.1993`
- Cold 개선이 크지만 Warm은 소폭 악화되어 Cold 전용 후보로 봄

### H25. 같은 재료 안에서의 상대적 크기 순위가 절대 크기보다 가격 설명력이 있을 것이다

- 배경
- 같은 30호라도 재료에 따라 큰 작품인지 작은 작품인지 의미가 다를 수 있음
- 질문
- 재료별 상대 크기 순위가 절대 크기보다 가격 설명에 도움이 되는가
- 현재 판단
- 검증 완료
- Cold 채택 후보
- 연구 방법
- train 기준으로 `medium_area_percentile`, `medium_ho_percentile` 계산
- test에는 train 기준 분포를 적용함
- 데이터 새어 나감 방지를 위해 test 분포는 사용하지 않음
- 검증 결과
- 관련 실험: `H23_H25_size_3d_relative_ablation`
- 상세 기록: [`2026-05-13_h23_h25_size_3d_relative_ablation.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h23_h25_size_3d_relative_ablation.md:1)
- Cold median APE `0.3163 -> 0.3022`
- Warm median APE `0.1958 -> 0.2017`
- Cold에는 도움이 되지만 Warm은 악화되어 Cold 전용 후보로 봄

### H26. 크기 관련 피처가 중복되어 있어 일부를 제거하면 성능이 유지되거나 안정성이 좋아질 것이다

- 배경
- 현재 크기 관련 피처가 `depth_cm`, `width_cm`, `height_cm`, `log_area`, `estimated_ho` 등으로 많음
- 서로 같은 정보를 반복해서 담고 있을 수 있음
- 질문
- 일부 크기 피처를 제거해도 Warm / Cold 성능이 유지되는가
- 현재 판단
- 검증 완료
- `width_cm`, `height_cm` 제거안은 Cold median APE가 `0.3237 -> 0.3207`로 소폭 개선됨
- Warm median APE는 `0.2045 -> 0.2056`으로 거의 유지됨
- 따라서 `width_cm`, `height_cm`는 운영 단순화 관점에서 제거 후보로 볼 수 있음
- 연구 방법
- 전체 크기 피처 사용안과 축소안을 비교함
- 축소 A: `log_area + estimated_ho + depth_cm`
- 축소 B: `log_area + depth_cm`
- 축소 C: `estimated_ho + depth_cm`
- 성능 악화가 작고 안정성이 좋아지면 운영 단순화 후보로 봄
- 검증 결과
- 관련 실험: `H26_H28_size_feature_reduction`
- 상세 기록: [`2026-05-13_h26_h28_size_feature_reduction.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h26_h28_size_feature_reduction.md:1)
- 후속 H19~H22는 이 축소 기준으로 진행했고, H29에서 최종 공통 피처 여부를 정리함

### H27. `estimated_ho`와 `log_area` 중 하나만 남겨도 성능 차이가 크지 않을 것이다

- 배경
- `estimated_ho`와 `log_area`는 모두 크기를 설명함
- 두 피처가 중복이면 운영 입력을 단순화할 수 있음
- 질문
- `estimated_ho` 또는 `log_area` 중 하나만 사용해도 성능이 유지되는가
- 현재 판단
- 검증 완료
- `estimated_ho`만 남기는 안은 Cold median APE가 `0.3237 -> 0.4071`로 크게 악화되어 기각함
- `log_area` 중심 축소안은 Cold는 거의 유지되지만 Warm이 소폭 악화됨
- 둘 중 하나만 남긴다면 `log_area`가 더 안정적이지만, 현재 기준에서는 `estimated_ho`도 완전히 제거하지 않음
- 연구 방법
- V0: 둘 다 사용
- V1: `estimated_ho`만 사용
- V2: `log_area`만 사용
- Warm / Cold 성능 악화가 `0.005~0.01` 이하인지 확인함
- 검증 결과
- 관련 실험: `H26_H28_size_feature_reduction`
- 상세 기록: [`2026-05-13_h26_h28_size_feature_reduction.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h26_h28_size_feature_reduction.md:1)
- 호수 표현 자체의 개선 가능성은 H19~H22에서 별도 검증했고, H22와 함께 최종 표현을 정리함

### H28. `width_cm`, `height_cm`는 `log_area`, `aspect_ratio`로 대체 가능할 것이다

- 배경
- 작품 크기는 고정된 형태이므로 가로/세로 원값보다 면적과 비율로 표현하는 것이 더 안정적일 수 있음
- 질문
- `width_cm`, `height_cm`를 제거하고 `log_area`, `aspect_ratio`만 써도 성능이 유지되는가
- 현재 판단
- 검증 완료
- `width_cm`, `height_cm` 제거 후 `log_area + aspect_ratio`를 유지하면 Cold는 소폭 개선되고 Warm은 거의 유지됨
- 반대로 `aspect_ratio`까지 제거하면 Warm median APE가 `0.2045 -> 0.2223`으로 악화됨
- 따라서 `width_cm`, `height_cm`는 대체 가능하지만 `aspect_ratio`는 유지 가치가 있음
- 연구 방법
- 원본 크기 피처와 파생 크기 피처를 비교함
- V0: `width_cm + height_cm + log_area`
- V1: `log_area + aspect_ratio`
- V2: `log_area`만
- 검증 결과
- 관련 실험: `H26_H28_size_feature_reduction`
- 상세 기록: [`2026-05-13_h26_h28_size_feature_reduction.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-13_h26_h28_size_feature_reduction.md:1)

### H29. Warm과 Cold에서 필요한 크기/호수 피처 구성이 다를 것이다

- 배경
- Warm은 작가 이력 피처가 강하고 Cold는 작품 구조 피처 의존도가 높음
- 따라서 같은 파생 피처라도 Warm과 Cold에서 효과가 다를 수 있음
- 질문
- H19~H28의 피처 채택 기준을 Warm / Cold에서 다르게 가져가야 하는가
- 현재 판단
- 검증 완료
- 연구 방법
- H19~H28 결과를 종합해 Warm 전용, Cold 전용, 공통 유지 피처로 분류함
- 검증 결과
- 관련 실험: `H29_H30_feature_policy_slice_analysis`
- 상세 기록: [`2026-05-14_h29_h30_feature_policy_slice_analysis.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h29_h30_feature_policy_slice_analysis.md:1)
- Warm 최적 후보는 `V0_warm_policy_ho_enhanced`, Warm median APE `0.1958`
- Cold 최적 후보는 `V1_cold_policy_3d`, Cold median APE `0.2824`
- Cold 3D 피처를 Warm에 넣으면 Warm median APE가 `0.1958 -> 0.1993`으로 소폭 악화됨
- 결론
- Warm / Cold 피처 정책은 분리하는 것이 맞음
- 단, Cold 3D 피처는 Cold 2D를 악화시키므로 Cold 전체가 아니라 조건부 적용으로 재검증 필요

### H30. 파생 피처는 전체 성능보다 약점 slice에서만 개선될 수 있다

- 배경
- 새 피처가 전체 median APE를 크게 개선하지 않아도 특정 구간에서는 의미 있을 수 있음
- 질문
- 호수/크기 파생 피처가 `mixed`, `other`, 대형, 3D, Cold 2D 같은 약점 구간을 개선하는가
- 현재 판단
- 검증 완료
- 연구 방법
- 전체 Warm / Cold 성능과 함께 slice별 median APE를 기록함
- 전체 성능 악화가 작고 특정 약점 slice가 개선되면 보조 피처 후보로 분류함
- 검증 결과
- 관련 실험: `H29_H30_feature_policy_slice_analysis`
- 상세 기록: [`2026-05-14_h29_h30_feature_policy_slice_analysis.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h29_h30_feature_policy_slice_analysis.md:1)
- Cold 3D는 `0.2936 -> 0.2364`로 개선
- Cold 대형 호수는 `0.5130 -> 0.4448`로 개선
- Cold 초대형 호수는 `0.7432 -> 0.5522`로 개선
- Cold 2D는 `0.3767 -> 0.6071`로 악화
- 결론
- 개선은 전체에 고르게 나타나지 않고 특정 slice에 집중됨
- 따라서 slice 안전장치 없이 전체 모델에 일괄 적용하면 위험함

### H31. H17 Warm champion에 호수/3D 피처를 추가하면 Warm 성능이 더 좋아질 것이다

- 배경
- H19-H30의 Warm 기준값은 `0.1958`로, H17 안정성 검증 후보 `0.1147`보다 약함
- 따라서 H19-H30에서 좋아 보인 호수/3D 피처가 실제 Warm 최적 후보 위에서도 효과가 있는지 다시 확인해야 함
- 질문
- H17 Warm champion에 호수/3D 파생 피처를 추가하면 Warm median APE가 더 낮아지는가
- 현재 판단
- 검증 완료
- `H17 champion 0.1147`
- `H17 + 호수 전체 + 3D 피처 0.1090`
- 연구 방법
- H17과 같은 3개 seed LightGBM 안정성 평가를 사용함
- H17 기준 피처에 호수 세분화, 대형 호수 flag, 호수-면적 관계, 3D 부피/긴 변 피처를 순서대로 추가함
- 검증 결과
- 관련 실험: `H31_warm_champion_feature_retest`
- 상세 기록: [`2026-05-14_h31_warm_champion_feature_retest.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h31_warm_champion_feature_retest.md:1)
- 결론
- Warm 후보는 H17 단독보다 H31 `V5_plus_all_ho_and_3d`가 더 좋음
- 단, PR7 탐색 최고 기록 `0.1031`은 별도 재확인이 필요함

### H32. Cold 3D 피처는 전체 적용보다 3D 작품에만 조건부 적용하는 것이 더 안정적일 것이다

- 배경
- H29-H30에서 Cold 3D 피처는 전체 Cold를 개선했지만 Cold 2D를 크게 악화시킴
- 전체 모델 교체보다 3D 작품에만 다른 모델을 쓰는 정책이 더 안전할 수 있음
- 질문
- 2D에는 기존 Cold 모델을 쓰고, 3D에만 3D 피처 모델을 쓰면 전체 Cold 성능이 개선되는가
- 현재 판단
- 검증 완료
- 전체 Cold `0.3163 -> 0.2786`
- Cold 2D `0.3767 -> 0.3767`
- Cold 3D `0.2936 -> 0.2364`
- 연구 방법
- 기본 Cold 모델과 3D 피처 Cold 모델을 각각 학습함
- 최종 예측에서는 2D 작품은 기본 모델 예측, 3D 작품은 3D 모델 예측을 사용함
- 검증 결과
- 관련 실험: `H32_cold_3d_conditional_fallback`
- 상세 기록: [`2026-05-14_h32_cold_3d_conditional_fallback.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h32_cold_3d_conditional_fallback.md:1)
- 결론
- Cold 최적 후보는 단일 3D 피처 모델이 아니라 조건부 fallback 정책임
- production 후보 반영 검토가 필요함

### H33. PR7 Warm 최고 탐색 기록은 release split / 운영 가능 피처 기준에서도 유지될 것이다

- 배경
- PR7 탐색 실험의 Warm 최고 기록은 `0.1031`로 가장 낮았음
- 하지만 PR7은 dev/CV 기준 탐색 결과였고, 현재 release split 최종 후보와 직접 비교되지 않았음
- 질문
- PR7의 운영 가능 피처만 사용해도 release split에서 H31 Warm 후보를 이길 수 있는가
- 현재 판단
- 검증 완료
- PR7 운영 가능 피처 최고 `0.2251`
- H31 현재 Warm 후보 `0.1090`
- 연구 방법
- release split의 `track3_train.csv`, `track3_test_warm.csv`를 사용함
- `source_platform`은 release split에 없고 운영 입력도 어려워 제외함
- `medium_ho_bucket`, `artist_works_log`, `aspect_ratio`를 PR7 계열 피처로 재검증함
- 검증 결과
- 관련 실험: `H33_pr7_release_warm_reconfirm`
- 상세 기록: [`2026-05-14_h33_pr7_release_warm_reconfirm.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h33_pr7_release_warm_reconfirm.md:1)
- 결론
- PR7 탐색 최고 기록 `0.1031`은 현재 release split 최종 성능으로 보지 않음
- Warm 최종 후보는 H31 `V5_plus_all_ho_and_3d`를 유지함

### H34. Cold 3D 조건부 모델은 모든 3D 작품보다 특정 3D 구간에서 효과가 클 것이다

- 배경
- H32에서 Cold 3D 조건부 fallback은 전체 Cold를 개선했음
- 다만 3D 작품 내부에서도 크기나 부피에 따라 효과가 다를 수 있음
- 질문
- 3D fallback은 모든 3D 작품에 적용해도 되는가
- 아니면 특정 3D 구간에만 더 효과적인가
- 현재 판단
- 검증 완료
- 3D 전체는 개선됨
- 중간 부피 3D 구간은 악화 신호가 있음
- 연구 방법
- Cold 3D 작품을 부피, 호수, 대형 여부 기준으로 나눠 H32 base와 fallback을 비교함
- 검증 결과
- 관련 실험: `H34_H43_followup_validation`
- 상세 기록: [`2026-05-14_h34_h43_followup_validation.md`](/Users/bo/VisionAI/docs/track3_experiments/2026-05-14_h34_h43_followup_validation.md:1)
- 결론
- H32 조건부 fallback은 유지함
- 다만 3D 중간 부피 구간은 추가 분석 후보로 둠

### H35. Warm/Cold를 하나의 모델로 합치는 것보다 분리 모델을 쓰는 것이 안정적일 것이다

- 배경
- Warm과 Cold는 입력 가능 정보와 난이도가 다름
- 모델을 하나로 합치면 운영은 단순하지만 Cold 성능이 흔들릴 수 있음
- 질문
- H31형 단일 모델이 Warm과 Cold를 동시에 잘 처리할 수 있는가
- 현재 판단
- 검증 완료
- 단일 공유 모델은 Cold에서 크게 악화됨
- 연구 방법
- H31형 LightGBM을 Cold에도 적용하고, H31/H32 분리 정책과 비교함
- 검증 결과
- 단일 공유 모델 Cold median APE `0.5938`
- H32 Cold 조건부 모델 median APE `0.2786`
- 결론
- Warm/Cold 분리 정책을 유지함

### H36. H31 Warm 후보는 작가별 학습 작품 수가 적은 작가에서 성능이 불안정할 수 있다

- 배경
- Warm은 작가 이력 피처를 쓰기 때문에 작가별 학습 작품 수가 중요할 수 있음
- 질문
- 학습 작품 수가 적은 작가의 Warm 예측 오차가 더 큰가
- 현재 판단
- 검증 완료
- 작가 이력이 적은 구간에서 오차가 큼
- 연구 방법
- Warm test를 작가 학습 작품 수 구간별로 나누어 H31 성능을 비교함
- 검증 결과
- 작가 1건 구간 `0.2466`
- 작가 51건 이상 구간 `0.0621`
- 결론
- 저이력 Warm 작가는 신뢰도 경고 또는 넓은 가격 범위가 필요함

### H37. 예측 오차는 작가 학습 이력 수에 영향을 받을 것이다

- 배경
- H36에서 작가 이력 수에 따른 오차 차이가 확인됨
- 질문
- `artist_works_log`를 신뢰도 피처로도 볼 수 있는가
- 현재 판단
- 검증 완료
- 작가 이력이 많을수록 오차가 줄어드는 경향이 있음
- 연구 방법
- `artist_works_log`와 Warm APE의 순위 상관을 확인함
- 검증 결과
- Spearman 상관 `-0.2423`
- 결론
- `artist_works_log`는 성능 피처와 신뢰도 피처 후보로 유지함

### H38. artist_name_ko 자체보다 구조화된 작가 이력 피처가 운영 안정성이 높을 것이다

- 배경
- 작가명은 Warm에서 강하지만 운영상 신규/동명이인/표기 문제를 만들 수 있음
- 구조화된 작가 이력은 설명과 관리가 더 쉬울 수 있음
- 질문
- 작가명만 쓰는 것보다 작가 이력 피처가 더 좋은가
- 현재 판단
- 검증 완료
- 작가 이력만으로도 작가명 단독보다 훨씬 좋음
- 연구 방법
- 작가명만, 작가 이력만, 작가명+이력 모델을 비교함
- 검증 결과
- 작가명만 `0.2273`
- 작가 이력만 `0.1120`
- 작가명+이력 `0.1002`
- 결론
- 작가 이력 피처 유지
- 단, 운영 채택 전 H16 temporal-safe 검증 필요

### H39. 대형 작품은 일반 작품과 다른 가격 구조를 가지므로 별도 보정이 필요하다

- 배경
- 대형/초대형 작품은 운송, 설치, 시장 수요 등의 영향으로 가격 구조가 다를 수 있음
- 질문
- 대형 작품에서 현재 모델 오차가 더 큰가
- 현재 판단
- 검증 완료
- 특히 Cold 대형/초대형 작품에서 오차가 큼
- 연구 방법
- Warm/Cold를 대형 호수, 초대형 호수, 대형 면적 구간으로 나누어 성능을 비교함
- 검증 결과
- Cold 대형 호수 `0.4448`
- Cold 초대형 호수 `0.5412`
- 결론
- Cold 대형 작품은 high-risk 또는 보정 후보로 관리함

### H40. Cold에서는 재료보다 크기/형태 피처가 더 중요한 설명 변수일 것이다

- 배경
- Cold는 작가 정보가 없기 때문에 작품 자체 정보의 중요도가 커짐
- 질문
- Cold에서 어떤 피처 그룹이 더 중요한가
- 현재 판단
- 검증 완료
- 재료도 중요하지만 크기/호수 제거 시 악화가 더 큼
- 연구 방법
- Cold full 모델에서 재료, 크기/호수, 형태 피처를 각각 제거해 비교함
- 검증 결과
- full `0.3163`
- 재료 제거 `0.4112`
- 크기/호수 제거 `0.4809`
- 형태 제거 `0.3393`
- 결론
- Cold 기본 피처에서 크기/호수와 재료 모두 유지함

### H41. 현재 최적 후보는 반복 실행에서도 순위가 크게 바뀌지 않을 것이다

- 배경
- 최종 후보는 단일 실행 결과가 아니라 반복 실행에서도 안정적이어야 함
- 질문
- H31/H32 후보가 반복 확인에서도 유지되는가
- 현재 판단
- 검증 완료
- H31/H32 후보 순위가 유지됨
- 연구 방법
- H31은 3개 seed 평균을 확인하고, H32는 deterministic LAD 기준을 확인함
- 검증 결과
- H31 Warm 약 `0.1090`
- H32 Cold `0.2786`
- 결론
- 현재 후보 안정성은 유지됨

### H42. 예측값이 크게 벗어나는 작품은 사전에 탐지 가능한 패턴이 있다

- 배경
- 가격 예측 서비스에서는 큰 오차가 나는 작품을 미리 경고하는 것이 중요함
- 질문
- 큰 오차 작품은 3D, 대형, 저이력 같은 공통 패턴이 있는가
- 현재 판단
- 검증 완료
- 큰 오차가 3D/대형/저이력 쪽에 집중되는 경향이 있음
- 연구 방법
- Warm/Cold 오차 상위 10% 작품의 피처 분포를 확인함
- 검증 결과
- Warm 오차 상위 10% 작가 학습 작품 수 중앙값 `3`
- Cold 오차 상위 10% 3D 비율 `72.8%`
- 결론
- high-risk flag 후보로 관리함

### H43. 최종 서비스에서는 단일 가격보다 가격 범위를 함께 제시하는 것이 더 안전하다

- 배경
- 미술품 가격은 변동성과 이상치가 커서 단일 가격만 제시하면 오해가 생길 수 있음
- 질문
- 현재 후보의 오차 수준을 보면 가격 범위 출력이 필요한가
- 현재 판단
- 검증 완료
- Cold는 Warm보다 훨씬 넓은 범위가 필요함
- 연구 방법
- 현재 H31/H32 예측의 로그 오차 분포에서 단순 오차폭을 확인함
- 검증 결과
- Warm 90% 단순 로그 오차폭 `0.666`
- Cold 90% 단순 로그 오차폭 `1.070`
- 결론
- 최종 서비스는 단일 가격 + 신뢰도/가격 범위 출력이 더 안전함
- 최종 후보 확정 후 calibration이 필요함

### H44. Warm 저이력 작가에는 일반 Warm 모델보다 보수적 fallback이 더 안정적일 것이다

- 배경
- H36에서 작가 학습 작품 수가 적은 Warm 구간의 오차가 컸음
- 질문
- 저이력 Warm 작가를 H31로 예측하는 것이 맞는가
- 구조-only fallback이 더 안정적인가
- 현재 판단
- 검증 완료
- 구조-only fallback은 저이력 Warm에서도 악화됨
- 연구 방법
- 작가 학습 작품 수 1건, 1~3건, 4건 이상 구간에서 H31과 구조-only 모델을 비교함
- 검증 결과
- 작가 1건 구간 H31 `0.2466`, 구조-only fallback `0.5015`
- 결론
- fallback은 기각
- 저이력 Warm은 H31 유지 + 신뢰도 경고로 관리함

### H45. Cold 3D 중간 부피 구간은 3D fallback보다 기본 Cold 모델이 더 안정적일 것이다

- 배경
- H34에서 3D 중간 부피 구간은 fallback 악화 신호가 있었음
- 질문
- H32 3D fallback을 모든 3D에 적용해도 되는가
- 중간 부피 3D는 기본 Cold 모델로 예외 처리하는 것이 나은가
- 현재 판단
- 검증 완료
- 중간 부피 3D와 전체 Cold median APE는 소폭 개선됨
- 연구 방법
- Cold 3D를 부피 기준 low/mid/high로 나누고, mid 구간만 기본 Cold 모델로 되돌림
- 검증 결과
- 3D mid `0.2238 -> 0.1912`
- 전체 Cold `0.2786 -> 0.2765`
- 결론
- 조건부 예외 후보
- 다만 p90/p95 오차가 일부 커져 추가 기준 확인 필요

### H46. High-risk 작품에는 가격 범위를 넓게 주는 방식이 실제 포함률을 개선할 것이다

- 배경
- H42/H43에서 high-risk 작품과 가격 범위 출력 필요성이 확인됨
- 질문
- high-risk 작품에 더 넓은 가격 범위를 주면 실제 가격 포함률이 개선되는가
- 현재 판단
- 검증 완료
- Warm 저이력 등급과 Cold 2D/대형/초대형 조건에서 넓은 가격 범위 필요성이 확인됨
- 연구 방법
- high-risk와 low-risk를 나누고, 같은 오차폭 적용과 구간별 오차폭 적용을 비교함
- 검증 결과
- Warm high-risk coverage `0.7088 -> 0.7997`
- H69 최종 calibration 기준
- Warm D 등급 80% 가격 범위 배율 `x1.98`
- Cold 표준 2D 80% 가격 범위 배율 `x2.64`
- Cold 대형/초대형 high-risk 80% 가격 범위 배율 `x2.92`
- Cold 대형/초대형 high-risk 90% 가격 범위 배율 `x5.41`
- 결론
- H46은 검증 완료
- high-risk 작품에는 별도 넓은 가격 범위와 낮은 신뢰도 표시를 적용함

### H47. artist_works_log만으로도 Warm 신뢰도 등급을 만들 수 있을 것이다

- 배경
- H37에서 작가 이력 수와 Warm 오차의 관계가 확인됨
- 질문
- 작가 학습 작품 수만으로도 Warm 신뢰도 등급을 만들 수 있는가
- 현재 판단
- 검증 완료
- 등급별 오차가 단계적으로 나뉨
- 연구 방법
- 작가 학습 작품 수를 A/B/C/D 구간으로 나누어 Warm median APE를 비교함
- 검증 결과
- A: 51건 이상 `0.0621`
- B: 11~50건 `0.0759`
- C: 4~10건 `0.1350`
- D: 1~3건 `0.1608`
- 결론
- Warm 신뢰도 등급 후보로 사용 가능

### H48. Cold high-risk 기준을 더 좁게 잡으면 가격 범위 정책이 더 안정적일 것이다

- 배경
- H46에서 Cold high-risk 정의가 너무 넓어 해석이 불안정했음
- 질문
- Cold high-risk를 어떤 조건으로 잡아야 실제 오차가 큰 작품을 잘 구분하는가
- 현재 판단
- 검증 완료
- `large_ho`, `very_large_area`, `extra_large_ho`는 high-risk 기준으로 유효함
- 단순 3D 여부는 오히려 low-risk보다 오차가 낮아 high-risk 기준으로 부적합함
- 연구 방법
- 3D, 초대형 호수, 대형 면적, 조합 조건별로 median APE와 p90/p95를 비교함
- 검증 결과
- `large_ho_only` high-risk median APE `0.4448`, low-risk `0.2394`
- `very_large_area_only` high-risk median APE `0.4448`, low-risk `0.2346`
- `extra_large_ho_only` high-risk median APE `0.5412`, low-risk `0.2628`
- 결론
- Cold high-risk는 대형/초대형 조건 중심으로 관리함

### H49. Cold 3D 중간 부피 예외는 tail risk 기준까지 보고 채택해야 한다

- 배경
- H45에서 median APE는 개선됐지만 p90/p95 오차 악화 가능성이 있음
- 질문
- median APE 개선이 tail risk 악화를 감수할 만큼 충분한가
- 현재 판단
- 검증 완료
- median APE는 개선되지만 p95가 악화되어 채택 보류
- 연구 방법
- H32와 H45 예외 정책을 median APE, p90, p95, within-50%로 함께 비교함
- 검증 결과
- 전체 Cold median APE `0.2786 -> 0.2765`
- 전체 p95 APE `1.4860 -> 1.6229`
- 중간 3D median APE `0.2238 -> 0.1912`
- 중간 3D p95 APE `0.9427 -> 1.3670`
- 결론
- tail risk 악화가 있어 현재 운영 후보에는 반영하지 않음

### H50. Warm 신뢰도 등급은 p90 APE 기준으로 재구성하는 것이 더 실용적일 것이다

- 배경
- H47은 median APE 기준으로 등급을 나눴음
- 서비스에서는 큰 오차 가능성도 중요함
- 질문
- p90 APE 기준으로 등급을 다시 나누면 더 실용적인가
- 현재 판단
- 검증 완료
- 작가 이력 구간별 median/p90/p95가 단계적으로 벌어짐
- 연구 방법
- artist_count 구간별 p90 APE와 within-30/50을 비교해 등급 기준을 재설계함
- 검증 결과
- A 51건 이상 median APE `0.0570`, p95 `0.5604`
- B 11~50건 median APE `0.0705`, p95 `0.7167`
- C 4~10건 median APE `0.1288`, p95 `0.9585`
- D 1~3건 median APE `0.1714`, p95 `2.0514`
- 결론
- Warm 신뢰도 등급은 작가 이력 수 기반으로 운영 후보 유지

### H51. Warm 신뢰도 등급과 가격 범위를 결합하면 더 안정적인 출력 정책을 만들 수 있다

- 배경
- H46은 가격 범위, H47은 신뢰도 등급을 각각 봤음
- 질문
- Warm 등급별로 다른 가격 범위를 주는 것이 적절한가
- 현재 판단
- 검증 완료
- 저이력 D 등급은 별도 넓은 가격 범위가 필요함
- 연구 방법
- A/B/C/D 등급별 로그 오차폭과 coverage를 계산함
- 검증 결과
- D 등급 전역 width80 coverage `0.6667`
- D 등급별 width80 coverage `0.8004`
- A/B 등급은 전역 width보다 좁은 등급별 width로도 coverage 확보 가능
- 결론
- Warm 출력 정책은 신뢰도 등급별 가격 범위를 분리하는 방향이 적절함

### H52. Cold에서는 단일 가격 범위보다 모델 조건별 가격 범위가 더 적절할 것이다

- 배경
- Cold는 2D, 3D, 대형 여부에 따라 오차 구조가 다름
- 질문
- Cold 전체에 같은 가격 범위를 쓰는 것이 적절한가
- 현재 판단
- 검증 완료
- Cold 2D/대형/초대형 구간은 전역 가격 범위로 coverage가 부족함
- 연구 방법
- Cold 전체, 2D, 3D, 대형, 초대형 구간별 interval coverage를 비교함
- 검증 결과
- Cold 전체 전역 width80 coverage `0.7999`
- Cold 2D 전역 width80 coverage `0.6915`
- large_ho 전역 width80 coverage `0.6770`
- very_large_area 전역 width80 coverage `0.6187`
- 결론
- Cold는 조건별 가격 범위를 따로 두는 것이 적절함

### H57. Warm에서는 작가 이력 피처를 더 세분화하면 성능이 개선될 것이다

- 배경
- H38에서 작가 이력 피처가 강하게 작동함
- 질문
- 작가별 가격 분포를 더 세밀하게 표현하면 Warm 성능이 더 좋아지는가
- 현재 판단
- 검증 완료
- multi-seed에서 개선 신호는 있으나 채택 기준에는 미달함
- 연구 방법
- 작가별 p25/p75/p90, 고가 작품 비율, 변동성 등급을 추가해 H31과 비교함
- 검증 결과
- H66 base mean median APE `0.1051`
- H57 extended history mean median APE `0.1032`
- delta `-0.0019`
- H57 p95 APE는 `0.9679 -> 0.9849`로 소폭 악화
- 결론
- 현재 Warm 최종 후보에는 반영하지 않음

### H58. Warm에서는 작가별 가격대와 작품 크기의 상호작용 피처가 성능을 개선할 것이다

- 배경
- 같은 크기라도 작가 가격대에 따라 가격 상승폭이 다를 수 있음
- 질문
- 작가 가격대와 크기/호수의 조합이 Warm 가격을 더 잘 설명하는가
- 현재 판단
- 검증 완료
- H66 대비 악화되어 기각
- 연구 방법
- `artist_ln_price_median * log_area`, `artist_ln_price_median * log_ho` 등 상호작용 피처를 추가함
- 검증 결과
- H66 base mean median APE `0.1051`
- H58 interactions mean median APE `0.1092`
- 결론
- 상호작용 피처는 현재 후보에서 제외

### H59. Cold에서는 재료별 별도 스케일 보정이 성능을 개선할 것이다

- 배경
- H40에서 재료 제거 시 Cold가 악화되어 재료 중요도가 확인됨
- 질문
- 재료별 가격 분포 차이를 보정하면 Cold 성능이 좋아지는가
- 현재 판단
- 검증 완료
- 개선 폭이 너무 작아 채택 보류
- 연구 방법
- train 기준 재료별 residual 또는 로그가격 중앙값 보정을 적용해 Cold 성능을 비교함
- 검증 결과
- H32 base median APE `0.2786`
- medium shift 0.10 median APE `0.2783`
- within-30%는 `0.5203 -> 0.5150`으로 악화
- 결론
- 성능 개선 폭이 운영 복잡도를 정당화하지 못함

### H60. Cold에서는 medium_category와 support_category 조합을 더 정리하면 성능이 개선될 것이다

- 배경
- 희소한 재료/바탕 조합은 noise가 될 수 있음
- 질문
- 희소 조합을 묶고 안정적인 조합만 남기면 Cold 성능이 개선되는가
- 현재 판단
- 검증 완료
- H32보다 악화되어 기각
- 연구 방법
- train 빈도 기준 rare combo를 `other_combo`로 묶고 기존 피처와 비교함
- 검증 결과
- H32 base median APE `0.2786`
- combo base only `0.2922`
- combo base + 3D fallback `0.2803`
- 결론
- medium/support 조합 정리 피처는 사용하지 않음

### H61. Cold에서는 비선형 모델이 전체는 약해도 특정 slice에서는 선형보다 우세할 것이다

- 배경
- 전체 Cold에서는 LAD가 우세하지만 일부 slice에서는 tree expert 가능성이 있었음
- 질문
- 3D, 대형, 초대형 구간에만 tree expert를 적용하면 성능이 개선되는가
- 현재 판단
- 검증 완료
- tree expert는 전체와 target slice 모두 악화됨
- 결론
- 기각

### H62. Warm에서는 LightGBM 튜닝을 H31 피처 기준으로 다시 하면 성능이 개선될 것이다

- 배경
- H31은 새 피처셋이므로 기존 LightGBM 설정이 최적이 아닐 수 있음
- 질문
- H31 피처셋 기준으로 LightGBM 설정을 다시 맞추면 Warm 성능이 개선되는가
- 현재 판단
- 부분 검증
- 단일 seed 기준 개선 신호가 있음
- 검증 결과
- `h31_current_like` `0.1002`
- `larger_low_lr` `0.1027`
- 결론
- multi-seed 재검증 필요

### H63. Cold LAD의 규제 강도 alpha를 조정하면 성능과 안정성이 개선될 것이다

- 배경
- 현재 Cold LAD는 `alpha=0` 기준임
- 질문
- alpha를 주면 median APE 또는 tail risk가 개선되는가
- 현재 판단
- 검증 완료
- alpha 증가 시 성능 악화
- 결론
- 기각

### H64. Cold 예측값을 robust ensemble로 결합하면 tail risk가 줄어들 것이다

- 배경
- LAD, Huber, Ridge는 각각 다른 오차 특성을 가질 수 있음
- 질문
- robust ensemble이 LAD보다 안정적인가
- 현재 판단
- 검증 완료
- Ridge base는 LAD base보다 개선됐지만 H32 조건부 후보보다 좋지 않음
- 결론
- 최종 Cold 후보 대체에는 사용하지 않음

### H65. Warm 예측값과 작가별 기준가격을 blending하면 저이력 작가 성능이 개선될 것이다

- 배경
- H44에서 구조-only fallback은 실패했지만, 완전 교체가 아닌 blending은 가능성이 있음
- 질문
- 저이력 Warm에서 H31 예측과 작가 중앙값을 섞으면 성능이 좋아지는가
- 현재 판단
- 검증 완료
- 전체 Warm 개선은 매우 작고 저이력 개선 목적을 충족하지 못함
- 결론
- 미채택

### H66. H62의 Warm LightGBM 재튜닝 개선 신호는 multi-seed에서도 유지될 것이다

- 배경
- H62에서 단일 seed 기준 Warm LightGBM 재튜닝 개선 신호가 있었음
- 단일 seed 결과만으로 최종 Warm 후보를 바꾸면 위험함
- 질문
- H62의 `larger_low_lr` 후보가 여러 seed에서도 기존 H31 current-like 설정보다 좋은가
- 현재 판단
- 검증 완료
- `larger_low_lr`가 multi-seed 평균 기준으로 개선됨
- 연구 방법
- seed `11`, `22`, `33`에서 `h31_current_like`, `larger_low_lr`, `smaller_regularized`를 비교함
- 검증 결과
- `h31_current_like` mean median APE `0.1090`
- `larger_low_lr` mean median APE `0.1051`
- delta `-0.0039`
- 결론
- Warm 최종 후보를 `larger_low_lr` 설정으로 갱신함

### H67. H57/H58의 Warm 피처 확장 개선 신호는 multi-seed에서도 유지될 것이다

- 배경
- H57/H58이 단일 seed에서 Warm 개선 신호를 보였음
- 단일 seed 기준으로 피처를 늘리면 과적합 또는 우연 개선일 수 있음
- 질문
- H57/H58 추가 피처가 여러 seed에서도 H66 후보보다 안정적으로 좋은가
- 현재 판단
- 검증 완료
- H57은 개선 신호는 있으나 채택 기준 미달
- H58은 H66보다 악화
- 연구 방법
- seed `11`, `22`, `33`에서 H66 base, H57, H58, H57+H58을 비교함
- 검증 결과
- H66 base mean median APE `0.1051`
- H57 extended history `0.1032`
- H58 interactions `0.1092`
- H57+H58 combined `0.1042`
- 결론
- Warm 최종 후보는 H66 유지
- H57/H58 추가 피처는 현재 운영 후보에 넣지 않음

### H68. Warm 모델 사용 기준을 작가 학습 작품 수 3건/5건 이상으로 올리면 더 안정적일 것이다

- 배경
- 현재 운영 기준은 작가 학습 작품이 1건 이상이면 Warm 모델을 사용함
- H36/H47에서 저이력 작가의 Warm 오차가 높게 나타남
- 질문
- Warm 모델을 쓰기 위한 최소 작가 작품 수 기준을 3건, 5건 이상으로 올리는 것이 좋은가
- 현재 판단
- 검증 완료
- 기준을 올리면 전체 Warm 성능이 악화됨
- 저이력 작가도 Cold fallback보다 Warm 모델이 더 나음
- 연구 방법
- Warm 평가셋에서 `artist_train_count >= 1, 2, 3, 5, 10, 20, 50` 기준을 비교함
- 기준 이상은 H66 Warm 모델 사용
- 기준 미만은 Cold base fallback 사용
- 검증 결과
- 항상 Warm / count >= 1 median APE `0.1024`
- count >= 3 정책 median APE `0.1369`
- count >= 5 정책 median APE `0.1828`
- 항상 Cold fallback median APE `0.4982`
- 작가 학습 작품 1건 구간에서도 Warm median APE `0.2596`, Cold fallback `0.5651`
- 결론
- Warm 라우팅 기준은 `artist_train_count >= 1` 유지
- 저이력 작가는 Cold 전환이 아니라 신뢰도 경고와 넓은 가격 범위로 관리함

### H70. 내부 calibration split으로 계산한 가격 범위도 유지될 것이다

- 배경
- H69 가격 범위는 test residual을 기준으로 계산되어 운영 과적합 우려가 있었음
- 질문
- test residual이 아니라 train 내부 calibration split으로 가격 범위를 계산해도 Warm/Cold 조건별 가격 범위 정책이 유지되는가
- 현재 판단
- 검증 완료
- 연구 방법
- Warm은 train 안에서 작가별 1개 작품을 calibration으로 분리함
- Cold는 train 안에서 작가 200명을 통째로 holdout해 내부 Cold calibration set을 만듦
- calibration residual로 조건별 80% 가격 범위 폭을 계산함
- 계산된 폭을 실제 Warm/Cold test 예측에 적용해 coverage를 확인함
- 검증 결과
- Warm 전체 coverage `0.821`, D등급 coverage `0.794`
- Cold 전체 coverage `0.855`, 표준 2D coverage `0.783`, high-risk coverage `0.794`
- 결론
- 조건별 가격 범위 정책은 유지 가능함
- 운영 pipeline에서는 calibration split을 별도로 고정해야 함

### H71. Cold 3D 중간 부피 예외는 train 기준 threshold로 정해도 유효할 것이다

- 배경
- H45/H49의 중간 부피 예외는 cold test quantile을 기준으로 만들어져 운영 기준으로 바로 쓰기 어려웠음
- 질문
- train 3D 분포 기준으로 중간 부피 threshold를 정해도 예외 정책이 유효한가
- 현재 판단
- 검증 완료
- 미채택
- 연구 방법
- train 3D 작품의 `volume_log` q33, q66을 기준으로 중간 부피 구간을 정의함
- Cold test에서 해당 구간만 3D fallback 대신 기본 Cold 모델을 적용함
- 전체 Cold median APE와 p95 APE를 H32와 비교함
- 검증 결과
- 전체 Cold median APE `0.2786 -> 0.2798`로 악화
- 전체 Cold p95 APE `1.4860 -> 1.6192`로 악화
- 중간 3D median APE는 `0.2488 -> 0.2414`로 소폭 개선
- 중간 3D p95 APE는 `1.0778 -> 1.6086`로 크게 악화
- 결론
- 중간 3D 예외는 tail risk가 커서 미채택
- H32 Cold 3D 조건부 fallback 유지

### H72. medium/support 조합 정리는 여러 희소도 기준에서도 Cold 성능을 개선할 것이다

- 배경
- H60은 `min_count=100` 기준만 확인해 조합 정리 방식이 충분히 검증됐는지 의문이 있었음
- 질문
- `min_count` 기준을 바꿔도 medium/support 조합 정리가 H32보다 좋은가
- 현재 판단
- 검증 완료
- 미채택
- 연구 방법
- `min_count=20/50/100/200/500` 기준으로 희소 조합을 `other_combo`로 묶음
- Cold base + 3D fallback 구조에서 H32와 비교함
- 검증 결과
- H32 기준 Cold median APE `0.2786`
- `min_count=20` median APE `0.2802`
- `min_count=50` median APE `0.2802`
- `min_count=100` median APE `0.2803`
- `min_count=200` median APE `0.2793`
- `min_count=500` median APE `0.2792`
- 결론
- 모든 기준에서 H32보다 median APE가 악화됨
- medium/support 조합 정리 피처는 미채택

## 5. 이 문서와 다른 문서의 역할 구분

- `track3_experiment_plan_v1.md`
- 전체 기준 문서
- `track3_hypothesis_list_v1.md`
- 가설 설명 문서
- `track3_hypothesis_table.md`
- 가설 상태를 한눈에 보는 표
- `track3_experiment_results_table.md`
- 실행된 실험 결과를 한눈에 보는 표
- `docs/track3_experiments/*`
- 개별 실험 상세 기록

## 6. 현재 결론

- Track 3에서는 실험을 바로 늘리는 방식보다
- 먼저 가설을 분명히 적고
- 그 가설에 맞는 방법을 고른 뒤
- 실행과 검증을 분리하는 방식이 더 적절함
- H13, H14는 현재 방식의 추가 피처가 채택 기준을 넘지 못함
- H15는 현재 release split에 결측 신호가 없어 보류함
- H9는 전체 마스킹 학습 방식이 채택 기준을 넘지 못함
- H10은 작가 이력 피처의 가치가 확인됐지만 temporal-safe 재검증이 필요함
- H11은 보조 출력 후보로 보류함
- H12는 설명용 보조 구조로 보류함
- H16은 날짜 컬럼 부재로 temporal-safe 검증을 보류함
- H17은 작가 이력 피처의 반복 안정성을 확인함
- H18은 Warm 80% 예측 구간 보정 가능성을 확인함
- H29~H30은 H4의 후속 가설로, Warm/Cold 피처 분리와 slice별 개선 가능성을 검증 완료함
- H31은 H17 Warm champion 위에서도 호수/3D 피처 개선이 유지되는지 재검증 완료함
- H32는 Cold 3D 피처를 조건부 fallback으로 적용하면 2D 악화 없이 Cold 전체가 개선되는지 검증 완료함
- H33은 PR7 Warm 최고 탐색 기록이 release split / 운영 가능 피처 기준에서는 유지되지 않음을 확인함
- H34는 Cold 3D fallback이 전체적으로 유효하지만 3D 내부 slice별 차이가 있음을 확인함
- H35는 Warm/Cold 단일 모델 통합보다 분리 정책이 안전함을 확인함
- H36~H37은 Warm 저이력 작가에서 오차가 커지고 작가 이력 수가 신뢰도 피처 후보임을 확인함
- H38은 작가명 단독보다 구조화된 작가 이력 피처가 강하다는 점을 확인함
- H39~H42는 Cold 대형/3D와 Warm 저이력 구간을 high-risk 후보로 관리해야 함을 확인함
- H43은 최종 서비스에서 단일 가격보다 가격 범위/신뢰도 출력이 더 안전하다는 근거를 추가함
- H48~H52는 Warm/Cold 신뢰도와 가격 범위 정책을 세분화할 근거를 확인함
- H57~H60은 추가 성능 개선 후보를 검증했지만 최종 모델을 바꿀 정도의 개선은 확인하지 못함
- H67은 H57/H58 multi-seed 검증 결과 Warm 후보를 H66으로 유지해야 함을 확인함
- H68은 Warm 라우팅 기준을 3건/5건 이상으로 올리는 정책을 기각하고 `artist_train_count >= 1` 기준 유지를 확인함
- H70은 내부 calibration split 기준으로도 조건별 가격 범위 정책이 유지됨을 확인함
- H71은 Cold 3D 중간 부피 예외가 train 기준 threshold에서도 tail risk를 악화시켜 미채택함
- H72는 medium/support 조합 정리가 grid 재검증에서도 H32보다 악화되어 미채택함
- H19~H22는 호수 파생 피처의 개선 가능성을 검증 완료함
- H23~H25는 크기/3D/상대 크기 피처를 검증 완료함
- H26~H28은 크기 피처 축소 가능성을 검증 완료함
- 현재 기준에서 남은 핵심 작업은
- H31~H43 결과를 바탕으로 최종 Warm / Cold / Cold 3D 조건부 후보와 신뢰도 출력 정책을 정리하는 것임
- 참고 문서 반영 이후에는
- `결측 대응`
- `거래 이력 기반 Warm 피처`
- `가격 범위 / 신뢰도`
- `2단계 residual 구조`
- `재료 세분화`
- `크기와 재료 조합`
- `결측 패턴 피처화`
- 역시 후속 가설로 관리함
