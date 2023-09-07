from typing import Generator


class Utils:
    @staticmethod
    def next_int(seed: int = 1) -> Generator[int, None, None]:
        while True:
            yield seed
            seed += 1
