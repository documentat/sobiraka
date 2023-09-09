from dataclasses import dataclass, field


@dataclass
class Counter:
    """
    A counter that produces formatted period-separated numbers like 5.2, 5.3, and so on.

    When created, a counter contains the value 0.
    To add 1 to a counter section, call increase() with the corresponding level, e.g.:
        - increase(1) will turn 0 into 1,
        - increase(2) will turn 0 into 0.1.
    """
    components: list[int] = field(default_factory=lambda: [0])

    def __str__(self):
        return '.'.join(map(str, self.components))

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self}>'

    def increase(self, level: int):
        """
        Increase given level by one.
        If the counter had any values after the given level, they will be removed (e.g., 4.2.1→4.3).
        If the given level exceeds the current number of levels by more than one, an exception will be thrown.
        """
        n = level - 1
        if n < len(self.components):
            self.components[n] += 1
            self.components = self.components[:n+1]
        elif n == len(self.components):
            self.components.append(1)
        else:
            raise ValueError(f'Can\'t increase level {level} in {self.components}.')
