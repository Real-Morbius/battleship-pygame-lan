import logging
import socket
import sys
import threading
from queue import Empty

import pygame

from battleship_pygame_lan.gui.board_render import BoardRenderer
from battleship_pygame_lan.gui.main_menu import MainMenu
from battleship_pygame_lan.logic import Player
from battleship_pygame_lan.logic.enums import ShipType, ShotResult
from battleship_pygame_lan.network.client import NetworkClient
from battleship_pygame_lan.network.models import ReadyType
from battleship_pygame_lan.network.payloads import build_ready_payload
from battleship_pygame_lan.network.server import NetworkServer


def get_local_ip() -> str:
    """Pobiera lokalny adres IP hosta w sieci LAN."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main() -> None:
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        filename="battleships.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(console_handler)

    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1000, 600))
    pygame.display.set_caption("Battleship LAN")
    clock = pygame.time.Clock()

    info_font = pygame.font.SysFont("Arial", 22, bold=True)

    menu = MainMenu(screen)
    renderer = BoardRenderer(screen)

    player1 = Player(menu.player_name)
    enemy = Player("Oczekiwanie...")

    server: NetworkServer | None = None
    client: NetworkClient | None = None
    current_host_ip = ""

    # Flagi synchronizacji
    ready_sent = False

    valid_ready_type = list(ReadyType)[0].value

    try:
        player1.place_ship(ShipType.ThreeMaster, 1, 1)
        player1.place_ship(ShipType.FourMaster, 5, 5, False)
    except Exception as e:
        logger.error(f"Initial ship placement failed: {e}")

    game_state = "MENU"
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if game_state == "MENU":
                action = menu.handle_events(event)
                if action == "settings_updated":
                    player1.name = menu.player_name

                elif action == "host":
                    player1.name = menu.player_name
                    current_host_ip = get_local_ip()
                    print(
                        f"\n[HOST] Uruchamianie serwera... Twoje IP: {current_host_ip}"
                    )

                    server = NetworkServer(server_ip="0.0.0.0")
                    server_thread = threading.Thread(target=server.start, daemon=True)
                    server_thread.start()

                    print(
                        f"[KLIENT] {player1.name} łączy się lokalnie pod IP: {current_host_ip}"
                    )
                    client = NetworkClient(
                        player_name=player1.name, server_ip=current_host_ip
                    )
                    client.connect()

                    client.is_my_turn = False
                    game_state = "GAME"

                elif action == "join_final":
                    player1.name = menu.player_name
                    target_ip = getattr(menu, "target_ip", "127.0.0.1")

                    print(
                        f"\n[KLIENT] {player1.name} próbuje połączyć się z hostem: {target_ip}..."
                    )
                    client = NetworkClient(
                        player_name=player1.name, server_ip=target_ip
                    )
                    try:
                        client.connect()
                        client.is_my_turn = False
                        game_state = "GAME"
                    except Exception as e:
                        print(f"[BŁĄD] Połączenie nieudane: {e}")

                elif action == "quit":
                    running = False

            elif game_state == "GAME":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    game_state = "MENU"

                # KONTROLA STRZELANIA MYSZĄ
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if client and client.enemy_name and client.is_my_turn:
                        pos = pygame.mouse.get_pos()
                        cell = renderer.get_clicked_cell(pos, 550, 80)
                        if cell:
                            row, col = cell
                            try:
                                client.send_attack_info(row, col)
                            except Exception as e:
                                logger.error(f"Błąd wysyłania ataku: {e}")

        # === REAKTYWNA OBSŁUGA SIECI LAN ===
        if client and client.connected:
            if client.enemy_name and enemy.name != client.enemy_name:
                enemy.name = client.enemy_name
                if server:
                    print(f"[SERWER] Gracz '{enemy.name}' dołączył pomyślnie do sesji!")

            # WYMUSZENIE KOLEJNOŚCI SYGNAŁU READY
            if client.enemy_name and not ready_sent:
                # Jeśli program jest Hostem (ma instancję server), opóźnia wysłanie gotowości.
                # Klient (Morbius) wyśle pakiet od razu i zostanie zarejestrowany jako (1/2).
                # Host wyśle pakiet po 300 ms i zamknie lobby jako (2/2), co wymusi inicjalizację tury.
                if server:
                    pygame.time.wait(300)

                print(
                    f"[GRA] Rejestracja gotowości ({valid_ready_type}) dla: {client.player_name}"
                )
                ready_payload = build_ready_payload(
                    player1.name, valid_ready_type, True
                )
                client.send_to_socket(client.client, ready_payload)
                ready_sent = True

                # Od razu dajemy Hostowi lokalne prawo do startu
                if server:
                    client.is_my_turn = True

            try:
                while True:
                    payload = client.message_queue.get_nowait()
                    payload_type = payload.get("type")

                    if payload_type == "change_turn":
                        turn_user = payload.get("turn")
                        client.is_my_turn = turn_user == client.player_name
                        print(
                            f"[SIEĆ] Serwer autoryzował turę: {turn_user} (Ja: {client.is_my_turn})"
                        )

                    elif payload_type == "shot_result":
                        attacker = payload.get("attacker")
                        row = payload.get("row")
                        col = payload.get("col")
                        result_str = payload.get("result")

                        shot_result = ShotResult[result_str]

                        if attacker == client.player_name:
                            player1.mark_shot(row, col, shot_result)
                            menu.play_combat_sound(shot_result)

                            if shot_result == ShotResult.Miss:
                                client.is_my_turn = False
                            else:
                                client.is_my_turn = True
                        else:
                            player1.receive_shot(row, col)
                            menu.play_combat_sound(shot_result)

                            if shot_result == ShotResult.Miss:
                                client.is_my_turn = True
                            else:
                                client.is_my_turn = False

                    client.message_queue.task_done()
            except Empty:
                pass

        # === LOGIKA RENDEROWANIA ===
        if game_state == "MENU":
            menu.draw()
            ready_sent = False
        elif game_state == "GAME":
            screen.fill((10, 10, 25))

            renderer.draw(player1.board, 50, 80, f"FLEET: {player1.name}")
            renderer.draw(player1.radar, 550, 80, f"RADAR (OPPONENT: {enemy.name})")

            if client and client.connected:
                if not client.enemy_name:
                    turn_text = "OCZEKIWANIE NA GRACZA"
                    turn_color = (255, 255, 0)
                elif client.is_my_turn:
                    turn_text = "TWOJA TURA"
                    turn_color = (50, 255, 50)
                else:
                    turn_text = "TURA PRZECIWNIKA"
                    turn_color = (255, 50, 50)
            else:
                turn_text = "OCZEKIWANIE NA POŁĄCZENIE"
                turn_color = (255, 255, 0)

            turn_surface = info_font.render(turn_text, True, turn_color)
            screen.blit(turn_surface, (20, 560))

            if server and current_host_ip:
                ip_surface = info_font.render(
                    f"HOST IP: {current_host_ip}", True, (150, 150, 255)
                )
                screen.blit(ip_surface, (20, 530))

        pygame.display.flip()
        clock.tick(60)

    if client:
        client.disconnect()
    if server:
        server.stop()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
