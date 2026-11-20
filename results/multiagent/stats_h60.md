# Sixty-round games: sharing all along minus working alone, paired over the 8 pilot worlds


## lemonade framing: runs solo_h60 24, share_h60 24 (20-round comparators: solo 24, share 24)

| window | measure | share minus solo |
|---|---|---|
| rounds 1-60 | best_peak | n=8 | 97.8 -> 96.4 | diff -1.4 [-9.8, +7.0] p=1.000 (1 up, 2 down) |
| rounds 1-60 | sum_pct | n=8 | 71.2 -> 89.4 | diff +18.2 [+11.6, +24.8] p=0.008 (8 up, 0 down) |
| rounds 1-60 | unique | n=8 | 68.9 -> 28.4 | diff -40.5 [-46.2, -34.8] p=0.008 (0 up, 8 down) |
| rounds 1-60 | reached_best | n=8 | 95.8 -> 91.7 | diff -4.2 [-22.0, +13.7] p=1.000 (1 up, 2 down) |
| rounds 21-60 | best_peak | n=8 | 97.8 -> 96.4 | diff -1.4 [-9.8, +7.0] p=1.000 (1 up, 2 down) |
| rounds 21-60 | sum_pct | n=8 | 80.6 -> 95.4 | diff +14.8 [+6.8, +22.8] p=0.008 (8 up, 0 down) |
| rounds 21-60 | unique | n=8 | 17.2 -> 2.7 | diff -14.5 [-21.7, -7.2] p=0.008 (0 up, 8 down) |
| rounds 21-60 | reached_best | n=8 | 95.8 -> 91.7 | diff -4.2 [-22.0, +13.7] p=1.000 (1 up, 2 down) |
| rounds 1-20 of 60 | best_peak | n=8 | 89.4 -> 94.1 | diff +4.6 [-4.0, +13.3] p=0.195 (6 up, 2 down) |
| rounds 1-20 of 60 | sum_pct | n=8 | 52.5 -> 77.5 | diff +25.1 [+20.2, +29.9] p=0.008 (8 up, 0 down) |
| rounds 1-20 of 60 | unique | n=8 | 53.4 -> 26.8 | diff -26.6 [-30.1, -23.1] p=0.008 (0 up, 8 down) |
| rounds 1-20 of 60 | reached_best | n=8 | 83.3 -> 87.5 | diff +4.2 [-19.1, +27.4] p=1.000 (3 up, 2 down) |
| 20-round game | best_peak | n=8 | 84.4 -> 75.4 | diff -9.0 [-25.3, +7.2] p=0.250 (3 up, 4 down) |
| 20-round game | sum_pct | n=8 | 53.7 -> 64.9 | diff +11.2 [+3.1, +19.4] p=0.023 (7 up, 1 down) |
| 20-round game | unique | n=8 | 42.8 -> 22.8 | diff -20.1 [-26.9, -13.3] p=0.008 (0 up, 8 down) |
| 20-round game | reached_best | n=8 | 70.8 -> 50.0 | diff -20.8 [-53.9, +12.3] p=0.312 (1 up, 4 down) |

| stated horizon, same window (rounds 1-20) | measure | 60-round game minus 20-round game |
|---|---|---|
| solo | best_peak | n=8 | 84.4 -> 89.4 | diff +5.0 [-13.3, +23.4] p=0.531 (4 up, 2 down) |
| solo | sum_pct | n=8 | 53.7 -> 52.5 | diff -1.2 [-7.6, +5.1] p=0.617 (5 up, 3 down) |
| solo | unique | n=8 | 42.8 -> 53.4 | diff +10.5 [+5.2, +15.9] p=0.008 (8 up, 0 down) |
| share | best_peak | n=8 | 75.4 -> 94.1 | diff +18.7 [+5.0, +32.3] p=0.031 (6 up, 0 down) |
| share | sum_pct | n=8 | 64.9 -> 77.5 | diff +12.6 [-0.0, +25.2] p=0.047 (6 up, 2 down) |
| share | unique | n=8 | 22.8 -> 26.8 | diff +4.0 [+0.9, +7.2] p=0.031 (6 up, 1 down) |

Decision rule: C1_sum_reversed no, C2_late_sum_negative no, C3_ceiling_gap_closed YES, C4_unique_positive no, complete YES

## alien framing: runs solo_h60 24, share_h60 24 (20-round comparators: solo 24, share 24)

| window | measure | share minus solo |
|---|---|---|
| rounds 1-60 | best_peak | n=8 | 91.4 -> 81.2 | diff -10.3 [-27.5, +7.0] p=0.188 (1 up, 4 down) |
| rounds 1-60 | sum_pct | n=8 | 65.2 -> 75.5 | diff +10.3 [-5.0, +25.6] p=0.164 (5 up, 3 down) |
| rounds 1-60 | unique | n=8 | 63.5 -> 28.9 | diff -34.7 [-40.6, -28.7] p=0.008 (0 up, 8 down) |
| rounds 1-60 | reached_best | n=8 | 83.3 -> 66.7 | diff -16.7 [-50.0, +16.6] p=0.500 (1 up, 3 down) |
| rounds 21-60 | best_peak | n=8 | 91.4 -> 81.2 | diff -10.3 [-27.5, +7.0] p=0.188 (1 up, 4 down) |
| rounds 21-60 | sum_pct | n=8 | 75.3 -> 81.1 | diff +5.8 [-10.3, +21.9] p=0.398 (5 up, 3 down) |
| rounds 21-60 | unique | n=8 | 13.0 -> 1.6 | diff -11.5 [-17.1, -5.8] p=0.008 (0 up, 8 down) |
| rounds 21-60 | reached_best | n=8 | 83.3 -> 66.7 | diff -16.7 [-50.0, +16.6] p=0.500 (1 up, 3 down) |
| rounds 1-20 of 60 | best_peak | n=8 | 87.5 -> 79.3 | diff -8.2 [-24.8, +8.4] p=0.328 (4 up, 3 down) |
| rounds 1-20 of 60 | sum_pct | n=8 | 44.9 -> 64.2 | diff +19.3 [+4.8, +33.8] p=0.031 (6 up, 2 down) |
| rounds 1-20 of 60 | unique | n=8 | 52.1 -> 28.2 | diff -23.9 [-27.0, -20.8] p=0.008 (0 up, 8 down) |
| rounds 1-20 of 60 | reached_best | n=8 | 79.2 -> 62.5 | diff -16.7 [-50.0, +16.6] p=0.500 (1 up, 3 down) |
| 20-round game | best_peak | n=8 | 86.8 -> 79.2 | diff -7.6 [-30.9, +15.7] p=0.750 (5 up, 2 down) |
| 20-round game | sum_pct | n=8 | 48.4 -> 65.6 | diff +17.2 [+3.5, +30.9] p=0.031 (7 up, 1 down) |
| 20-round game | unique | n=8 | 48.0 -> 26.2 | diff -21.8 [-24.7, -18.9] p=0.008 (0 up, 8 down) |
| 20-round game | reached_best | n=8 | 79.2 -> 66.7 | diff -12.5 [-45.6, +20.6] p=0.750 (1 up, 2 down) |

| stated horizon, same window (rounds 1-20) | measure | 60-round game minus 20-round game |
|---|---|---|
| solo | best_peak | n=8 | 86.8 -> 87.5 | diff +0.7 [-2.4, +3.7] p=0.688 (3 up, 4 down) |
| solo | sum_pct | n=8 | 48.4 -> 44.9 | diff -3.5 [-6.5, -0.6] p=0.023 (1 up, 7 down) |
| solo | unique | n=8 | 48.0 -> 52.1 | diff +4.1 [+2.7, +5.4] p=0.008 (8 up, 0 down) |
| share | best_peak | n=8 | 79.2 -> 79.3 | diff +0.1 [-13.1, +13.2] p=0.969 (3 up, 3 down) |
| share | sum_pct | n=8 | 65.6 -> 64.2 | diff -1.4 [-12.5, +9.7] p=0.773 (4 up, 4 down) |
| share | unique | n=8 | 26.2 -> 28.2 | diff +2.0 [-0.6, +4.6] p=0.133 (5 up, 3 down) |

Decision rule: C1_sum_reversed no, C2_late_sum_negative no, C3_ceiling_gap_closed no, C4_unique_positive no, complete YES

**Horizon changes the story (C1-C3, either framing): YES**
