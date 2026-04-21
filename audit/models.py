from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    """
    Immutable activity log for the system.
    Tracks who did what and when, referencing the specific entity.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, help_text="Null for system actions")
    action = models.CharField(max_length=100, help_text="E.g., INVOICE_GENERATED, PAYMENT_RECORDED")
    
    entity_type = models.CharField(max_length=50, help_text="E.g., Contract, Payment, Ticket")
    entity_id = models.PositiveIntegerField(help_text="ID of the related entity")
    
    description = models.TextField()
    seen = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['actor']),
            models.Index(fields=['action']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['seen']),
        ]

    def __str__(self):
        actor_name = self.actor.display_name if self.actor else "System"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {actor_name} -> {self.action} on {self.entity_type} {self.entity_id}"
