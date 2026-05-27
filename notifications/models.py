from django.conf import settings
from django.db import models

from common.constants import NotificationType

import uuid

try:
    import uuid6
    default_uuid_generator = uuid6.uuid7
except ImportError:
    default_uuid_generator= uuid.uuid4
    
class Notification(models.Model):
    id=models.UUIDField(primary_key=True, default=default_uuid_generator, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices, db_index=True)
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=['user', 'is_read', 'created_at'])]

    def __str__(self):
        return f'Notification<{self.user.email}:{self.notification_type}>'
