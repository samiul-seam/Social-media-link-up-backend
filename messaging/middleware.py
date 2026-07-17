import logging
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        token = AccessToken(token_key)
        user_id = token['user_id']
        return User.objects.get(id=user_id)
    except Exception as e:
        logger.warning(f"WS token auth failed: {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        try:
            query_string = scope.get('query_string', b'').decode()
            # parse_qs safely handles tokens with '=' padding and multiple params
            params = parse_qs(query_string)
            token = params.get('token', [None])[0]
            scope['user'] = await get_user_from_token(token) if token else AnonymousUser()
        except Exception as e:
            logger.error(f"JWTAuthMiddleware error: {e}")
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)