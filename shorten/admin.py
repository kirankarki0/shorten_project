from django.contrib import admin
from .models import ShortURL

@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ('slug', 'original_url', 'created_at', 'hits')
    search_fields = ('original_url', 'slug')
