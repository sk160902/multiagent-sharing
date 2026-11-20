# Share and periodic board minus solo, paired over the 8 pilot worlds

| model | framing | measure | condition | n | solo | condition | diff [95% CI] | p | up/down |
|---|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | lemonade | best_peak | share | 8 | 93.8 | 78.9 | -14.9 [-29.3, -0.6] | 0.062 | 2/5 |
| claude-opus-5-5 | lemonade | best_peak | share_at6-11-16 | 8 | 93.8 | 90.8 | -3.1 [-11.0, +4.9] | 0.844 | 3/3 |
| claude-opus-5-5 | lemonade | sum_pct | share | 8 | 60.2 | 64.2 | +4.0 [-8.2, +16.3] | 0.453 | 5/3 |
| claude-opus-5-5 | lemonade | sum_pct | share_at6-11-16 | 8 | 60.2 | 67.2 | +7.0 [-1.8, +15.7] | 0.094 | 6/2 |
| claude-opus-5-5 | lemonade | unique | share | 8 | 51.9 | 33.1 | -18.8 [-21.5, -16.1] | 0.008 | 0/8 |
| claude-opus-5-5 | lemonade | unique | share_at6-11-16 | 8 | 51.9 | 45.8 | -6.1 [-8.1, -4.0] | 0.008 | 0/8 |
| claude-opus-5-5 | lemonade | reached_best | share | 8 | 93.8 | 56.2 | -37.5 [-67.1, -7.9] | 0.062 | 0/5 |
| claude-opus-5-5 | lemonade | reached_best | share_at6-11-16 | 8 | 93.8 | 81.2 | -12.5 [-42.1, +17.1] | 1.000 | 0/1 |
| claude-opus-5-5 | alien | best_peak | share | 8 | 84.0 | 84.5 | +0.6 [-7.0, +8.1] | 0.875 | 3/2 |
| claude-opus-5-5 | alien | best_peak | share_at6-11-16 | 8 | 84.0 | 80.0 | -4.0 [-11.0, +3.0] | 0.250 | 0/3 |
| claude-opus-5-5 | alien | sum_pct | share | 8 | 52.6 | 62.8 | +10.2 [+1.6, +18.7] | 0.031 | 7/1 |
| claude-opus-5-5 | alien | sum_pct | share_at6-11-16 | 8 | 52.6 | 55.8 | +3.2 [-0.9, +7.3] | 0.094 | 7/1 |
| claude-opus-5-5 | alien | unique | share | 8 | 47.8 | 36.1 | -11.6 [-20.2, -3.0] | 0.023 | 1/7 |
| claude-opus-5-5 | alien | unique | share_at6-11-16 | 8 | 47.8 | 45.1 | -2.6 [-6.7, +1.4] | 0.219 | 3/5 |
| claude-opus-5-5 | alien | reached_best | share | 8 | 68.8 | 75.0 | +6.2 [-8.5, +21.0] | 1.000 | 1/0 |
| claude-opus-5-5 | alien | reached_best | share_at6-11-16 | 8 | 68.8 | 62.5 | -6.2 [-21.0, +8.5] | 1.000 | 0/1 |
| gpt-5.6-sol | lemonade | best_peak | share | 8 | 84.4 | 75.4 | -9.0 [-25.3, +7.2] | 0.250 | 3/4 |
| gpt-5.6-sol | lemonade | best_peak | share_at6-11-16 | 8 | 84.4 | 78.8 | -5.6 [-21.7, +10.5] | 0.438 | 3/4 |
| gpt-5.6-sol | lemonade | sum_pct | share | 8 | 53.7 | 64.9 | +11.2 [+3.1, +19.4] | 0.023 | 7/1 |
| gpt-5.6-sol | lemonade | sum_pct | share_at6-11-16 | 8 | 53.7 | 60.9 | +7.2 [+0.5, +13.9] | 0.023 | 7/1 |
| gpt-5.6-sol | lemonade | unique | share | 8 | 42.8 | 22.8 | -20.1 [-26.9, -13.3] | 0.008 | 0/8 |
| gpt-5.6-sol | lemonade | unique | share_at6-11-16 | 8 | 42.8 | 37.1 | -5.7 [-9.2, -2.3] | 0.031 | 0/6 |
| gpt-5.6-sol | lemonade | reached_best | share | 8 | 70.8 | 50.0 | -20.8 [-53.9, +12.3] | 0.312 | 1/4 |
| gpt-5.6-sol | lemonade | reached_best | share_at6-11-16 | 8 | 70.8 | 58.3 | -12.5 [-42.1, +17.1] | 0.531 | 2/4 |
| gpt-5.6-sol | alien | best_peak | share | 8 | 86.8 | 71.2 | -15.6 [-35.9, +4.7] | 0.156 | 3/4 |
| gpt-5.6-sol | alien | best_peak | share_at6-11-16 | 8 | 86.8 | 89.7 | +2.9 [-12.7, +18.5] | 0.703 | 5/2 |
| gpt-5.6-sol | alien | sum_pct | share | 8 | 48.4 | 58.8 | +10.4 [-1.9, +22.7] | 0.102 | 5/3 |
| gpt-5.6-sol | alien | sum_pct | share_at6-11-16 | 8 | 48.4 | 59.9 | +11.5 [+4.9, +18.1] | 0.016 | 7/1 |
| gpt-5.6-sol | alien | unique | share | 8 | 48.0 | 25.1 | -23.0 [-25.9, -20.0] | 0.008 | 0/8 |
| gpt-5.6-sol | alien | unique | share_at6-11-16 | 8 | 48.0 | 42.8 | -5.2 [-8.6, -1.9] | 0.023 | 1/7 |
| gpt-5.6-sol | alien | reached_best | share | 8 | 79.2 | 50.0 | -29.2 [-63.9, +5.6] | 0.250 | 0/3 |
| gpt-5.6-sol | alien | reached_best | share_at6-11-16 | 8 | 79.2 | 83.3 | +4.2 [-23.5, +31.8] | 1.000 | 2/2 |
