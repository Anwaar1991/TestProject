import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'notifications_{self.user_id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass  # Not needed for now

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["content"]))




# Chat Feature comsumer start here!

from asgiref.sync import sync_to_async



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.friend_id = self.scope['url_route']['kwargs']['friend_id']
        print("---------CHECK IF WE HAVE THE LOGGED IN USER ID------", self.user.id)
        self.room_group_name = self.get_chat_group_name(self.user.id, self.friend_id)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


# RECEIVE FUNCTION TO RECIEVE MESSAGES:
    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content")
        sender_id = int(data.get("sender_id"))  # manually passed sender_id with message
        receiver_id = int(self.friend_id)

        # Check if the sender ID matches the connected user but here I will not use it as my self.user.id would not work without authentication

        # if self.user.id != sender_id:
        #     await self.send(text_data=json.dumps({"error": "Sender ID does not match authenticated user."}))
        #     return


        # Check if both users are friends
        are_friends = await self.are_users_friends(sender_id, receiver_id)
        if not are_friends:
            await self.send(text_data=json.dumps({"error": "Not friends."}))
            return

        # Save message
        message = await self.save_message(sender_id, receiver_id, content)

        # Broadcast message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': content,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'timestamp': str(message.timestamp),
                'message_id': message.id
            }
        )



    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    @sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        from .models import Message
        from django.contrib.auth import get_user_model
        CustomUser = get_user_model()
        sender = CustomUser.objects.get(id=sender_id)
        receiver = CustomUser.objects.get(id=receiver_id)
        return Message.objects.create(sender=sender, receiver=receiver, content=content)

    @sync_to_async
    def are_users_friends(self, user1_id, user2_id):
        from accounts.models import CustomUser
        try:
            user1 = CustomUser.objects.get(id=user1_id)
            return user1.friends.filter(id=user2_id).exists()
        except CustomUser.DoesNotExist:
            return False

    def get_chat_group_name(self, user1_id, user2_id):
        sorted_ids = sorted([str(user1_id), str(user2_id)])
        return f"chat_{sorted_ids[0]}_{sorted_ids[1]}"


'''
CHAT API DETAILS:

ws/chat/<reciever id>/

here you will have to put the id of the friend who you are sending message.
the id of sender will be automatically get by the code as request.user.id. in production
but for now you have to pass sender_id with message also:
{
    "content" : "your message",
    "sender_id" : "7"
}

'''