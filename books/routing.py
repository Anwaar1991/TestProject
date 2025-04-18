from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<user_id>\d+)/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<friend_id>\d+)/$', consumers.ChatConsumer.as_asgi()),  # fixed here
]

'''
urls are

ws://localhost/ws/notifications/ws/user_id/

at this route you will get all the notifications about likes, comments and also chats.

example: ws://127.0.0.1:8000/ws/notifications/1/

'''