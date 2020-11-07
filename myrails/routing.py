from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.urls import path
from myapp import consumer


webSocket_urlPattern = [
    path('pull_notifications/', consumer.NotificationsConsumer.as_asgi())
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(URLRouter(webSocket_urlPattern))
})
