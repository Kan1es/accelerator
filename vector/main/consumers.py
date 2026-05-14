import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer для уведомлений пользователей.
    Каждый пользователь подключается к своей личной группе user_{user_id}.
    """

    async def connect(self):
        self.user = self.scope.get('user', AnonymousUser())

        if self.user.is_anonymous:
            await self.close()
            return

        self.user_group_name = f'user_{self.user.id}'

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def send_notification(self, event):
        """
        Отправляет JSON-сообщение клиенту.
        event - словарь, содержащий данные для отправки.
        Обычно event['data'] - основное сообщение.
        """
        message = event.get('data', {})

        await self.send(text_data=json.dumps(message))


    @classmethod
    async def send_to_user(cls, user_id, data):
        """
        Статический метод для отправки уведомления конкретному пользователю.
        Вызывается из любого места (например, из задачи Celery).
        """
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'user_{user_id}',
            {
                'type': 'send_notification',
                'data': data
            }
        )