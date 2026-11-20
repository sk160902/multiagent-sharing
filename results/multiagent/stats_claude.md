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
| claude-opus-5-5 | alien | best_peak | share | 8 | 84.0 | 86.9 | +3.0 [-10.1, +16.0] | 0.719 | 4/2 |
| claude-opus-5-5 | alien | best_peak | share_at6-11-16 | 8 | 84.0 | 78.8 | -5.1 [-13.5, +3.2] | 0.500 | 1/2 |
| claude-opus-5-5 | alien | sum_pct | share | 8 | 52.6 | 60.1 | +7.5 [-2.0, +16.9] | 0.109 | 6/2 |
| claude-opus-5-5 | alien | sum_pct | share_at6-11-16 | 8 | 52.6 | 56.1 | +3.5 [-1.9, +8.9] | 0.188 | 6/2 |
| claude-opus-5-5 | alien | unique | share | 8 | 47.8 | 38.6 | -9.2 [-15.5, -2.9] | 0.031 | 2/6 |
| claude-opus-5-5 | alien | unique | share_at6-11-16 | 8 | 47.8 | 46.2 | -1.6 [-5.4, +2.3] | 0.469 | 4/4 |
| claude-opus-5-5 | alien | reached_best | share | 8 | 68.8 | 75.0 | +6.2 [-20.5, +33.0] | 1.000 | 2/1 |
| claude-opus-5-5 | alien | reached_best | share_at6-11-16 | 8 | 68.8 | 62.5 | -6.2 [-21.0, +8.5] | 1.000 | 0/1 |
| gpt-5.6-sol | lemonade | best_peak | share | 8 | 84.4 | 75.4 | -9.0 [-25.3, +7.2] | 0.250 | 3/4 |
| gpt-5.6-sol | lemonade | best_peak | share_at6-11-16 | 8 | 84.4 | 78.8 | -5.6 [-21.7, +10.5] | 0.438 | 3/4 |
| gpt-5.6-sol | lemonade | sum_pct | share | 8 | 53.7 | 64.9 | +11.2 [+3.1, +19.4] | 0.023 | 7/1 |
| gpt-5.6-sol | lemonade | sum_pct | share_at6-11-16 | 8 | 53.7 | 60.9 | +7.2 [+0.5, +13.9] | 0.023 | 7/1 |
| gpt-5.6-sol | lemonade | unique | share | 8 | 42.8 | 22.8 | -20.1 [-26.9, -13.3] | 0.008 | 0/8 |
| gpt-5.6-sol | lemonade | unique | share_at6-11-16 | 8 | 42.8 | 37.1 | -5.7 [-9.2, -2.3] | 0.031 | 0/6 |
| gpt-5.6-sol | lemonade | reached_best | share | 8 | 70.8 | 50.0 | -20.8 [-53.9, +12.3] | 0.312 | 1/4 |
| gpt-5.6-sol | lemonade | reached_best | share_at6-11-16 | 8 | 70.8 | 58.3 | -12.5 [-42.1, +17.1] | 0.531 | 2/4 |
| gpt-5.6-sol | alien | best_peak | share | 8 | 86.8 | 79.2 | -7.6 [-30.9, +15.7] | 0.750 | 5/2 |
| gpt-5.6-sol | alien | best_peak | share_at6-11-16 | 8 | 86.8 | 83.6 | -3.1 [-16.5, +10.2] | 0.750 | 5/2 |
| gpt-5.6-sol | alien | sum_pct | share | 8 | 48.4 | 65.6 | +17.2 [+3.5, +30.9] | 0.031 | 7/1 |
| gpt-5.6-sol | alien | sum_pct | share_at6-11-16 | 8 | 48.4 | 56.9 | +8.5 [+3.7, +13.3] | 0.016 | 7/1 |
| gpt-5.6-sol | alien | unique | share | 8 | 48.0 | 26.2 | -21.8 [-24.7, -18.9] | 0.008 | 0/8 |
| gpt-5.6-sol | alien | unique | share_at6-11-16 | 8 | 48.0 | 42.5 | -5.6 [-9.6, -1.5] | 0.031 | 1/7 |
| gpt-5.6-sol | alien | reached_best | share | 8 | 79.2 | 66.7 | -12.5 [-45.6, +20.6] | 0.750 | 1/2 |
| gpt-5.6-sol | alien | reached_best | share_at6-11-16 | 8 | 79.2 | 70.8 | -8.3 [-33.0, +16.4] | 0.750 | 1/2 |
