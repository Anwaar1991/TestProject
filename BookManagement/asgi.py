import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import books.routing 
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BookManagement.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            books.routing.websocket_urlpatterns
        )
    ),
})

