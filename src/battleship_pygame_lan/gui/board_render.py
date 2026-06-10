import pygame


class BoardRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", 14)
        self.label_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.cell_size = 35
        self.grid_size = 10
        self.grid_step = self.cell_size + 1

    def draw(self, board_object, ox, oy, title):
        if board_object is None:
            return

        # Rysowanie tytułu planszy nad nią
        title_surf = self.label_font.render(title, True, (210, 220, 255))
        self.screen.blit(title_surf, (ox + 25, oy - 20))

        # Rysowanie nagłówków kolumn (A-J)
        for col in range(self.grid_size):
            label = self.font.render(chr(ord("A") + col), True, (140, 140, 140))
            self.screen.blit(label, (ox + 25 + col * self.grid_step + 12, oy + 2))

        # Pobranie wewnętrznej reprezentacji macierzy 10x10 z Twojego oryginalnego silnika
        cells_grid = board_object
        if hasattr(board_object, "get_grid_state"):
            try:
                cells_grid = board_object.get_grid_state()
            except:
                pass
        elif hasattr(board_object, "grid"):
            cells_grid = board_object.grid

        # Rysowanie właściwych wierszy i kafelków siatki
        for row in range(self.grid_size):
            # Numery wierszy (1-10)
            row_label = self.font.render(str(row + 1), True, (140, 140, 140))
            self.screen.blit(row_label, (ox + 4, oy + 25 + row * self.grid_step + 8))

            for col in range(self.grid_size):
                rect = pygame.Rect(
                    ox + 25 + col * self.grid_step,
                    oy + 25 + row * self.grid_step,
                    self.cell_size,
                    self.cell_size,
                )

                # Renderowanie domyślnego koloru tła oceanu
                pygame.draw.rect(self.screen, (16, 28, 54), rect)

                # Bezpieczne wyciąganie wartości pola bez wywoływania błędów indeksu
                cell_val = None
                if cells_grid:
                    try:
                        cell_val = cells_grid[row][col]
                    except:
                        pass

                val_str = str(cell_val).upper() if cell_val is not None else ""

                # Mapowanie kolorów i stanów pól dokładnie z Twojego oryginalnego projektu
                if "SHIP" in val_str or val_str == "1":
                    pygame.draw.rect(
                        self.screen, (70, 80, 120), rect
                    )  # Czysty segment statku
                elif "HIT" in val_str:
                    pygame.draw.rect(self.screen, (70, 80, 120), rect)
                    pygame.draw.circle(
                        self.screen, (230, 40, 40), rect.center, 6
                    )  # Trafiony
                elif "MISS" in val_str or "WATER" in val_str:
                    pygame.draw.circle(
                        self.screen, (100, 110, 140), rect.center, 4
                    )  # Pudło
                elif "SUNK" in val_str:
                    pygame.draw.rect(self.screen, (30, 30, 40), rect)  # Zatopiony

                # Rysowanie krawędzi siatki
                pygame.draw.rect(self.screen, (32, 48, 82), rect, 1)

    def get_clicked_cell(self, mouse_pos, ox, oy):
        """Mapuje współrzędne myszy na indeksy tablicy (wiersz, kolumna)."""
        mx, my = mouse_pos
        board_total_size = self.grid_size * self.grid_step

        click_area = pygame.Rect(ox + 25, oy + 25, board_total_size, board_total_size)
        if click_area.collidepoint(mx, my):
            col = (mx - (ox + 25)) // self.grid_step
            row = (my - (oy + 25)) // self.grid_step
            if 0 <= col < self.grid_size and 0 <= row < self.grid_size:
                return (row, col)
        return None
