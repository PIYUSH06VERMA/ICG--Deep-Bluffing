"""
cfr_trainer.py
----------------
Trains a Counterfactual Regret Minimization (CFR) strategy for Heads-Up
Limit Hold'em, using CARD ABSTRACTION to make the problem tractable.

WHY ABSTRACTION?
Full-card CFR for HULHE has an enormous number of states (billions+). Real
poker bots (e.g. Libratus, Pluribus) handle this with "abstraction": group
similar hands into a small number of buckets and solve CFR over the much
smaller abstracted game. We do the same here with 5 hand-strength buckets
(0 = weakest, 4 = strongest), based on estimated win probability vs a
random opponent hand (the same Chen Formula / Monte Carlo estimator used
in the baseline agent).

MODELING CHOICES (documented here for the LaTeX report):
1. Bucket definition: 5 equal-width bins over estimated win probability
   [0, 1] -> buckets 0-4.
2. Street-to-street bucket evolution: modeled as a small random walk
   (delta -1/0/+1 with probabilities 0.2/0.6/0.2). This reflects that a
   hand's relative strength shifts somewhat as community cards are
   revealed, without requiring us to track exact cards during training.
3. Showdown resolution: since we don't track exact cards during CFR
   training, we approximate P(bucket A beats bucket B) as a monotonic
   function of the bucket gap (similar in spirit to an Elo win-probability
   curve), calibrated to reasonable poker intuition (bigger bucket gap =
   much higher win probability; equal buckets = 50/50 in expectation).
4. Betting abstraction: the *exact* fixed-limit betting rules from the
   assignment are preserved (bet sizes 2/2/4/4, cap of 4 bets/raises per
   street, heads-up turn order). Only the CARDS are abstracted, not the
   betting structure.

ALGORITHM: External-Sampling Monte Carlo CFR (Lanctot et al., 2009). For
the traversing player we explore all legal actions (needed for regret
computation); for the opponent and for chance events (bucket transitions)
we sample a single outcome according to the current strategy / chance
distribution. This is far cheaper than full vanilla CFR while still
provably converging to a Nash equilibrium of the abstracted game.

Output: cfr_strategy.json, a lookup table from infoset -> action
probabilities, loaded by agent.py at decision time.
"""

import json
import random

NUM_BUCKETS = 5
STREETS = 4  # 0=preflop, 1=flop, 2=turn, 3=river
BET_SIZE = [2, 2, 4, 4]
MAX_BETS_PER_STREET = 4
ACTIONS = ['FOLD', 'CALL', 'RAISE']

# Rough distribution of preflop bucket assignments (most starting hands are
# mediocre; only a small fraction are premium). Calibrated loosely against
# the Chen Formula's win-probability range (~0.30 to ~0.85).
PREFLOP_BUCKET_DIST = [0.05, 0.35, 0.35, 0.20, 0.05]

# Street-to-street bucket "random walk" transition model
BUCKET_TRANSITIONS = [(-1, 0.2), (0, 0.6), (1, 0.2)]

# Showdown win probability as a function of (traverser_bucket - opponent_bucket)
SHOWDOWN_TABLE = {
    4: 0.95, 3: 0.85, 2: 0.75, 1: 0.65, 0: 0.50,
    -1: 0.35, -2: 0.25, -3: 0.15, -4: 0.05,
}


def sample_preflop_bucket():
    r = random.random()
    cum = 0.0
    for i, p in enumerate(PREFLOP_BUCKET_DIST):
        cum += p
        if r < cum:
            return i
    return NUM_BUCKETS - 1


def sample_bucket_transition(bucket):
    r = random.random()
    cum = 0.0
    for delta, p in BUCKET_TRANSITIONS:
        cum += p
        if r < cum:
            return max(0, min(NUM_BUCKETS - 1, bucket + delta))
    return bucket


def showdown_win_prob(traverser_bucket, opponent_bucket):
    diff = max(-4, min(4, traverser_bucket - opponent_bucket))
    return SHOWDOWN_TABLE[diff]


def legal_actions(bets_count, is_facing_bet):
    acts = []
    if is_facing_bet:
        acts.append('FOLD')
    acts.append('CALL')
    if bets_count < MAX_BETS_PER_STREET:
        acts.append('RAISE')
    return acts


def get_strategy(infoset_key, legal, regret_sum):
    """Regret matching: strategy proportional to positive regret."""
    rk = regret_sum.get(infoset_key)
    if rk is None:
        p = 1.0 / len(legal)
        return {a: (p if a in legal else 0.0) for a in ACTIONS}
    positive = {a: max(rk[a], 0.0) for a in legal}
    total = sum(positive.values())
    if total > 0:
        return {a: (positive[a] / total if a in legal else 0.0) for a in ACTIONS}
    p = 1.0 / len(legal)
    return {a: (p if a in legal else 0.0) for a in ACTIONS}


def sample_action(strat, legal):
    r = random.random()
    cum = 0.0
    for a in legal:
        cum += strat[a]
        if r <= cum:
            return a
    return legal[-1]


def step(traverser, street, bets_count, acted_count, to_act, buckets, contrib,
         action, regret_sum, strategy_sum):
    other = 1 - to_act

    if action == 'FOLD':
        pot = contrib[0] + contrib[1]
        if other == traverser:
            return pot - contrib[traverser]
        return -contrib[traverser]

    new_contrib = list(contrib)
    new_bets_count = bets_count

    if action == 'CALL':
        to_call = max(contrib[other] - contrib[to_act], 0)
        new_contrib[to_act] += to_call
    else:  # RAISE
        to_call = max(contrib[other] - contrib[to_act], 0)
        new_contrib[to_act] += to_call + BET_SIZE[street]
        new_bets_count = bets_count + 1

    new_acted = acted_count + 1

    if action == 'RAISE':
        return traverse(traverser, street, new_bets_count, new_acted, True,
                         other, buckets, new_contrib, regret_sum, strategy_sum)

    # action == 'CALL' -- did that close the street?
    if new_acted >= 2:
        if street == STREETS - 1:  # river -> showdown
            p = showdown_win_prob(buckets[traverser], buckets[1 - traverser])
            pot = new_contrib[0] + new_contrib[1]
            return p * pot - new_contrib[traverser]
        # move to next street
        new_buckets = [sample_bucket_transition(buckets[0]),
                        sample_bucket_transition(buckets[1])]
        return traverse(traverser, street + 1, 0, 0, False, 1, new_buckets,
                         new_contrib, regret_sum, strategy_sum)

    # street continues (this was the first check of a postflop street)
    return traverse(traverser, street, new_bets_count, new_acted, False,
                     other, buckets, new_contrib, regret_sum, strategy_sum)


def traverse(traverser, street, bets_count, acted_count, is_facing_bet,
             to_act, buckets, contrib, regret_sum, strategy_sum):
    legal = legal_actions(bets_count, is_facing_bet)
    infoset_key = f"{buckets[to_act]}|{street}|{bets_count}|{int(is_facing_bet)}"

    if to_act == traverser:
        strat = get_strategy(infoset_key, legal, regret_sum)
        action_utils = {}
        node_util = 0.0
        for a in legal:
            u = step(traverser, street, bets_count, acted_count, to_act,
                      buckets, contrib, a, regret_sum, strategy_sum)
            action_utils[a] = u
            node_util += strat[a] * u

        rk = regret_sum.setdefault(infoset_key, {a: 0.0 for a in ACTIONS})
        for a in legal:
            rk[a] += (action_utils[a] - node_util)

        sk = strategy_sum.setdefault(infoset_key, {a: 0.0 for a in ACTIONS})
        for a in legal:
            sk[a] += strat[a]

        return node_util
    else:
        strat = get_strategy(infoset_key, legal, regret_sum)
        a = sample_action(strat, legal)
        return step(traverser, street, bets_count, acted_count, to_act,
                     buckets, contrib, a, regret_sum, strategy_sum)


def train(iterations):
    regret_sum = {}
    strategy_sum = {}

    for i in range(iterations):
        b0 = sample_preflop_bucket()
        b1 = sample_preflop_bucket()
        for traverser in (0, 1):
            # Preflop start: blinds already posted (SB=1, BB=2), SB acts
            # first and is "facing" the BB's blind (bets_count=1).
            traverse(traverser, 0, 1, 0, True, 0, [b0, b1], [1, 2],
                      regret_sum, strategy_sum)

        if (i + 1) % 5000 == 0:
            print(f"  iteration {i + 1}/{iterations}  ({len(strategy_sum)} infosets seen)")

    return strategy_sum


def extract_average_strategy(strategy_sum):
    avg_strategy = {}
    for infoset_key, sums in strategy_sum.items():
        total = sum(sums.values())
        if total > 0:
            avg_strategy[infoset_key] = {a: sums[a] / total for a in ACTIONS}
        else:
            avg_strategy[infoset_key] = {a: 1.0 / len(ACTIONS) for a in ACTIONS}
    return avg_strategy


if __name__ == "__main__":
    import time
    ITERATIONS = 300000

    print(f"Training CFR over {ITERATIONS} iterations (abstracted 5-bucket game)...")
    start = time.time()
    strategy_sum = train(ITERATIONS)
    elapsed = time.time() - start
    print(f"Training complete in {elapsed:.1f}s. Infosets discovered: {len(strategy_sum)}")

    avg_strategy = extract_average_strategy(strategy_sum)

    with open("cfr_strategy.json", "w") as f:
        json.dump(avg_strategy, f, indent=2)
    print(f"Saved {len(avg_strategy)} infoset strategies to cfr_strategy.json")
