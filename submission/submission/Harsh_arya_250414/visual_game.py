import pygame
import random
import math
from agent import CustomPokerBot, create_deck, best_hand

# CONFIGURATION
WIDTH, HEIGHT = 1280, 720
FPS = 60
BG_COLOR = (34, 112, 63)  

P1_COORDS = [(400, 500), (480, 500)]  
P2_COORDS = [(400, 100), (480, 100)]  
FLOP_COORDS = [(450, 300), (530, 300), (610, 300), (690, 300), (770, 300)]  
DEALER_START_POS = (WIDTH // 2, HEIGHT + 50)  

SUIT_COLORS = {'h': (235, 64, 52), 'd': (52, 131, 235), 'c': (40, 163, 75), 's': (30, 30, 30)}

class VisualCard:
    def __init__(self, card_str):
        self.card_str = card_str
        self.rank_str = card_str[0]
        self.suit = card_str[1]
        self.current_pos = list(DEALER_START_POS)
        self.target_pos = list(DEALER_START_POS)
        self.animation_complete = False

    def set_target(self, pos):
        self.target_pos = list(pos)
        self.animation_complete = False

    def update(self):
        if self.animation_complete: return
        dx = self.target_pos[0] - self.current_pos[0]
        dy = self.target_pos[1] - self.current_pos[1]
        distance = math.sqrt(dx**2 + dy**2)
        speed = 25  
        if distance < speed:
            self.current_pos = self.target_pos.copy()
            self.animation_complete = True
        else:
            self.current_pos[0] += (dx / distance) * speed
            self.current_pos[1] += (dy / distance) * speed

    def draw(self, surface, font):
        card_width, card_height = 70, 100
        rect = pygame.Rect(int(self.current_pos[0]), int(self.current_pos[1]), card_width, card_height)
        pygame.draw.rect(surface, (255, 255, 255), rect, border_radius=8)
        pygame.draw.rect(surface, (180, 180, 180), rect, width=2, border_radius=8)
        color = SUIT_COLORS[self.suit]
        text_surf = font.render(f"{self.rank_str}{self.suit.upper()}", True, color)
        surface.blit(text_surf, (rect.x + 8, rect.y + 8))

class VisualPokerGame:
    def __init__(self):
        self.my_bot = CustomPokerBot("DeepBluff")
        self.raw_deck = create_deck()
        random.shuffle(self.raw_deck)
        
        self.p1_raw = [self.raw_deck.pop(), self.raw_deck.pop()]
        self.p2_raw = [self.raw_deck.pop(), self.raw_deck.pop()]
        self.board_raw = [self.raw_deck.pop(), self.raw_deck.pop(), self.raw_deck.pop(), self.raw_deck.pop(), self.raw_deck.pop()]
        
        self.p1_cards = [VisualCard(c) for c in self.p1_raw]
        self.p2_cards = [VisualCard(c) for c in self.p2_raw]
        self.board_cards = [VisualCard(c) for c in self.board_raw]
        
        self.all_cards = []
        self.step = 0
        self.winner_text = ""
        self.last_action = "Waiting..."
        self.deal_next()

    def deal_next(self):
        if self.step == 0:
            for i, c in enumerate(self.p1_cards):
                c.set_target(P1_COORDS[i])
                self.all_cards.append(c)
            self.last_action = self.my_bot.get_action(self.p1_raw, [], 20, 1000, 0, ["CHECK", "RAISE"])
            self.step += 1
        elif self.step == 1:
            for i, c in enumerate(self.p2_cards):
                c.set_target(P2_COORDS[i])
                self.all_cards.append(c)
            self.step += 1
        elif self.step == 2:
            for i, c in enumerate(self.board_cards):
                c.set_target(FLOP_COORDS[i])
                self.all_cards.append(c)
            
            self.last_action = self.my_bot.get_action(self.p1_raw, self.board_raw[:3], 40, 980, 10, ["CALL", "RAISE", "FOLD"])
            
            p1_s = best_hand(self.p1_raw + self.board_raw)
            p2_s = best_hand(self.p2_raw + self.board_raw)
            if p1_s > p2_s: self.winner_text = "DeepBluff WINS!"
            elif p2_s > p1_s: self.winner_text = "Opponent WINS!"
            else: self.winner_text = "SPLIT POT!"
            self.step += 1

    def update(self):
        for c in self.all_cards: c.update()
        if all(c.animation_complete for c in self.all_cards) and self.step < 3:
            pygame.time.delay(500)
            self.deal_next()

    def draw(self, screen, font, big_font):
        screen.blit(font.render("Opponent Cards", True, (255, 255, 255)), (400, 40))
        screen.blit(font.render(f"DeepBluff (Your Bot Action: {self.last_action})", True, (255, 255, 255)), (400, 620))
        screen.blit(font.render("Press SPACEBAR for Next Hand", True, (240, 240, 100)), (20, HEIGHT - 40))
        
        for c in self.all_cards: c.draw(screen, font)
        
        if self.winner_text:
            t = big_font.render(self.winner_text, True, (255, 215, 0))
            screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 + 150))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DeepBluff Bot Visual Simulator")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24, bold=True)
    big_font = pygame.font.SysFont("impact", 60)
    
    game = VisualPokerGame()
    running = True
    while running:
        clock.tick(FPS)
        screen.fill(BG_COLOR)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game = VisualPokerGame()
        game.update()
        game.draw(screen, font, big_font)
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()