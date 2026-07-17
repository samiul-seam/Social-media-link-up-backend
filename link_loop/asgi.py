import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'link_loop.settings')

# Django setup must happen before any other imports
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from messaging.middleware import JWTAuthMiddleware
import api.routing

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': JWTAuthMiddleware(
        URLRouter(
            api.routing.websocket_urlpatterns
        )
    ), 
})
app = application
