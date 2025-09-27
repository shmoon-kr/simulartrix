import strawberry
import requests
import openai
import tiktoken
import asyncio, os, threading
from .types import *
# from .resolver import *
# from .permissions import *
from asgiref.sync import sync_to_async
from typing import List, Optional, AsyncGenerator
from django.conf import settings
from openai import OpenAI
from graphql import GraphQLError
from django.contrib.auth import authenticate
from strawberry_django import mutations as strawberry_mutations
from strawberry_django.permissions import IsAuthenticated
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry.extensions.tracing import ApolloTracingExtension
from strawberry.types import Info
from gqlauth.core.middlewares import JwtSchema
from gqlauth.user.queries import UserQueries
from gqlauth.user import arg_mutations as mutations


@strawberry.type
class Query(UserQueries):
    pass


@strawberry.type
class Mutation:
    verify_token = mutations.VerifyToken.field
    #update_account = mutations.UpdateAccount.field
    archive_account = mutations.ArchiveAccount.field
    delete_account = mutations.DeleteAccount.field
    password_change = mutations.PasswordChange.field
    #swap_emails = mutations.SwapEmails.field
    #captcha = Captcha.field
    token_auth = mutations.ObtainJSONWebToken.field
    register = mutations.Register.field
    verify_account = mutations.VerifyAccount.field
    resend_activation_email = mutations.ResendActivationEmail.field
    send_password_reset_email = mutations.SendPasswordResetEmail.field
    password_reset = mutations.PasswordReset.field
    password_set = mutations.PasswordSet.field
    refresh_token = mutations.RefreshToken.field
    revoke_token = mutations.RevokeToken.field
    #verify_secondary_email = mutations.VerifySecondaryEmail.field

    @strawberry.mutation
    async def send_prompt(
            self,
            info: Info,
            session_id: strawberry.ID,
            prompt: str,
    ) -> None:

        session = await models.Session.objects.select_related("template").prefetch_related("ticks").aget(id=session_id)

        client = OpenAI()

        llm_model = "gpt-4o-mini"

        chat_history = [
            {
                "role": "system",
                "content": [
                    {"type": "input_text", "text": session.template.system_prompt},
                ],
            },
        ]

        last_ticks = session.ticks.filter(id__gte=getattr(session.last_context_update, "id", 0))

        async for tick in last_ticks:
            chat_history.extend(
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": tick.user_input},
                        ],
                    },
                    {
                        "role": "assistant",
                        "content": [
                            {"type": "output_text", "text": tick.llm_response},
                        ],
                    },
                ]
            )

        chat_history.append(
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                ],
            }
        )

        response = client.responses.create(
            model=llm_model,
            input=chat_history,
        )

        # print(response.refusal)

        # 토크나이저 불러오기
        encoding = tiktoken.encoding_for_model(llm_model)

        tick = await models.Tick.objects.acreate(
            session=session,
            user_input=prompt,
            llm_response=response.output_text,
            token_usage=len(encoding.encode(prompt)) + len(encoding.encode(response.output_text)) + 4
        )

        # WebSocket 그룹에 메시지를 전송
        # 그룹 이름은 채팅방 이름 기반으로 설정됨
        await info.context['request'].consumer.channel_layer.group_send(
            f"session_{session_id}",
            {
                "type": "session.message",
                "session_id": f"session_{session_id}",
                "message": tick.llm_response,
            },
        )


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)

    @strawberry.subscription
    async def on_session_message(
            self,
            info: Info,
            session_id: strawberry.ID,
    ) -> AsyncGenerator[SessionMessage, None]:
        """Join and subscribe to message sent to the given rooms."""
        ws = info.context["ws"]
        channel_layer = ws.channel_layer

        # room_id = f"chat_{room.room_name}"
        session = await models.Session.objects.aget(id=session_id)
        session_id = f"session_{session_id}"

        # Join room group
        await channel_layer.group_add(session_id, ws.channel_name)

        await channel_layer.group_send(
            session_id,
            {
                "type": "session.message",
                "session_id": session_id,
                "message": f"process: {os.getpid()} thread: {threading.current_thread().name}"
                           f" -> Hello welcome to session {session_id}!",
            },
        )

        async with ws.listen_to_channel("session.message", groups=[session_id]) as cm:
            async for message in cm:
                yield SessionMessage(
                    session=session,
                    message=message["message"],
                )


extensions = (DjangoOptimizerExtension, ApolloTracingExtension, )

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription, extensions=extensions)
arg_schema = JwtSchema(query=Query, mutation=Mutation, subscription=Subscription)
