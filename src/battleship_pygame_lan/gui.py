import pygame

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 120, 215)
HOVER_COLOR = (0, 100, 180)


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.font_title = pygame.font.SysFont("Arial", 80, bold=True)
        self.font_button = pygame.font.SysFont("Arial", 40)

        # Definicja przycisków (Tekst, środek Y)
        self.buttons = [
            {"text": "START", "pos_y": 300, "action": "play"},
            {"text": "OPCJE", "pos_y": 400, "action": "options"},
            {"text": "WYJŚCIE", "pos_y": 500, "action": "quit"},
        ]

    def draw(self):
        self.screen.fill(BLACK)

        # Rysowanie tytułu
        title_surf = self.font_title.render("STATKI", True, WHITE)
        title_rect = title_surf.get_rect(center=(self.screen_rect.centerx, 150))
        self.screen.blit(title_surf, title_rect)

        # Pobranie pozycji myszy
        mouse_pos = pygame.mouse.get_pos()

        # Rysowanie przycisków
        for btn in self.buttons:
            text_color = WHITE
            # Tworzenie rect dla detekcji najechania myszą
            text_surf = self.font_button.render(btn["text"], True, text_color)
            rect = text_surf.get_rect(center=(self.screen_rect.centerx, btn["pos_y"]))

            if rect.collidepoint(mouse_pos):
                text_surf = self.font_button.render(btn["text"], True, BLUE)
                # Opcjonalnie: lekkie powiększenie lub tło

            self.screen.blit(text_surf, rect)
            btn["rect"] = rect  # Zapisujemy rect do obsługi kliknięć

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Lewy przycisk myszy
                for btn in self.buttons:
                    if btn["rect"].collidepoint(event.pos):
                        return btn["action"]
        return None
