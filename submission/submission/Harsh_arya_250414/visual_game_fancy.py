import pygame
import random
import math
from agent import CustomPokerBot, create_deck, best_hand

# =====================================================================
# CONFIGURATION & MODERN DARK PALETTE
# =====================================================================
WIDTH, HEIGHT = 1280, 720
FPS = 60

BG_DARK = (15, 23, 42)        # Deep slate background
TABLE_COLOR = (16, 75, 46)     # Rich poker green
BORDER_COLOR = (234, 179, 8)   # Gold border
CARD_BG = (255, 255, 255)    
CARD_BORDER = (226, 232, 240)

SUIT_COLORS = {
    'h': (239, 68, 68),   # Vibrant Red
    'd': (59, 130, 246),  # Modern Blue
    'c': (34, 197, 94),   # Emerald Green
    's': (30, 41, 59)     # Dark Slate
}

SUIT_SYMBOLS = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}

P1_COORDS = [(530, 520), (670, 520)]  
P2_COORDS = [(530, 80), (670, 80)]  
BOARD_COORDS = [(370, 300), (480, 300), (590, 300), (700, 300), (810, 300)]
DEALER_START_POS = (WIDTH // 2, -100)  # Top center se cards aayenge

class FancyVisualCard:
    def __init__(self, card_str):
        self.card_str = card_str
        self.rank = card_str[0]
        self.suit = card_str[1]
        self.current_pos = list(DEALER_START_POS)
        self.target_pos = list(DEALER_START_POS)
        
        # Flip & Animation flags
        self.is_revealed = False      # Card front dikhana hai ya nahi
        self.should_reveal = False    # Target par pahunchne ke baad flip hona hai ya nahi
        self.animation_complete = False
        self.flip_width = 80          # Animation ke liye dynamic width

    def set_target(self, pos, should_reveal=False):
        self.target_pos = list(pos)
        self.should_reveal = should_reveal
        self.animation_complete = False

    def update(self):
        # 1. Move Animation (Easing effect)
        if not self.animation_complete:
            dx = self.target_pos[0] - self.current_pos[0]
            dy = self.target_pos[1] - self.current_pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 2:
                self.current_pos = self.target_pos.copy()
                self.animation_complete = True
            else:
                # Easing: paas aane par speed halki kam hogi jo smooth lagti hai
                speed = max(2, distance * 0.25) 
                self.current_pos[0] += (dx / distance) * speed
                self.current_pos[1] += (dy / distance) * speed

        # 2. Smooth Flip Animation
        if self.animation_complete and self.should_reveal and not self.is_revealed:
            self.flip_width -= 10  # Shrink card horizontally
            if self.flip_width <= 0:
                self.is_revealed = True
        
        if self.is_revealed and self.flip_width < 80:
            self.flip_width += 10  # Expand card back with front face
            if self.flip_width > 80:
                self.flip_width = 80

    def draw(self, surface, font, big_font):
        card_h = 120
        x = int(self.current_pos[0] + (80 - self.flip_width) // 2)
        y = int(self.current_pos[1])
        
        if self.flip_width <= 0: return
        
        rect = pygame.Rect(x, y, self.flip_width, card_h)
        shadow_rect = pygame.Rect(x + 4, y + 4, self.flip_width, card_h)
        pygame.draw.rect(surface, (15, 23, 42, 100), shadow_rect, border_radius=10)
        
        if self.is_revealed:
            pygame.draw.rect(surface, CARD_BG, rect, border_radius=10)
            pygame.draw.rect(surface, CARD_BORDER, rect, width=2, border_radius=10)
            
            if self.flip_width > 40: # Only draw text if card is wide enough
                color = SUIT_COLORS[self.suit]
                sym = SUIT_SYMBOLS[self.suit]
                
                corner_txt = font.render(f"{self.rank}", True, color)
                surface.blit(corner_txt, (x + 8, y + 6))
                
                center_txt = big_font.render(sym, True, color)
                cx = x + (self.flip_width // 2) - (center_txt.get_width() // 2)
                cy = y + (card_h // 2) - (center_txt.get_height() // 2)
                surface.blit(center_txt, (cx, cy))
        else:
            # Card Back Design
            pygame.draw.rect(surface, (29, 78, 216), rect, border_radius=10)
            pygame.draw.rect(surface, (255, 255, 255), rect, width=3, border_radius=10)
            if self.flip_width > 20:
                pygame.draw.rect(surface, (30, 58, 138), rect.inflate(-10, -10), border_radius=6)


class FancyPokerGame:
    def __init__(self):
        self.my_bot = CustomPokerBot("DeepBluff")
        self.raw_deck = create_deck()
        random.shuffle(self.raw_deck)
        
        self.p1_raw = [self.raw_deck.pop(), self.raw_deck.pop()]
        self.p2_raw = [self.raw_deck.pop(), self.raw_deck.pop()]
        self.board_raw = [self.raw_deck.pop(), self.raw_deck.pop(), self.raw_deck.pop(), self.raw_deck.pop(), self.raw_deck.pop()]
        
        self.p1_cards = [FancyVisualCard(c) for c in self.p1_raw]
        self.p2_cards = [FancyVisualCard(c) for c in self.p2_raw]
        self.board_cards = [FancyVisualCard(c) for c in self.board_raw]
        
        self.all_cards = []
        self.queue_cards = [] # Queue for dealing one by one
        
        self.state = 'START'  # START, DEAL_HOLE, FLOP, TURN, RIVER, SHOWDOWN
        self.winner_text = ""
        self.bot_action = "Waiting..."
        
        # Auto-trigger first deal
        self.deal_next()

    def deal_next(self):
        # Active animations check
        if self.queue_cards or not all(c.animation_complete and c.flip_width == 80 for c in self.all_cards):
            return

        if self.state == 'START':
            # Deal Player 1 cards (Revealed)
            for i, c in enumerate(self.p1_cards):
                self.queue_cards.append((c, P1_COORDS[i], True))
            # Deal Player 2 cards (Hidden)
            for i, c in enumerate(self.p2_cards):
                self.queue_cards.append((c, P2_COORDS[i], False))
                
            self.bot_action = self.my_bot.get_action(self.p1_raw, [], 20, 1000, 0, ["CHECK", "RAISE"])
            self.state = 'DEAL_HOLE'
            
        elif self.state == 'DEAL_HOLE':
            # Flop: 3 cards one by one
            for i in range(3):
                self.queue_cards.append((self.board_cards[i], BOARD_COORDS[i], True))
            self.bot_action = self.my_bot.get_action(self.p1_raw, self.board_raw[:3], 40, 980, 10, ["CALL", "RAISE", "FOLD"])
            self.state = 'FLOP'
            
        elif self.state == 'FLOP':
            # Turn: 4th card
            self.queue_cards.append((self.board_cards[3], BOARD_COORDS[3], True))
            self.bot_action = self.my_bot.get_action(self.p1_raw, self.board_raw[:4], 60, 960, 20, ["CALL", "RAISE", "FOLD"])
            self.state = 'TURN'
            
        elif self.state == 'TURN':
            # River: 5th card
            self.queue_cards.append((self.board_cards[4], BOARD_COORDS[4], True))
            self.bot_action = self.my_bot.get_action(self.p1_raw, self.board_raw, 80, 940, 20, ["CALL", "RAISE", "FOLD"])
            self.state = 'RIVER'
            
        elif self.state == 'RIVER':
            # Showdown: Reveal opponent cards
            for c in self.p2_cards:
                c.should_reveal = True
                
            p1_s = best_hand(self.p1_raw + self.board_raw)
            p2_s = best_hand(self.p2_raw + self.board_raw)
            if p1_s > p2_s: self.winner_text = "🏆 DeepBluff WINS! 🏆"
            elif p2_s > p1_s: self.winner_text = "Opponent WINS!"
            else: self.winner_text = "🤝 It's a TIE! 🤝"
            self.state = 'SHOWDOWN'

    def update(self):
        # Manage One-by-One Dealing Queue
        if self.queue_cards:
            # Check if the last card added to screen has finished its journey
            if not self.all_cards or (self.all_cards[-1].animation_complete and self.all_cards[-1].flip_width == 80):
                card, coords, reveal = self.queue_cards.pop(0)
                card.set_target(coords, reveal)
                self.all_cards.append(card)

        for c in self.all_cards: 
            c.update()

    def draw(self, screen, font, big_font, score_font):
        # Drawing Poker Table
        table_rect = pygame.Rect(140, 80, 1000, 520)
        pygame.draw.ellipse(screen, (15, 23, 42), table_rect.inflate(20, 20)) 
        pygame.draw.ellipse(screen, BORDER_COLOR, table_rect.inflate(10, 10))  
        pygame.draw.ellipse(screen, TABLE_COLOR, table_rect)                  
        
        for c in self.all_cards: 
            c.draw(screen, font, big_font)
            
        opp_lbl = font.render("CHALLENGER (Opponent)", True, (241, 245, 249))
        screen.blit(opp_lbl, (WIDTH // 2 - opp_lbl.get_width() // 2, 35))
        
        bot_lbl = font.render(f"DeepBluff (Your Bot Action: {self.bot_action.upper()})", True, (251, 191, 36))
        screen.blit(bot_lbl, (WIDTH // 2 - bot_lbl.get_width() // 2, 655))
        
        # Smart Status/Instruction Bar
        if self.state != 'SHOWDOWN':
            inst_text = "Press SPACEBAR to deal next round"
        else:
            inst_text = "Game Over! Press SPACEBAR for New Match"
            
        inst_lbl = font.render(inst_text, True, (148, 163, 184))
        screen.blit(inst_lbl, (30, HEIGHT - 40))
        
        if self.winner_text:
            banner_surface = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
            banner_surface.fill((15, 23, 42, 230)) 
            screen.blit(banner_surface, (0, 435))
            
            pygame.draw.line(screen, BORDER_COLOR, (0, 435), (WIDTH, 435), 2)
            pygame.draw.line(screen, BORDER_COLOR, (0, 515), (WIDTH, 515), 2)
            
            t = score_font.render(self.winner_text, True, (253, 224, 71))
            screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 435 + (80 - t.get_height()) // 2))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DeepBluff Poker Arena")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont("segoe ui", 22, bold=True)
    big_font = pygame.font.SysFont("arial", 48, bold=True)
    score_font = pygame.font.SysFont("segoe ui", 32, bold=True)
    
    game = FancyPokerGame()
    running = True
    
    while running:
        clock.tick(FPS)
        screen.fill(BG_DARK) 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if game.state == 'SHOWDOWN':
                    game = FancyPokerGame()
                else:
                    game.deal_next()
                
        game.update()
        game.draw(screen, font, big_font, score_font)
        pygame.display.flip()
        
    pygame.quit()

if __name__ == "__main__":
    main()
    