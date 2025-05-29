from enum import Flag, auto


class AggregationPolicy(Flag):
    WAIT_FOR_CHILDREN = auto()
    WAIT_FOR_SUBTREE = auto()
    WAIT_FOR_ANY_PAGE = auto()
