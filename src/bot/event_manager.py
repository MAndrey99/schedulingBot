from enum import Enum, auto
from typing import Callable
from collections import defaultdict


class EventType(Enum):
    SCHEDULE_CHANGED = auto()
    SCHEDULE_CHANGING_CHECK = auto()


class Event:
    @property
    def type(self):
        return self.__type

    @property
    def kwargs(self):
        return self.__kwargs

    def __init__(self, event_type: EventType, **kwargs):
        self.__type = event_type
        self.__kwargs = kwargs


class EventManager:
    def __init__(self):
        self._callbacks: dict[EventType, set[Callable]] = defaultdict(set)

    def emit(self, event: Event):
        for f in self._callbacks[event.type]:
            f(**event.kwargs)

    def register_slot(self, event_type: EventType, callback: Callable = None):
        def decorator(handler: Callable):
            self._callbacks[event_type].add(handler)
            return handler
        if callback is None:
            return decorator
        self._callbacks[event_type].add(callback)


event_manager = EventManager()
