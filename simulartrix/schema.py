import strawberry
import asyncio, os, threading
# from .resolver import *
# from .permissions import *
from asgiref.sync import sync_to_async
from typing import List, Optional, AsyncGenerator
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


@strawberry.input
class ChatRoom:
    room_name: str


@strawberry.type
class ChatRoomMessage:
    room_name: str
    current_user: str
    message: str


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
    async def send_chat_message(
            self,
            info: Info,
            room: ChatRoom,
            message: str,
    ) -> None:
        # WebSocket 그룹에 메시지를 전송
        # 그룹 이름은 채팅방 이름 기반으로 설정됨
        await info.context['request'].consumer.channel_layer.group_send(
            f"chat_{room.room_name}",
            {
                "type": "chat.message",
                "room_id": f"chat_{room.room_name}",
                "message": message,
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
    async def join_chat_rooms(
            self,
            info: Info,
            rooms: List[ChatRoom],
            user: str,
    ) -> AsyncGenerator[ChatRoomMessage, None]:
        """Join and subscribe to message sent to the given rooms."""
        ws = info.context["ws"]
        channel_layer = ws.channel_layer

        room_ids = [f"chat_{room.room_name}" for room in rooms]

        for room in room_ids:
            # Join room group
            await channel_layer.group_add(room, ws.channel_name)

        for room in room_ids:
            await channel_layer.group_send(
                room,
                {
                    "type": "chat.message",
                    "room_id": room,
                    "message": f"process: {os.getpid()} thread: {threading.current_thread().name}"
                               f" -> Hello my name is {user}!",
                },
            )

        async with ws.listen_to_channel("chat.message", groups=room_ids) as cm:
            async for message in cm:
                if message["room_id"] in room_ids:
                    yield ChatRoomMessage(
                        room_name=message["room_id"],
                        message=message["message"],
                        current_user=user,
                    )


extensions = (DjangoOptimizerExtension, ApolloTracingExtension, )

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription, extensions=extensions)
arg_schema = JwtSchema(query=Query, mutation=Mutation, subscription=Subscription)
