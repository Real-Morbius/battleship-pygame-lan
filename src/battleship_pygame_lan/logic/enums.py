from enum import Enum


class ShipType(Enum):
    """
    Defines the available ship types and their length. Ship length is also it's health
    """

    FourMaster = 4
    ThreeMaster = 3
    TwoMaster = 2
    OneMaster = 1


class FieldState(Enum):
    """
    Represents the current state of a single field on the board.
    """

    # numbers can be later changed to colors
    Empty = 1
    Taken = 2
    Missed = 3
    Hit = 4
