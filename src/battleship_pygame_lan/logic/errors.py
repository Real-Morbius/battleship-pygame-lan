class BattleshipError(Exception):
    """
    Base class for custom exceptions
    """

    def __init__(self, msg: str) -> None:
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self) -> str:
        return self.msg


class OutOfBoundsError(BattleshipError):
    def __init__(
        self, row: int, column: int, msg: str = "Row or column is out of bounds"
    ) -> None:
        self.msg = msg
        self.row = row
        self.column = column
        super().__init__(self.msg)

    def __str__(self) -> str:
        return f"({self.row}, {self.column}) - {self.msg}"


class NearbyTakenError(BattleshipError):
    def __init__(
        self, row: int, column: int, msg: str = "Field nearby is taken"
    ) -> None:
        self.msg = msg
        self.row = row
        self.column = column
        super().__init__(self.msg)

    def __str__(self) -> str:
        return f"({self.row}, {self.column}) - {self.msg}"


class AlreadyShotError(BattleshipError):
    def __init__(self, msg: str = "This position is already marked as shot") -> None:
        self.msg = msg
        super().__init__(msg)

    def __str__(self) -> str:
        return self.msg
