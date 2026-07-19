# Deep Bluffing — Starter Kit

## Files
- `card.py` — Card object (rank + suit, comparable)
- `deck.py` — 52-card deck, dealing, "unseen cards" helper
- `hand_evaluator.py` — finds best 5-card hand out of 7 cards, ranks it
- `agent.py` — **the required entry point.** Contains `BasePokerBot` and
  `CustomPokerBot`. This is what gets loaded into the tournament arena.
- `test_hand_evaluator.py` — proves the hand ranking math is correct
- `test_agent.py` — proves the bot makes sane decisions and never returns
  an illegal action

## How the bot thinks (in plain terms)
1. It doesn't know the opponent's cards or future community cards, so it
   *imagines* 100 random possible futures (Monte Carlo simulation) and
   checks how often it would win in each one. That gives a win probability.
2. It compares that win probability to the "pot odds" (how cheap it is to
   continue relative to the pot). If winning is more likely than what the
   pot odds require, it calls/raises. Otherwise it folds.

## Run this first, right now
```
cd deep_bluffing
python3 test_hand_evaluator.py
python3 test_agent.py
```
Both should print "ALL TESTS PASSED". This proves the code works before you
touch anything.

## What's still missing (things YOU should do next)
1. **Game engine** (betting rounds, blinds, turn order, pot management) —
   the assignment says the arena runs this for you, so you mainly need
   `agent.py` to be correct. But it's worth writing your own mini game loop
   locally so you can watch two bots play full hands and sanity-check
   behavior end to end. Ask me and I'll build it with you.
2. **Improve the bot** — the current strategy is a solid, honest baseline
   (this alone should survive the arena without crashing and play
   reasonably). To push win-rate higher later, you could:
   - Increase `simulations` if you have runtime budget
   - Add bluffing (occasionally raise with weak hands to stay unpredictable)
   - Try CFR (Counterfactual Regret Minimization) or a DQN — bigger lift,
     good report material
3. **report.pdf** — the 25% LaTeX defense. You already know how to explain
   this part in Hinglish to me — we can turn that into the formal write-up
   whenever you're ready (state representation = hole+community cards,
   reward shaping = EV-based pot odds, etc.)

## Submission checklist (from the assignment)
- [ ] Fork the repo
- [ ] Folder: `submissions/firstname_lastname_rollnumber/`
- [ ] `agent.py` inside that folder (this file, or your improved version)
- [ ] `report.pdf` compiled from LaTeX
- [ ] Open a PR before the deadline
