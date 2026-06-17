# Warm-lite unified route_gap_q50 v0.1

Default official 0.1v Warm route bundle for same-artist price history 1+.

- Selected candidate: `route_gap_q50`
- Gap threshold: `0.0252975144340901`
- Current formula: `seed_mean(qavg + clip(0.50 * residual, -0.10, +0.10))`
- Routed formula: `seed_mean(qavg) + clip(seed_mean(residual), -0.15, +0.15)`
- Status: default official 0.1v Warm route policy.
