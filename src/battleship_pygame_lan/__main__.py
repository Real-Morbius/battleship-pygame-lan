import logging
import socket
import sys
import time
from threading import Thread

import pygame

# 1. POPRAWNE IMPORTY ZGODNIE ZE STRUKTURĄ KATALOGÓW I DOKUMENTACJĄ
from battleship_pygame_lan.game_manager.game_manager import GameManager
from battleship_pygame_lan.logic.enums import ShipType

# Zgodnie z dokumentacją te enumy są udostępniane przez moduł network
from battleship_pygame_lan.network import GameState, ReadyType
from battleship_pygame_lan.network.server import NetworkServer


def main() -> None:
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        filename="battleships.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1000, 600))
    pygame.display.set_caption("Battleship LAN")
    clock = pygame.time.Clock()

    # Czcionka do wyświetlania IP w lewym dolnym rogu
    font_ip_hud = pygame.font.SysFont("Arial", 16)

    # Importy klas interfejsu użytkownika
    from battleship_pygame_lan.gui.board_render import BoardRenderer
    from battleship_pygame_lan.gui.main_menu import MainMenu

    menu = MainMenu(screen)
    renderer = BoardRenderer(screen)

    # Inicjalizacja głównych obiektów sieciowych gry
    gm: GameManager = None
    server_instance: NetworkServer = None

    game_state = "MENU"
    running = True

    # Domyślny stan początkowy nagłówka przeciwnika
    ostatni_znany_przeciwnik = "Oczekiwanie na gracza"

    while running:
        # --- 1. ODBIERANIE PAKIETÓW SIECIOWYCH (WYMAGANE CO KLATKĘ) ---
        if game_state == "GAME" and gm is not None:
            try:
                gm.handle_response()
            except Exception:
                pass

        # --- 2. OBSŁUGA ZDARZEŃ PYGAME SYSTEMOWYCH I WEJŚCIOWYCH ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if gm is not None:
                    try:
                        gm.disconnect()
                    except:
                        pass
                running = False

            # --- SEKCJA: MENU GŁÓWNE ---
            if game_state == "MENU":
                action = menu.handle_events(event)

                if action == "settings_updated":
                    pass

                elif action == "host":
                    try:
                        host_ip = socket.gethostbyname(socket.gethostname())
                        logger.info(f"Hosting game on IP: {host_ip}")

                        # KOMUNIKAT KONSOLI DLA HOSTA
                        print("\n==================================================")
                        print(" LOG: Uruchomiono serwer Battleship!")
                        print(f" LOG: Twój lokalny adres IP to: {host_ip}")
                        print(" LOG: Oczekiwanie na połączenie od drugiego gracza...")
                        print("==================================================\n")

                        # Uruchomienie serwera sieciowego w tle (osobny wątek)
                        server_instance = NetworkServer(host_ip)
                        server_thread = Thread(
                            target=server_instance.start, daemon=True
                        )
                        server_thread.start()

                        # Krótka pauza, aby dać serwerowi czas na zajęcie portu
                        time.sleep(0.1)

                        # Połączenie lokalnego managera do własnego serwera
                        gm = GameManager(player_name=menu.player_name)
                        gm.connect()

                        game_state = "GAME"
                        ostatni_znany_przeciwnik = "Oczekiwanie na gracza"
                    except Exception as e:
                        logger.error(f"Failed to host game: {e}")

                elif action == "join_final":
                    try:
                        # Pobieramy IP z menu, domyślnie localhost jeśli pole puste
                        ip_do_polaczenia = (
                            menu.host_ip.strip() if menu.host_ip else "127.0.0.1"
                        )
                        logger.info(f"Joining game at IP: {ip_do_polaczenia}")

                        gm = GameManager(
                            player_name=menu.player_name, server_ip=ip_do_polaczenia
                        )
                        gm.connect()

                        # KOMUNIKAT KONSOLI DLA KLIENTA (Wstępne połączenie)
                        print("\n==================================================")
                        print(" LOG: Sukces połączenia niskopoziomowego!")
                        print(f" LOG: Połączono z IP Hosta: {ip_do_polaczenia}")
                        print(f" LOG: Wysłano profil gracza: {menu.player_name}")
                        print("==================================================\n")

                        game_state = "GAME"
                        ostatni_znany_przeciwnik = "Oczekiwanie na gracza"
                    except Exception as e:
                        print(
                            f"\n[BŁĄD POŁĄCZENIA] Nie udało się połączyć z IP: {ip_do_polaczenia}. Czy host na pewno wystartował?"
                        )
                        logger.error(f"Failed to join game: {e}")

                elif action == "quit":
                    running = False

            # --- SEKCJA: EKRAN ROZGRYWKI SIECIOWEJ ---
            elif game_state == "GAME" and gm is not None:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    try:
                        gm.disconnect()
                    except:
                        pass
                    gm = None
                    game_state = "MENU"
                    ostatni_znany_przeciwnik = "Oczekiwanie na gracza"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = pygame.mouse.get_pos()

                    # --- SYSTEM LOGOWANIA KLIKNIĘĆ ---
                    def loguj_klikniecie(x_pos, y_pos, nazwa_planszy):
                        cell = renderer.get_clicked_cell(pos, x_pos, y_pos)
                        if cell:
                            row, col = cell
                            print(
                                f"[INPUT] Kliknięto {nazwa_planszy}: Rząd {row}, Kolumna {col}"
                            )
                        return cell

                    # Sprawdzanie dla obu plansz (Twoja plansza na 50, Radar na 550)
                    klik_moja = renderer.get_clicked_cell(pos, 50, 80)
                    klik_radar = renderer.get_clicked_cell(pos, 550, 80)

                    if klik_moja:
                        loguj_klikniecie(50, 80, "TWOJA PLANSZA")
                    elif klik_radar:
                        loguj_klikniecie(550, 80, "RADAR")

                    # --- LOGIKA GRY ---
                    # FAZA A: LOBBY
                    if getattr(gm, "game_state", None) == GameState.LOBBY:
                        gm.ready(ReadyType.LOBBY)

                    # FAZA B: SHIP_PLACEMENT
                    elif getattr(gm, "game_state", None) == GameState.SHIP_PLACEMENT:
                        if klik_moja:
                            row, col = klik_moja
                            try:
                                sukces = gm.place_ship(
                                    ShipType.ThreeMaster,
                                    row=row,
                                    column=col,
                                    horizontal=True,
                                )
                                if sukces:
                                    logger.info(
                                        f"Statek pomyślnie postawiony na ({row}, {col})"
                                    )
                            except Exception as e:
                                logger.warning(f"Błąd rozstawiania statku: {e}")
                            gm.ready(ReadyType.SHIP_PLACED)

                    # FAZA C: WAR
                    elif getattr(gm, "game_state", None) == GameState.WAR:
                        if getattr(gm, "is_my_turn", False) and klik_radar:
                            row, col = klik_radar
                            gm.shoot(row, col)
                            logger.info(f"Wysłano strzał na pole: {row}, {col}")

        # --- 3. OBSŁUGA ASYNCHRONICZNYCH EVENTÓW INTERFEJSU (KOLEJKA GUI) ---
        if game_state == "GAME" and gm is not None:
            while not gm.gui_events_queue.empty():
                gui_event = gm.gui_events_queue.get()
                event_name = getattr(gui_event, "name", str(gui_event))

                if "ShotHit" in event_name:
                    menu.play_combat_sound("hit")
                elif "ShotMissed" in event_name:
                    menu.play_combat_sound("miss")
                elif "GameWon" in event_name:
                    logger.info("Gra zakończona – Wygrana!")
                elif "GameLost" in event_name:
                    logger.info("Gra zakończona – Przegrana!")

            # --- BEZPIECZNE SKANOWANIE NICKU PRZECIWNIKA ---
            zanalizowany_nick = None

            # 1. Próba przez obiekt opponent
            opp = getattr(gm, "opponent", None)
            if opp and hasattr(opp, "name") and opp.name:
                zanalizowany_nick = opp.name

            # 2. Próba przez zmienne bezpośrednie w gm
            if not zanalizowany_nick:
                for attr in ["enemy_name", "opp_name", "opponent_player_name"]:
                    if hasattr(gm, attr):
                        potencjalny_nick = getattr(gm, attr)
                        if potencjalny_nick:
                            zanalizowany_nick = potencjalny_nick
                            break

            # 3. Próba przez klienta sieciowego
            if not zanalizowany_nick:
                net_client = getattr(gm, "network_client", getattr(gm, "client", None))
                if net_client:
                    for attr in ["opponent_name", "enemy_name", "player_name"]:
                        if hasattr(net_client, attr):
                            potencjalny_nick = getattr(net_client, attr)
                            if potencjalny_nick:
                                zanalizowany_nick = potencjalny_nick
                                break

            # --- FILTRACJA DUPLIKATÓW I CHYBIONYCH NAZW ---
            ZAKAZANE_DOMYSLNE = [
                "",
                "PRZECIWNIK",
                "ENEMY",
                "GRACZ 2",
                "PLAYER 2",
                "NONE",
                "UNKNOWN",
                "GRACZ POŁĄCZONY",
                "OCZEKIWANIE NA PRZECIWNIKA",
            ]

            twoj_nick = str(menu.player_name).upper().strip()

            if zanalizowany_nick:
                czysty_odczyt = str(zanalizowany_nick).upper().strip()
                if czysty_odczyt in ZAKAZANE_DOMYSLNE or czysty_odczyt == twoj_nick:
                    zanalizowany_nick = None

            # --- USTALENIE OSTATECZNEGO TEKSTU ---
            if zanalizowany_nick is not None:
                ostatni_znany_przeciwnik = zanalizowany_nick
            else:
                ostatni_znany_przeciwnik = "Oczekiwanie na gracza"

            # KONSOLA: Logowanie sparsowania graczy
            if zanalizowany_nick and zanalizowany_nick != "Oczekiwanie na gracza":
                if (
                    not hasattr(main, "_zalogowany_nick")
                    or main._zalogowany_nick != zanalizowany_nick
                ):
                    print("\n==================================================")
                    print(" LOG: SPAROWANO Z GRACZEM!")
                    print(
                        f" LOG: Nazwa gracza, do którego się połączono: {zanalizowany_nick}"
                    )
                    print("==================================================\n")
                    main._zalogowany_nick = zanalizowany_nick

        # --- 4. RENDEROWANIE GRAFIKI (PYGAME DRAW) ---
        if game_state == "MENU":
            menu.draw()
        elif game_state == "GAME" and gm is not None:
            screen.fill((10, 10, 25))

            # Bezpieczne pobieranie obiektów plansz
            player_obj = getattr(gm, "player", gm)
            my_board = getattr(player_obj, "board", getattr(gm, "player_board", None))
            radar_board = getattr(player_obj, "radar", getattr(gm, "enemy_board", None))

            if my_board and radar_board:
                # Określenie adresu IP do wyświetlenia w nagłówku
                wyswietlane_ip = (
                    menu.host_ip
                    if menu.host_ip and menu.host_ip != "127.0.0.1"
                    else socket.gethostbyname(socket.gethostname())
                )

                # Nagłówki planszy lewej i prawej (wyczyściłem lewy z IP, bo jest teraz na dole)
                left_title = f"{menu.player_name}"
                right_title = f"RADAR: {ostatni_znany_przeciwnik}"

                # Render obu siatek do Pygame
                renderer.draw(my_board, 50, 80, left_title)
                renderer.draw(radar_board, 550, 80, right_title)

                # --- WYSZUKANIE I RENDEROWANIE IP W LEWYM DOLNYM ROGU ---
                tekst_ip = f"Twoje IP: {wyswietlane_ip}"
                powierzchnia_tekstu = font_ip_hud.render(
                    tekst_ip, True, (120, 120, 140)
                )
                # Pozycja: x = 20 pikseli od lewej, y = wysokość ekranu minus wysokość tekstu minus 20 pikseli marginesu
                screen.blit(
                    powierzchnia_tekstu,
                    (20, screen.get_height() - powierzchnia_tekstu.get_height() - 20),
                )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
