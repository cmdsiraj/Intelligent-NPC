from datetime import datetime, timedelta


class GameTime:
    def __init__(self, start_time: datetime = None):
        self._time = start_time or datetime.now()

    def tick(self) -> datetime:
        self._time = self._time + timedelta(days=1)
        return self._time

    def set_time(self, time: datetime) -> None:
        self._time = time

    def reset(self) -> None:
        self._time = datetime.now()

    @property
    def time(self) -> datetime:
        return self._time


_game_clock = None


def get_gametime_obj() -> GameTime:
    global _game_clock
    if _game_clock is None:
        _game_clock = GameTime()
    return _game_clock


def reset_clock() -> None:
    global _game_clock
    _game_clock = None
