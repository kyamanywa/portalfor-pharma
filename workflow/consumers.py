"""
WebSocket Consumers for real-time notifications
Handles live updates when users perform actions across the system
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    
    Handles:
    - User connections/disconnections
    - Real-time phase status updates
    - BMR approval notifications
    - Material release updates
    - QC/quarantine notifications
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        # Reject anonymous users
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Create unique group names for the user
        self.user_group_name = f"user_{self.user.id}"
        self.role_group_name = f"role_{self.user.role}"
        self.department_group_name = f"dept_{self.user.department.lower().replace(' ', '_')}" if self.user.department else None
        
        # Join user-specific group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        # Join role-based group (for role-specific notifications)
        await self.channel_layer.group_add(
            self.role_group_name,
            self.channel_name
        )
        
        # Join department group if applicable
        if self.department_group_name:
            await self.channel_layer.group_add(
                self.department_group_name,
                self.channel_name
            )
        
        # Join global notifications group
        await self.channel_layer.group_add(
            "global_notifications",
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to real-time notifications',
            'user_id': self.user.id,
            'username': self.user.username
        }))
        
        logger.info(f"User {self.user.username} connected to WebSocket")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave all groups
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.role_group_name,
            self.channel_name
        )
        if self.department_group_name:
            await self.channel_layer.group_discard(
                self.department_group_name,
                self.channel_name
            )
        await self.channel_layer.group_discard(
            "global_notifications",
            self.channel_name
        )
        
        logger.info(f"User {self.user.username} disconnected from WebSocket")
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                # Mark notification as read
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
            
            elif message_type == 'ping':
                # Respond to ping to keep connection alive
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
    
    async def send_notification(self, event):
        """Send notification to WebSocket client"""
        await self.send(text_data=json.dumps({
            'type': event['type'],
            'notification': event.get('notification'),
            'data': event.get('data'),
            'timestamp': event.get('timestamp')
        }))
    
    async def phase_update(self, event):
        """Handle phase status update notification"""
        await self.send(text_data=json.dumps({
            'type': 'phase_update',
            'phase_id': event['phase_id'],
            'bmr_number': event['bmr_number'],
            'phase_name': event['phase_name'],
            'status': event['status'],
            'updated_by': event['updated_by'],
            'timestamp': event['timestamp']
        }))
    
    async def bmr_status_update(self, event):
        """Handle BMR status update notification"""
        await self.send(text_data=json.dumps({
            'type': 'bmr_status_update',
            'bmr_number': event['bmr_number'],
            'batch_number': event['batch_number'],
            'status': event['status'],
            'updated_by': event['updated_by'],
            'timestamp': event['timestamp']
        }))
    
    async def material_release_update(self, event):
        """Handle material release notification"""
        await self.send(text_data=json.dumps({
            'type': 'material_release_update',
            'release_number': event['release_number'],
            'status': event['status'],
            'updated_by': event['updated_by'],
            'timestamp': event['timestamp']
        }))
    
    async def qc_update(self, event):
        """Handle QC/quarantine update notification"""
        await self.send(text_data=json.dumps({
            'type': 'qc_update',
            'batch_number': event['batch_number'],
            'quarantine_status': event['quarantine_status'],
            'action': event['action'],
            'updated_by': event['updated_by'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read in database"""
        from dashboards.models import UserNotification
        
        try:
            notification = UserNotification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.is_read = True
            notification.save()
        except UserNotification.DoesNotExist:
            pass


# Utility functions for sending notifications
async def send_phase_update_to_user(user_id, phase_id, bmr_number, phase_name, status, updated_by):
    """Send phase update to specific user"""
    from channels.layers import get_channel_layer
    from django.utils import timezone
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"user_{user_id}",
        {
            'type': 'phase_update',
            'phase_id': phase_id,
            'bmr_number': bmr_number,
            'phase_name': phase_name,
            'status': status,
            'updated_by': updated_by,
            'timestamp': timezone.now().isoformat()
        }
    )


async def send_phase_update_to_role(role, phase_id, bmr_number, phase_name, status, updated_by):
    """Send phase update to all users with specific role"""
    from channels.layers import get_channel_layer
    from django.utils import timezone
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"role_{role}",
        {
            'type': 'phase_update',
            'phase_id': phase_id,
            'bmr_number': bmr_number,
            'phase_name': phase_name,
            'status': status,
            'updated_by': updated_by,
            'timestamp': timezone.now().isoformat()
        }
    )


async def send_bmr_update_to_user(user_id, bmr_number, batch_number, status, updated_by):
    """Send BMR status update to specific user"""
    from channels.layers import get_channel_layer
    from django.utils import timezone
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"user_{user_id}",
        {
            'type': 'bmr_status_update',
            'bmr_number': bmr_number,
            'batch_number': batch_number,
            'status': status,
            'updated_by': updated_by,
            'timestamp': timezone.now().isoformat()
        }
    )


async def send_qc_update_to_user(user_id, batch_number, quarantine_status, action, updated_by):
    """Send QC update to specific user"""
    from channels.layers import get_channel_layer
    from django.utils import timezone
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"user_{user_id}",
        {
            'type': 'qc_update',
            'batch_number': batch_number,
            'quarantine_status': quarantine_status,
            'action': action,
            'updated_by': updated_by,
            'timestamp': timezone.now().isoformat()
        }
    )