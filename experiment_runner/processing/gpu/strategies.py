"""
Contains Strategies for GPU Selection
"""

import random
from enum import Enum
from typing import Callable, Dict, List

from experiment_runner.processing.gpu.models import GPU
from experiment_runner.utils import nan_safe_float

SelectionStrategy = Callable[[List[GPU]], List[GPU]]


class SelectionStrategyEnum(Enum):
    """
    Enum containing all available GPU selection strategies
    """

    NONE = "none"  # NO GPU is used
    FIRST = "first"  # select the GPU with the lowest ID
    LAST = "last"  # select the GPU with the highest ID
    RANDOM = "random"  # select a random available GPU
    LOAD = "load"  # select the GPU with the lowest load
    MEMORY = "memory"  # select the GPU with the most memory available
    LOAD_MEMORY_RANDOM = "load_memory_random"


class SelectionStrategyFactory:
    """
    Factory for SelectionStrategies
    """

    class_dictionary: Dict[SelectionStrategyEnum, SelectionStrategy] = {}

    @classmethod
    def register(cls, strategy_type: SelectionStrategyEnum) -> Callable[[SelectionStrategy], SelectionStrategy]:
        """
        Decorator registration for Strategies
        """

        def inner_method(strategy: SelectionStrategy) -> SelectionStrategy:
            cls.class_dictionary[strategy_type] = strategy
            return strategy

        return inner_method

    @classmethod
    def get_instance(cls, strategy_type: SelectionStrategyEnum) -> SelectionStrategy:
        """
        Gets strategy from SelectionStrategyEnum
        """
        try:
            strategy = cls.class_dictionary[strategy_type]
        except KeyError as exc:
            known_strategies = [key.value for key, _ in cls.class_dictionary.items()]
            raise ValueError(f"Unbekannte Strategie. Folgende Strategien existieren: {known_strategies}") from exc

        return strategy


@SelectionStrategyFactory.register(SelectionStrategyEnum.FIRST)
def select_first(gpus: List[GPU]) -> List[GPU]:
    """
    Select the first available GPU
    """
    glist = list(gpus)
    glist.sort(key=lambda x: x.id, reverse=False)
    return glist


@SelectionStrategyFactory.register(SelectionStrategyEnum.LAST)
def select_last(gpus: List[GPU]) -> List[GPU]:
    """
    Select the last available GPU
    """
    glist = list(gpus)
    glist.sort(key=lambda x: x.id, reverse=True)
    return glist


@SelectionStrategyFactory.register(SelectionStrategyEnum.RANDOM)
def select_random(gpus: List[GPU]) -> List[GPU]:
    """
    Select a random available GPU
    """

    glist = [gpus[g] for g in random.sample(range(0, len(gpus)), len(gpus))]
    return glist


@SelectionStrategyFactory.register(SelectionStrategyEnum.LOAD)
def select_load(gpus: List[GPU]) -> List[GPU]:
    """
    Select the GPU with the least load
    """

    glist = list(gpus)
    glist.sort(key=lambda x: nan_safe_float(x.load), reverse=False)
    return glist


@SelectionStrategyFactory.register(SelectionStrategyEnum.MEMORY)
def select_memory(gpus: List[GPU]) -> List[GPU]:
    """
    Select the GPU with the most memory available
    """

    glist = list(gpus)
    glist.sort(key=lambda x: nan_safe_float(x.memory_util), reverse=False)
    return glist


@SelectionStrategyFactory.register(SelectionStrategyEnum.LOAD_MEMORY_RANDOM)
def select_load_memory_random(gpus: List[GPU]) -> List[GPU]:
    """
    Select the GPU with least load, most memory and then at random
    """

    glist = list(gpus)
    glist.sort(
        key=lambda x: (nan_safe_float(x.load), nan_safe_float(x.memory_util), random.randint(0, len(gpus))),
        reverse=False,
    )
    return glist


@SelectionStrategyFactory.register(SelectionStrategyEnum.NONE)
def select_none(gpus: List[GPU]) -> List[GPU]:
    """
    Select no GPU
    """
    gpus.sort()  # Pylint does not like it
    return []
