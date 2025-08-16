import string
from django.utils.crypto import get_random_string
from .models import ShortURL

ALPHABET = string.ascii_letters + string.digits
SLUG_LENGTH = 6

def generate_slug():
    for _ in range(10):
        slug = get_random_string(length=SLUG_LENGTH, allowed_chars=ALPHABET)
        if not ShortURL.objects.filter(slug=slug).exists():
            return slug
    return get_random_string(length=SLUG_LENGTH + 2, allowed_chars=ALPHABET)
