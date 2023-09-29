import json
from django.shortcuts import get_object_or_404
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from .models import Group, Message
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_id = None
        self.group_name = None

    async def connect(self):
        user = self.scope["user"]
        group = self.scope["group"]
        if user.is_authenticated and group :
            self.group = group
            self.group_id = group.id
            self.group_name = f"group_{self.group_id}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            await self.send_existing_messages()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    # Manageing the
        # text_data_json = json.loads(text_data)
        # message = text_data_json['content']
        # group_id = text_data_json['group_id']
        # sender_id = text_data_json['sender']
 
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        command = text_data_json['command']

        message = text_data_json['content']
        sender = self.scope["user"]
        group = self.scope["group"]
        
        if command == 'send_group_messages':
            message_object = await sync_to_async(self.save_message)(message,sender,group)
            await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chat_message',
                        'message_object': message_object,
                        'command':'new_message'
                    }
                )
            # messages = await sync_to_async(self.get_messages_from_group)(group_id)
            # await sync_to_async(self.send_messages)(messages)
        elif command == 'send_group_likes':
            message_object = await sync_to_async(self.get_existing_message)(message,sender)
            await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chat_message',
                        'message_object': message_object,
                        'command':'like_message'
                    }
                )

    async def chat_message(self, event):
        message_object = event['message_object']
        command = event['command']
        message = await self.serialize_message(message_object)
        # # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'command': command,
            'message': message,
        }))

    def send_messages(self, messages):
        for message in messages:
            self.send(text_data=json.dumps({
                'command': 'existing_message',
                'content': message.content,
                'sender': message.sender.username,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }))
    
    async def serialize_message(self,message_object):
        liked_users_data = await sync_to_async(self.get_liked_users)(message_object)
        return {
            "group": self.scope["group"].id,
            "content": message_object.content,
            "timestamp": message_object.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "sender": {
                "id": message_object.sender.id,
                    "username": message_object.sender.username,
                    "first_name": message_object.sender.first_name,
                    "last_name": message_object.sender.last_name
            },
            "id": message_object.id,
            "likes": liked_users_data
        }

    def get_messages_from_group(self, group_id):
        # Use synchronous database operations here to get messages
        messages = Message.objects.filter(group_id=group_id).order_by('timestamp')
        return messages.all()
    
    def save_message(self, message_content, sender,group):
        return Message.objects.create(
            group=group,
            sender=sender,
            content=message_content,
        )
        
    def get_liked_users(self, message):
        liked_users = message.likes.all()
        return [{'id': user.id, 'username': user.username} for user in liked_users]

    async def send_like_messages_to_channel(self,message):
        pass

    async def send_existing_messages(self):
        existing_messages_coroutine = await database_sync_to_async(self.get_existing_messages)(self.group)
        existing_messages = await existing_messages_coroutine
        await self.send_existing_messages_to_channel(existing_messages)
    
    @database_sync_to_async
    def get_existing_messages(self,groupID):
        messages = Message.objects.filter(group=groupID).order_by('timestamp').select_related('sender', 'group').prefetch_related('likes')
        return list(messages)
    
    def get_existing_message(self,message_id,sender):
        try:
            message_object = Message.objects.get(id=message_id) 
            if message_object:
                if sender in message_object.likes.all():
                    message_object.likes.remove(sender)
                else:message_object.likes.add(sender)
                print("message_object.sender")
                print(message_object.sender)

            return message_object
        except Message.DoesNotExist:
            return None
    
    async def send_existing_messages_to_channel(self, existing_messages):
        for message in existing_messages:
            event={
                'type': 'chat_message',
                'message_object': message,
                'command':'existing_message'
            }
            await self.chat_message(event)
        
    