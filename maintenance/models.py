from django.db import models
from django.conf import settings
from properties.models import Unit

class MaintenanceTicket(models.Model):
    URGENCY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH',     'High'),
        ('MEDIUM',   'Medium'),
        ('LOW',      'Low'),
    ]
    STATUS_CHOICES = [
        ('OPEN',        'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED',    'Resolved'),
        ('CLOSED',      'Closed'),
    ]

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='maintenance_tickets')
    title = models.CharField(max_length=200)
    description = models.TextField()
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='LOW')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reported_tickets')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Logged at resolution")
    cost_document = models.FileField(upload_to='documents/maintenance/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['urgency']),
            models.Index(fields=['unit']),
        ]

    def __str__(self):
        return f"Ticket #{self.id} - {self.title} ({self.status})"

class TicketTimeline(models.Model):
    ticket = models.ForeignKey(MaintenanceTicket, on_delete=models.CASCADE, related_name='timeline')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=MaintenanceTicket.STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    cost_logged = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.ticket.id} -> {self.status} at {self.timestamp}"

class MaintenanceFeedback(models.Model):
    ticket = models.OneToOneField(MaintenanceTicket, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(help_text="1 to 5 stars")
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Ticket #{self.ticket_id}: {self.rating} stars"
