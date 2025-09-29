import strawberry
from strawberry import auto
from typing import Union
from . import models


@strawberry.django.filters.filter(models.Thread, lookups=True)
class ThreadFilter:
    id: auto


@strawberry.django.ordering.order(models.Thread)
class ThreadOrder:
    id: auto


@strawberry.django.type(models.Thread, filters=ThreadFilter, order=ThreadOrder)
class Thread:
    id: auto
    # template = models.ForeignKey(SessionTemplate, on_delete=models.CASCADE, related_name='sessions')
    title: auto
    system_prompt: auto
    context_summary: auto
    # last_context_update = models.ForeignKey('Tick', on_delete=models.CASCADE, related_name='+')
    is_active: auto
    created_at: auto
    updated_at: auto


@strawberry.django.filters.filter(models.Tick, lookups=True)
class TickFilter:
    id: auto
    thread: Union['ThreadFilter', None]


@strawberry.django.ordering.order(models.Tick)
class TickOrder:
    id: auto


@strawberry.django.type(models.Tick, filters=TickFilter, order=TickOrder)
class Tick:
    id: auto
    thread: 'Thread'
    user_input: auto
    prompt: auto
    llm_response: auto
    context_snapshot: auto
    token_usage: auto
    created_at: auto
