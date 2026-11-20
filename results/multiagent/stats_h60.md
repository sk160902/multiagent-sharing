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
| rounds 1-60 | best_peak | n=8 | 91.4 -> 72.4 | diff -19.0 [-41.0, +2.9] p=0.125 (1 up, 5 down) |
| rounds 1-60 | sum_pct | n=8 | 65.2 -> 67.4 | diff +2.2 [-15.7, +20.1] p=0.766 (6 up, 2 down) |
| rounds 1-60 | unique | n=8 | 63.5 -> 30.0 | diff -33.5 [-41.4, -25.7] p=0.008 (0 up, 8 down) |
| rounds 1-60 | reached_best | n=8 | 83.3 -> 50.0 | diff -33.3 [-72.8, +6.1] p=0.156 (1 up, 5 down) |
| rounds 21-60 | best_peak | n=8 | 91.4 -> 72.4 | diff -19.0 [-41.0, +2.9] p=0.125 (1 up, 5 down) |
| rounds 21-60 | sum_pct | n=8 | 75.3 -> 72.3 | diff -3.0 [-23.5, +17.5] p=0.727 (3 up, 5 down) |
| rounds 21-60 | unique | n=8 | 13.0 -> 1.3 | diff -11.7 [-17.5, -5.9] p=0.008 (0 up, 8 down) |
| rounds 21-60 | reached_best | n=8 | 83.3 -> 50.0 | diff -33.3 [-72.8, +6.1] p=0.156 (1 up, 5 down) |
| rounds 1-20 of 60 | best_peak | n=8 | 87.5 -> 72.3 | diff -15.1 [-36.7, +6.5] p=0.203 (4 up, 4 down) |
| rounds 1-20 of 60 | sum_pct | n=8 | 44.9 -> 57.5 | diff +12.6 [-1.9, +27.1] p=0.086 (6 up, 2 down) |
| rounds 1-20 of 60 | unique | n=8 | 52.1 -> 29.6 | diff -22.5 [-27.3, -17.7] p=0.008 (0 up, 8 down) |
| rounds 1-20 of 60 | reached_best | n=8 | 79.2 -> 50.0 | diff -29.2 [-69.8, +11.5] p=0.250 (1 up, 4 down) |
| 20-round game | best_peak | n=8 | 86.8 -> 71.2 | diff -15.6 [-35.9, +4.7] p=0.156 (3 up, 4 down) |
| 20-round game | sum_pct | n=8 | 48.4 -> 58.8 | diff +10.4 [-1.9, +22.7] p=0.102 (5 up, 3 down) |
| 20-round game | unique | n=8 | 48.0 -> 25.1 | diff -23.0 [-25.9, -20.0] p=0.008 (0 up, 8 down) |
| 20-round game | reached_best | n=8 | 79.2 -> 50.0 | diff -29.2 [-63.9, +5.6] p=0.250 (0 up, 3 down) |

| stated horizon, same window (rounds 1-20) | measure | 60-round game minus 20-round game |
|---|---|---|
| solo | best_peak | n=8 | 86.8 -> 87.5 | diff +0.7 [-2.4, +3.7] p=0.688 (3 up, 4 down) |
| solo | sum_pct | n=8 | 48.4 -> 44.9 | diff -3.5 [-6.5, -0.6] p=0.023 (1 up, 7 down) |
| solo | unique | n=8 | 48.0 -> 52.1 | diff +4.1 [+2.7, +5.4] p=0.008 (8 up, 0 down) |
| share | best_peak | n=8 | 71.2 -> 72.3 | diff +1.2 [-16.8, +19.1] p=0.875 (3 up, 3 down) |
| share | sum_pct | n=8 | 58.8 -> 57.5 | diff -1.4 [-11.5, +8.8] p=0.789 (3 up, 5 down) |
| share | unique | n=8 | 25.1 -> 29.6 | diff +4.5 [+0.0, +9.1] p=0.070 (6 up, 2 down) |

Decision rule: C1_sum_reversed no, C2_late_sum_negative YES, C3_ceiling_gap_closed no, C4_unique_positive no, complete YES

**Horizon changes the story (C1-C3, either framing): YES**
