import strawberry
from strawberry import auto
from . import models


@strawberry.django.type(models.Session)
class Session:
    id: auto
    # template = models.ForeignKey(SessionTemplate, on_delete=models.CASCADE, related_name='sessions')
    title: auto
    system_prompt: auto
    context_summary: auto
    # last_context_update = models.ForeignKey('Tick', on_delete=models.CASCADE, related_name='+')
    is_active: auto
    created_at: auto
    updated_at: auto


@strawberry.django.type(models.Tick)
class Tick:
    id: auto
    session: 'Session'
    user_input: auto
    prompt: auto
    llm_response: auto
    context_snapshot: auto
    token_usage: auto
    created_at: auto
