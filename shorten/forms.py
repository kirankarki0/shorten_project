from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import ShortURL
from .security import validate_url_security, validate_custom_slug_security, sanitize_input
import re

class ShortenForm(forms.Form):
    original_url = forms.URLField(
        label='URL', 
        max_length=2048,
        widget=forms.URLInput(attrs={
            'placeholder': 'https://example.com/very/long/url',
            'class': 'form-control',
            'autocomplete': 'off',
        })
    )
    
    custom_slug = forms.CharField(
        label='Custom Slug (optional)', 
        required=False,
        max_length=10,
        min_length=3,
        widget=forms.TextInput(attrs={
            'placeholder': 'mycompany',
            'class': 'form-control',
            'autocomplete': 'off',
        }),
        help_text='Leave empty for auto-generated slug (3-10 characters, letters and numbers only)'
    )
    
    def clean_original_url(self):
        """Clean and validate the original URL"""
        url = self.cleaned_data.get('original_url', '').strip()
        
        if not url:
            raise ValidationError('URL cannot be empty')
        
        # Sanitize input
        url = sanitize_input(url)
        
        # Validate URL security
        try:
            url = validate_url_security(url)
        except ValidationError as e:
            raise ValidationError(str(e))
        
        return url
    
    def clean_custom_slug(self):
        """Clean and validate the custom slug"""
        custom_slug = self.cleaned_data.get('custom_slug', '').strip()
        
        if not custom_slug:
            return custom_slug
        
        # Validate slug security first (before sanitization)
        try:
            custom_slug = validate_custom_slug_security(custom_slug)
        except ValidationError as e:
            raise ValidationError(str(e))
        
        # Sanitize input after validation
        custom_slug = sanitize_input(custom_slug)
        
        # Check if slug is already taken
        if ShortURL.objects.filter(slug=custom_slug).exists():
            raise ValidationError('This custom slug is already taken. Please choose another one.')
        
        return custom_slug
