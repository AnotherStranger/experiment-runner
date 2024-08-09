import random
from typing import List

from experiment_runner.processing.gpu.models import GPU
from experiment_runner.processing.gpu.strategies import (
    SelectionStrategyEnum,
    SelectionStrategyFactory,
)


def get_gpus(count, load: List = [], memory_usage: List = []):
    if len(load) == 0:
        load = [random.random() for i in range(count)]
    if len(memory_usage) == 0:
        memory_usage = [random.randint(0, 4096) for i in range(count)]
    return [
        GPU(
            id=x,
            uuid=str(random.randint(1, 100)),
            load=load[x],
            memory_total=4096,
            memory_used=memory_usage[x],
            memory_free=4096 - memory_usage[x],
            driver="nvidia",
            name="Quadro RTX 8000",
            serial=str(random.randint(1, 1000)),
            display_mode="no",
            display_active="no",
            temperature=1000,
        )
        for x in range(count)
    ]


def test_strategy_SelectFirst():
    # Check factory creating SelectFirst strategy
    strategy = SelectionStrategyFactory.get_instance(SelectionStrategyEnum.FIRST)

    gpus = get_gpus(5)

    # Check behaviour of SelectFirst strategy - Should always extract the first GPUs
    sorted_gpus = strategy(gpus)
    for g in range(len(gpus)):
        assert sorted_gpus[g].id == g


def test_strategy_SelectLast():
    # Check factory creating SelectLast strategy
    strategy = SelectionStrategyFactory.get_instance(SelectionStrategyEnum.LAST)

    gpus = get_gpus(5)

    # Check behaviour of SelectFirst strategy - Should always extract the last GPUs
    sorted_gpus = strategy(gpus)
    for g in range(len(gpus)):
        assert sorted_gpus[g].id == len(gpus) - g - 1


def test_strategy_SelectLoad():
    # Check factory creating SelectLoad strategy
    strategy = SelectionStrategyFactory.get_instance(SelectionStrategyEnum.LOAD)

    load_order = [random.random() for x in range(5)]
    load_order.sort()
    load_shuffled = random.sample(load_order, len(load_order))

    gpus = get_gpus(5, load_shuffled)

    sorted_gpus = strategy(gpus)
    for g in range(len(gpus)):
        assert sorted_gpus[g].load == load_order[g]


def test_strategy_SelectMemory():
    # Check factory creating SelectMemory strategy
    strategy = SelectionStrategyFactory.get_instance(SelectionStrategyEnum.MEMORY)

    memory_order = [random.randint(0, 4096) for x in range(5)]

    gpus = get_gpus(5, [], memory_order)

    memory_order.sort()
    sorted_gpus = strategy(gpus)
    for g in range(len(gpus)):
        assert sorted_gpus[g].memory_used == memory_order[g]
