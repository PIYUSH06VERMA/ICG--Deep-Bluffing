# ICG--Deep-Bluffing
Official repository of ICG-Summer Project 2026-27-Deep Bluffing

Welcome to Project Deep-Bluffing! The goal of this project is to build an autonomous AI bot capable of playing poker. 

# Capstone Challenge: Heads-Up Limit Hold'em (HULHE)

### **The Mission**
Balancing a pole on a cart was a perfect-information environment where you could see every variable. Now, it is time to step into the real world: **Imperfect Information**. 

Your final capstone challenge is to design, engineer, and train an autonomous AI agent capable of playing **Heads-Up Limit Texas Hold'em (HULHE)**. 

To prove your software engineering fundamentals, you will not be relying on pre-built poker libraries. You must architect the underlying game engine logic from scratch using Object-Oriented Python, and then build a bot smart enough to dominate the game tree.

---

### **Game Specifications (The Scope)**
To ensure the mathematics remain discrete and the game-tree branching factors are clean and manageable, we are enforcing the following strict architectural rules:
* **Format:** Heads-Up (1-vs-1). No multi-way pots.
* **Betting Structure:** **Limit Hold'em**. You cannot bet arbitrary chip amounts. At any decision point, your bot only has three discrete choices: `FOLD`, `CALL`, or `RAISE` (by a strictly fixed limit increment). 
* **The Deck:** A standard 52-card deck.

---
### **Crash Course: Game Sequence & Hand Rankings**
If you have never played Texas Hold'em, here is the exact sequence of events and how to determine the winner.

**The Street Sequence:**
1. **Pre-Flop:** Players receive 2 private Hole Cards. (First betting round).
2. **The Flop:** 3 public Community Cards are dealt face-up in the middle. (Second betting round).
3. **The Turn:** 1 additional Community Card is dealt. (Third betting round).
4. **The River:** 1 final Community Card is dealt. (Final betting round).
5. **Showdown:** If neither player has folded, both reveal their hands.

**Hand Rankings (From Strongest to Weakest):**
Your bot must find the best possible 5-card hand out of the 7 available cards.
1. **Royal Flush:** A, K, Q, J, 10 all of the same suit.
2. **Straight Flush:** 5 consecutive cards of the same suit.
3. **Four of a Kind (Quads):** 4 cards of the same rank.
4. **Full House:** 3 of a kind PLUS a pair.
5. **Flush:** Any 5 cards of the same suit (not consecutive).
6. **Straight:** 5 consecutive cards of mixed suits.
7. **Three of a Kind (Trips/Set):** 3 cards of the same rank.
8. **Two Pair:** Two different pairs.
9. **One Pair:** Two cards of the same rank.
10. **High Card:** Highest single card wins.

*Note on Ties (Kickers):* If both players have the same hand (e.g., both have a Pair of Aces), the winner is determined by the highest remaining cards in their 5-card hand, known as "kickers".

### **Mechanical Rules**
If you are new to poker, you must ensure your game engine implements these three specific mechanics correctly:

**1. Action Definitions:**
* **FOLD:** The player surrenders their cards and forfeits any chips they have put in the pot. The hand immediately ends, and the opponent wins the pot.
* **CALL:** The player matches the current `amount_to_call` to stay in the hand. (If the `amount_to_call` is 0, this action is known as a "Check").
* **RAISE:** The player puts in the `amount_to_call` PLUS the current fixed betting increment (Small Bet or Big Bet).

**2. Heads-Up Turn Order (Engine Logic):**
Heads-Up poker has a specific rule for who acts first, and the order flips after the first round:
* **Pre-Flop:** The Small Blind (Dealer) acts **first**, and the Big Blind acts **second**.
* **Post-Flop (Flop, Turn, River):** The Big Blind acts **first**, and the Small Blind (Dealer) acts **second**. 

**3. Split Pots (Ties):**
* If both players reach the showdown and have the exact same winning 5-card hand (including all tie-breaking kickers), it is a tie. The pot must be split evenly (50/50) between both players.

### **Detailed Game Mechanics & Bankroll**
To ensure all bots operate on a standardized mathematical state space, the tournament arena will enforce the following strict monetary and betting parameters:

1. **Initial Bankroll (The Stack):** At the beginning of every individual hand, both players are reset to a fresh stack of exactly **100 Chips**. Stacks do not carry over across hands; each hand is an isolated episodic simulation.
2. **The Forced Blinds:** 
   * **Small Blind (SB):** 1 Chip (posted automatically by the Dealer/Button).
   * **Big Blind (BB):** 2 Chips (posted automatically by the Non-Dealer).
3. **Fixed-Limit Betting Structure (The Raise Value):**
   You(mentees) **must not** define or choose the raise value. The arena dynamically enforces standard structured limit rules across the betting rounds:
   * **Pre-Flop & Flop:** The betting increment is fixed to a **Small Bet of 2 Chips**. Any `RAISE` action adds exactly 2 chips to the current highest bet.
   * **Turn & River:** The betting increment doubles to a **Big Bet of 4 Chips**. Any `RAISE` action adds exactly 4 chips to the current highest bet.
4. **The Cap Rule:** To prevent infinite betting loops, each street is limited to a maximum of **4 total bets** (1 initial bet + 3 raises). Once the betting is capped, the only legal actions remaining for the players are `CALL` or `FOLD`.

### **Technical Constraints & Rules**
This is a comprehensive test of pure algorithmic logic and clean software design. 

**NOT ALLOWED:**
* External poker simulation or evaluation libraries (e.g., `RLCard`, `PyPokerEngine`, `treys`).
* Hard-coded pre-computed lookup strategy tables downloaded from the internet.

**ALLOWED:**
* Machine Learning & Numerics: `numpy`, `torch`, `math`.
* Python Standard Libraries: `itertools`, `collections`, `random`.
* **Strategy Archetype:** You are free to explore any methodology. You can adapt your Deep Q-Network (DQN) architecture to handle hidden states, build a Monte Carlo Tree Search (MCTS) rollout framework, implement Counterfactual Regret Minimization (CFR), or design deep mathematical Expected Value (EV) heuristics.

---

### **The Architecture Blueprint & API (CRITICAL)**
Your bot will be dynamically extracted and loaded into a master tournament arena to play thousands of hands against your peers. **If your bot does not inherit from the base class or changes this exact function signature, it will crash the arena and receive a 0.**

Your code structure must provide a designated main entry point file named exactly `agent.py`. Inside `agent.py`, implement your agent using this exact class template:

```python
class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        """
        Calculates the optimal move for Limit Texas Hold'em.
        
        Parameters:
        - hole_cards (list): Your two private cards, e.g., ['Ah', 'Kd']
        - community_cards (list): Shared public cards, e.g., ['7s', '7c', '2d'] (Empty pre-flop)
        - pot_size (int): Total chips currently in the middle pot
        - stack_size (int): Your remaining chips in your stack
        - amount_to_call (int): Chips required to put in to stay in the hand
        - legal_actions (list): Available valid moves, e.g., ['FOLD', 'CALL', 'RAISE']
        
        Returns:
        - A string exactly matching ONE of the elements in legal_actions.
        """
        raise NotImplementedError("Your bot logic goes here!")

# Implement your subclass here
class CustomPokerBot(BasePokerBot):
    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        # Your custom decision network / game theory logic goes here
        # Return string: 'FOLD', 'CALL', or 'RAISE'
        pass
```
*Note: Cards are represented as strings, where the first character is the rank (`2`-`9`, `T`, `J`, `Q`, `K`, `A`) and the second character is the suit lowercase (`h` for hearts, `d` for diamonds, `c` for clubs, `s` for spades).*

### **The Research Board (Where to Start)**
Since you are building the card evaluation and engine yourself, utilize these built-in Python paradigms to avoid writing convoluted spaghetti code:
* **Python OOP Magic:** Implement dunder methods (`__eq__`, `__lt__`, `__gt__`) on a custom `Card` object to make sorting hands and comparing absolute values trivial. You can refer cherno's cpp playlist. For python particularly, you can refer [this](https://youtu.be/Mf2RdpEiXjU?si=9yL8XBqiNFBGRVL8)  
* **Hand Combinations:** Use `itertools.combinations` to easily extract the best 5-card combinations out of the 7 available cards (2 hole cards + 5 community cards).
* **Card Frequency Counting:** Use `collections.Counter` to check for pairs, pairs of pairs, trips, full houses, and matching flush suits effortlessly.
* **Game Theory Context:** Read up on *Monte Carlo Simulations/Rollouts* (simulating random outcomes from the current state to gauge hand strength) and *Expected Value calculations* ($EV = [\text{Probability of Winning} \times \text{Pot Size}] - [\text{Probability of Losing} \times \text{Amount to Call}]$).

---

### **Evaluation & Grading Rubric**
Your project grade is split evenly between programmatic execution and your theoretical approach:
* **75% — The Master Tournament:** Your agent folder will be compiled, and your bot will run through a grueling round-robin tournament (playing 10,000 hands against baseline agents and your peers). Points are awarded based on stability, invalid action avoidance, and cumulative win-rate performance.
* **25% — The LaTeX Defense (`report.pdf`):** You must submit a professional academic report compiled strictly in LaTeX. You must mathematically justify your state representation (how you quantized cards/hand strength into numeric features), your reward shaping mechanics (if using Reinforcement Learning), or your mathematical heuristics architecture.

---

### **How to Submit Your Solution**
We are utilizing a Pull Request (PR) workflow on our central repository. Follow these exact guidelines:
1. **Fork this repository** to your personal GitHub account.
2. **Clone your fork** locally to build out your modules. You are free to use multiple files (`model.py`, `utils.py`, etc.) to keep your code clean, modular, and professional.
3. **Create your submission directory** inside the `submissions/` folder. Your folder must be named exactly according to your name and roll number:  
    `submissions/firstname_lastname_rollnumber/`
4. **Organize your deliverables** directly within your personal folder:
   ```text
   submissions/firstname_lastname_rollnumber/
   ├── agent.py        # CRITICAL: Main entry point containing your custom bot class
   ├── report.pdf      # Compulsory strategy defense compiled from LaTeX
   └── [Any additional helper scripts, custom modules, or saved PyTorch .pth weights]
   ```
5. Open a Pull Request (PR) from your completed fork back to the main repository before the announced deadline.

### ALL THE BEST!