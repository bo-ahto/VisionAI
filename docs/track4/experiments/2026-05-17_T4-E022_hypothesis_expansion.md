# T4-E022 Track 4 가설 확장

- 실험 ID: `T4-E022`
- 연결 가설: `T4-H13` ~ `T4-H30`
- 상태: 완료
- 날짜: 2026-05-17
- 작성 방식: 개조식

## 1. 목적

- Track 3에서 검증했던 가설 축을 Track 4에 맞게 재정리함
- Track 4 데이터셋은 Track 3과 다르므로 가설을 그대로 복사하지 않음
- 1차 시장 데이터 특성, 운영 입력 제약, Warm/Cold split 구조를 반영함

## 2. 참고 기준

- Track 3 참고 축
- Warm / Cold 분리
- 작가 피처 효과
- robust Cold 모델
- 2D / 3D 조건부 보완
- 가격 범위와 신뢰도
- 피처 축소와 파생 피처 ablation
- Track 4 반영 차이
- 데이터셋이 1차 시장 기반으로 새로 구성됨
- source/gallery/tier는 운영 입력으로 쓸 수 없어 모델 피처에서 제외함
- `val_warm` row 수가 작아 반복 검증이 중요함
- support unknown 비율이 높아 unknown 처리 방식이 별도 검증 대상임
- depth/3D 후보가 있어 2D/3D 조건부 실험이 필요함

## 3. 추가한 가설

- `T4-H13`: 재료 세분화와 rare bucket 검증
- `T4-H14`: support unknown 처리 방식 검증
- `T4-H15`: 크기 피처 축소/대표 조합 검증
- `T4-H16`: 3D/depth 피처 조건부 적용 검증
- `T4-H17`: Cold 저위험/고위험 구간 분리 검증
- `T4-H18`: validation/calibration 기반 가격 범위 검증
- `T4-H19`: 저이력 Warm 위험 구간 검증
- `T4-H20`: 작가명 categorical과 작가 이력 피처 비교
- `T4-H21`: 공유 모델과 Warm/Cold 분리 모델 비교
- `T4-H22`: 반복 검증을 통한 모델 순위 안정성 확인
- `T4-H23`: source는 피처 제외, 감사 slice로만 활용
- `T4-H24`: 입력 정보 부족/위험 조건에서 출력 정책 검증
- `T4-H25`: 금지 피처 manifest 검사
- `T4-H26`: 고가 작품 tail risk 정책 검증
- `T4-H27`: Cold 2D/3D 조건부 fallback 검증
- `T4-H28`: 재료와 크기 조합 피처 검증
- `T4-H29`: source 없이 신뢰도 점수 생성 검증
- `T4-H30`: 최종 운영 패키지 재현성 검증

## 4. 결론

- Track 4 가설은 `T4-H1` ~ `T4-H30`으로 확장함
- 데이터 준비 체크포인트는 가설에서 제외하고 `T4-D` 기준으로 유지함
- 다음 모델 실험은 `T4-H1` 구조-only Warm / Cold baseline부터 진행하는 것이 맞음
- 이후 Warm 작가 피처, Cold robust 모델, support unknown, 2D/3D 조건부 실험 순서로 진행함

## 5. 후속 작업

- `T4-E023`: `T4-H1` 구조-only Warm / Cold baseline 실행
- `T4-E024`: `T4-H2`, `T4-H20` Warm 작가 피처 ablation 실행
- `T4-E025`: `T4-H4` Cold robust 모델 비교 실행
- `T4-E026`: `T4-H6`, `T4-H14` support unknown 처리 실험 실행
- `T4-E027`: `T4-H8`, `T4-H16`, `T4-H27` 2D/3D 조건부 실험 실행
