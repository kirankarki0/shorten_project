from django.db import models
from django.utils import timezone
class ShortURL(models.Model):
    original_url = models.URLField(max_length=2048, unique=True)
    slug = models.CharField(max_length=10, unique=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    hits = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"{self.slug} -> {self.original_url}"
