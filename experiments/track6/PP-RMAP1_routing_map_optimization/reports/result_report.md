# PP-RMAP1 2차원 라우팅 맵

 history_k  min_required_accuracy  max_tolerable_rho
         1                 0.7219             0.2781
         2                 0.7008             0.2992
         3                 0.6960             0.3040
         4                 0.6965             0.3035
         5                 0.7005             0.2995

{
 "joint_boundary_needed": false,
 "reason": "이력 k 전 구간에서 요구 정확도(~0.69)와 허용 ρ(~0.31)가 거의 동일 — k에 따라 매칭 임계를 다르게 둘 근거 없음(독립 임계 구조 유지)",
 "rho_tolerance": "사전 밖 동명이인율이 ~31% 미만이면 모든 k에서 match-path 우위 (train 사전 내 동명이인 6.6% 참고 시 큰 마진)",
 "threshold_0_90": "합성상 0.70+ 동일 정확도이므로 0.90은 미측정 위험(ρ) 대비 마진 — 운영 로그로 ρ 실측 후 0.80~0.85 하향(통과량 +69%) 검토 가능"
}

(전체 격자: outputs/routing_map_grid.csv)