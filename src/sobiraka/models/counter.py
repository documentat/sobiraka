from dataclasses import dataclass, field


@dataclass
class Counter:
    components: list[int] = field(default_factory=lambda: [0])

    def __str__(self):
        return '.'.join(map(str, self.components))

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self}>'

    def increase(self, level: int):
        n = level - 1
        if n < len(self.components):
            self.components[n] += 1
            self.components = self.components[:n+1]
        elif n == len(self.components):
            self.components.append(1)
        else:
            raise ValueError(f'Can\'t increase level {level} in {self.components}.')
