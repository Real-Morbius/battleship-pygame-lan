import pytest

from src.battleship_pygame_lan.game_logic import Board, FieldState, Ship, ShipType


def test_ship_initialization():
    ship = Ship(ShipType.ThreeMaster)
    assert ship.health == 3
    assert not ship.is_sunk()


def test_ship_hit_sink():
    ship = Ship(ShipType.OneMaster)
    ship.hit()

    assert ship.health == 0
    assert ship.is_sunk() is True


def test_board_initialization():
    board = Board(10, 10)

    with pytest.raises(ValueError, match="out of bounds"):
        board.shot(10, 10)

    with pytest.raises(ValueError, match="out of bounds"):
        board.shot(-1, 5)


def test_shot_miss():
    board = Board()
    result = board.shot(0, 0)

    assert result is False
    assert board.board[0][0].state == FieldState.Missed


def test_shot_taken():
    board = Board()
    board.shot(0, 0)

    with pytest.raises(ValueError, match="This place was already shot!"):
        board.shot(0, 0)


def test_placing_ship_success():
    board = Board()
    board.place_ship(ShipType.OneMaster, 0, 0)
    assert board.board[0][0].state == FieldState.Taken
    assert board.board[0][0].ship.health == 1

    board.place_ship(ShipType.TwoMaster, 3, 3)
    assert board.board[3][3].state == FieldState.Taken
    assert board.board[4][3].state == FieldState.Taken
    assert board.board[3][3].ship.health == 2
    assert (
        board.board[3][3].ship is board.board[4][3].ship
    )  # check if this is the same ship
    assert board.board[3][3].ship.id == board.board[4][3].ship.id  # check if id matches


@pytest.mark.parametrize(
    "x, y",
    [
        (123, 0),
        (-123, 0),
        (0, 123),
        (0, -123),
        (123, -123),
    ],
)
def test_placing_ship_out_of_bounds(x, y):
    board = Board()
    with pytest.raises(ValueError, match="X or Y is out of bounds!"):
        board.place_ship(ShipType.OneMaster, x, y)


def test_placing_ship_collision():
    board = Board()
    board.place_ship(ShipType.OneMaster, 1, 1)

    with pytest.raises(ValueError, match="Field nearby is taken"):
        board.place_ship(ShipType.OneMaster, 1, 1)

    with pytest.raises(ValueError, match="Field nearby is taken"):
        board.place_ship(ShipType.OneMaster, 2, 1)

    with pytest.raises(ValueError, match="Field nearby is taken"):
        board.place_ship(ShipType.OneMaster, 1, 2)


def test_game():
    board = Board()

    board.place_ship(ShipType.TwoMaster, 1, 1, True)
    placed_ship = board.board[1][1].ship

    result_1 = board.shot(1, 1)
    assert result_1 is True
    assert board.board[1][1].state == FieldState.Hit
    assert placed_ship.health == 1
    assert not placed_ship.is_sunk()

    result_2 = board.shot(2, 1)
    assert result_2 is True
    assert board.board[2][1].state == FieldState.Hit
    assert placed_ship.health == 0
    assert placed_ship.is_sunk() is True
