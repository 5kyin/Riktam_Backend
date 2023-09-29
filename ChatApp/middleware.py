from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from chatting.models import Group

@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()

@database_sync_to_async
def get_group(group_id):
    try:
        group = Group.objects.get(id=group_id)
        return group
    except Group.DoesNotExist:
        return None


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        try:
            params = (dict((x.split('=') for x in scope['query_string'].decode().split("&"))))
            token_key = params.get('token', None)[8:]
            group_id = params.get('group_id', None)
        except ValueError:
            token_key = None
            group_id = None
        scope['user'] = AnonymousUser() if token_key is None else await get_user(token_key)
        scope['group'] = None if group_id is None else await get_group(group_id)
        return await super().__call__(scope, receive, send)