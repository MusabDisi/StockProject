from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from asgiref.sync import async_to_sync


class NotificationsConsumer(AsyncJsonWebsocketConsumer):
    # Function to connect to the web socket
    async def connect(self):
        print('trying to connect')
        # Checking if the User is logged in
        if self.scope["user"].is_anonymous:
            await self.close()  # Reject the connection
        else:
            group_name = str(self.scope["user"].pk)  # user pk as group name
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )
            await self.accept()

    # Function to disconnect the Socket
    async def disconnect(self, close_code):
        await self.close()

    # Custom Notify Function which can be called from Views or api to send message to the frontend
    async def notify(self, event):
        print('notify called')
        print(event['data'])
        await self.send_json(event['data'])  # converted to json by the function itself
