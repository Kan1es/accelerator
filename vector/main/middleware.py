from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _user_from_token(token_key):
    """Resolve a DRF auth token to the corresponding Django User."""
    from rest_framework.authtoken.models import Token
    try:
        return Token.objects.select_related('user').get(key=token_key).user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware:
    """
    Django Channels middleware that authenticates WebSocket connections
    using DRF Token passed as a query parameter:
        ws://host/ws/notifications/?token=<token>

    The standard AuthMiddlewareStack relies on Django sessions, which the
    frontend doesn't use (it uses token-based auth). This middleware reads
    the token from the URL query string instead.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get('type') == 'websocket':
            query_string = scope.get('query_string', b'').decode()
            params = parse_qs(query_string)
            token_list = params.get('token', [])
            if token_list:
                scope['user'] = await _user_from_token(token_list[0])
            else:
                scope['user'] = AnonymousUser()
        return await self.inner(scope, receive, send)
