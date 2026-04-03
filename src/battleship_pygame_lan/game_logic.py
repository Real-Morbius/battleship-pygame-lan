import logging
import uuid
from enum import Enum

logger = logging.getLogger(__name__)


class ShipType(Enum):
    FourMaster = 4
    ThreeMaster = 3
    TwoMaster = 2
    OneMaster = 1


class Ship:
    def __init__(self, ship_type: ShipType) -> None:
        self.id = str(uuid.uuid4())
        self.ship_type: ShipType = ship_type
        self.health = self.ship_type.value

    def hit(self) -> None:
        self.health -= 1

    def is_sunk(self) -> bool:
        return self.health <= 0


class FieldState(Enum):
    # numbers can be later changed to colors
    Empty = 1
    Taken = 2
    Missed = 3
    Hit = 4


class Field:
    """
    Class Field represents one specific game field.
    """

    def __init__(self) -> None:
        self.state: FieldState = FieldState.Empty
        self.ship: Ship | None = None


class Board:
    """
    Board class. It handles most of the game logic.
    """

    def __init__(self, x=10, y=10) -> None:
        self.x = x
        self.y = y
        self.board: list[list[Field]] = [
            [Field() for _ in range(self.x)] for _ in range(self.y)
        ]

    def shoot(self, x: int, y: int) -> bool:
        """
        Take a shoot at specific field. Return True if something was hit and False if it
        was a miss.
        """
        if x >= self.x or x < 0 or y >= self.y or y < 0:
            logger.info(
                f"Player tried shooting at ({x}, {y}), but it was out of bounds"
            )
            raise ValueError("X or Y is out of bounds!")

        pos = self.board[x][y]

        if pos.state in [FieldState.Hit, FieldState.Missed]:
            logger.info(
                f"Player tried shooting at ({x}, {y}), but it was already shot, so no "
                "action was taken"
            )
            raise ValueError("This place was already shoot!")

        if pos.state == FieldState.Taken:
            logger.info(f"Ship at position ({x}, {y}) was hit!")
            pos.state = FieldState.Hit

            if pos.ship:
                pos.ship.hit()
                if pos.ship.is_sunk():
                    logger.info(
                        f"Ship {pos.ship.ship_type.name} at ({x}, {y}) was sunk! "
                    )

            return True

        logger.info(f"Player tried shooting at ({x}, {y}), but missed!")
        pos.state = FieldState.Missed
        return False
