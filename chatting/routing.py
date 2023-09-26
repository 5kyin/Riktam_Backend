from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from chatting import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:group_id>/', consumers.ChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': URLRouter(websocket_urlpatterns),
})