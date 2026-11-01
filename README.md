# Hidden Hand bot (team Alpha Rodeo)

Our entry for **Hidden Hand**, The Quant Club's freshers' algorithmic strategy event at
IIT (BHU), 5 to 8 October 2026. Each bot holds a hidden hand of cards and trades a stock
whose value is the sum of everyone's cards, against other teams' bots. The full game rules
from the organisers are in [GAME.md](GAME.md).

Built with AI-assisted development (Claude). Prompts we used are in [`prompts/`](prompts/).
The event's rules allowed AI tools.

## The final bot

[`heist/marseille.py`](heist/marseille.py) (v12; [`heist/professor.py`](heist/professor.py) is
the same code). A line-by-line study guide is in
[`heist/marseille_explained.pdf`](heist/marseille_explained.pdf).

- **Opponent model.** The stock is worth my hand, the board and the opponent's hidden hand,
  so the game is estimating that hand. The bot keeps a set of hypotheses about how the
  opponent forms its price: whether it reads my quotes, how much its own quotes reveal, how
  it reacts to my trades, and whether it will swap. Each hypothesis tracks a Gaussian
  estimate of the opponent's hand, updated with an extended Kalman filter from their quotes
  and from whether they bought, sold or passed at my price. Hypotheses that predict the
  opponent badly lose weight.
- **Planner.** Every possible quote and response is scored as the expected profit now plus a
  play-out of the rest of the deal under the most likely hypotheses, through a square-root
  utility that matches how the event is scored.
- **Steering readers.** An opponent that believes my quotes can be steered: when my position
  is at the 10-lot limit, an extreme quote costs nothing and pulls a reader into bad trades.
- **Swap.** Throws away the lowest card when it expects to end long and the highest when
  short, if the expected gain is large enough.
- **Speed.** The arena allows 50 ms per call. marseille plays the same strategy as the
  version before it (bogota) with about 40% less work per call.

## Layout

| Path | What |
|---|---|
| `engine.py`, `rules.py`, `backtester.py`, `bot_loader.py`, `starter_bot.py`, `strategies/` | the organisers' kit: game engine, rules, local duels, entry checker, starter and house bots |
| `heist/` | final stage: versions named after cities (up to `bogota` and `marseille`), the live-field census (`FIELD.md`), split tests |
| `zoo/` | earlier candidate bots |
| `versions/`, `avengers/`, `final/` | earlier versions, ledgers and upload notes |
| `tools/` | local testing: `eval.py` scores a bot against a pool, `trace.py` shows what a bot believed through one deal, `speed.py` measures call times, `live_ab.py` compares our uploads on the public fight list |
| `prompts/` | prompts given to Claude |

The opponent files (`heist/opp/`, `avengers/opp/`, `zoo/arena_*.py`) are **imitations we
fitted to other teams' public replays**, not their code. Each says so in its header.

## Try it

Python 3.10+, standard library only.

```bash
python backtester.py heist/marseille.py sharp --deals 1000   # duel a house bot
python tools/eval.py heist/marseille.py                       # score against a pool
python tools/trace.py heist/marseille.py reader               # watch one deal
```
