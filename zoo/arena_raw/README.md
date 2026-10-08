# Arena replays (raw tapes)

Scraped read-only (plain GET of public fight pages) from https://hiddenhand.tqciitbhu.org on
Wed 7 Oct 2026: first at about 18:00 (the entries the zoo/arena_*.py imitations copy), again at
about 23:00 (newer uploads and new teams).

One JSON file per fight: `<entry>_vs_<opponent>_<opponent entry>.json`. Entry numbers are the
arena's upload ids (`#29` = Quantumlesssss v3). Folders hold every fight of the team's newest entry
at scrape time; quantumlesssss/ and paperhands/ also hold their older entries.

| Folder | Team | Entry used for the imitation | Fights |
|---|---|---|---|
| quantumlesssss | Quantumlesssss | #29 (v3) | 64 (all 3 entries) |
| paperhands | PaperHands | #26 (v3) | 64 (all 3 entries) |
| kryptex | KRYPTEX | #45 (v10) | 25 |
| outliers | Outliers | #34 (v1) | 32 |
| team_how | Team How | #59 (v1) | 21 |
| teenpatti | TeenPatti | #8 (v1) | 47 |

Added at 23:00 (newest entry only; files are prefixed with the entry id, so old and new sit side by side):

| Folder | Team | Entry | Fights |
|---|---|---|---|
| alpha_rodeo | Alpha Rodeo | #129 (v6, = zoo/rival_2.py, 2430/2430 decisions) | 81 |
| quants_treasure | Quants Treasure | #215 (v4) | 41 |
| happy_happy | Happy Happy | #182 (v3) | 53 |
| imposters | Imposters | #217 (v9) | 38 |
| quantumlesssss | Quantumlesssss | #231 (v11) | 30 |
| teenpatti | TeenPatti | #175 (v3) | 65 |
| kryptex | KRYPTEX | #204 (v19) | 41 |
| team_how | Team How | #110 (v5) | 99 |

## Format

Top level: `a`, `b` (team names), `score_a`, `pnl_a`, `score_b`, `pnl_b` (the 400-deal live fight
result), `entry_ids`, `when`, `href`, and `plays`: the first deal of the fight, played both ways.

Each play mirrors engine.py's replay log: `seats` (seat 0 quotes first in odd rounds), `hands`,
`board` (cards as strings, e.g. "J♣"), `hand_ranks`, `board_ranks`, `rounds` (per round: `moves`
[seat 0, seat 1] as null / `{"kind": "swap", "out", "in"}` / `{"kind": "peek", "card"}`, and
`quotes` as `{"maker", "price", "qty", "auto"}`, qty being what the taker did), `V`, `final_hands`,
`positions`, `paid`, `pnl`.

## Caveat: one deal only

Every fight page shows the same deal 1: hands 3 4 J 9 5 (sum 32) and 2 10 Q 8 8 (sum 40), board
J 2 Q Q 10. So each team is seen with only two hands (32 in seat 0, 40 in seat 1). The variety
comes from the opponents. Anything that depends on the size of its own hand was decoded from
how the quotes move with the opponents' quotes and trades, not from different hands.
