from django.db import models


class AestheticAnalysis(models.Model):
    image = models.ImageField(upload_to='analyses/')
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Analysis {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ConversationAnalysis(models.Model):
    conversation_text = models.TextField()
    analysis_result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Conversation Analysis {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class IPUsage(models.Model):
    ip_address = models.CharField(max_length=64, unique=True)
    count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_updated']

    def __str__(self):
        return f"IPUsage {self.ip_address} = {self.count}"