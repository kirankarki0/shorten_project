"""
Security utilities for URL Shortener
Handles URL validation, rate limiting, and security checks
"""

import re
import ipaddress
from urllib.parse import urlparse
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
import logging

logger = logging.getLogger(__name__)


def validate_url_security(url: str) -> str:
    """
    Validate URL for security concerns
    
    Args:
        url: The URL to validate
        
    Returns:
        The validated URL
        
    Raises:
        ValidationError: If URL is considered unsafe
    """
    if not url:
        raise ValidationError('URL cannot be empty')
    
    # Normalize URL
    url = url.strip()
    
    # Check for dangerous protocols
    dangerous_protocols = [
        'javascript:', 'data:', 'vbscript:', 'file:', 'ftp:', 
        'mailto:', 'tel:', 'sms:', 'whatsapp:'
    ]
    
    url_lower = url.lower()
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            logger.warning(f'Dangerous protocol detected: {url}')
            raise ValidationError(f'Dangerous protocol "{protocol}" is not allowed')
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        logger.warning(f'Invalid URL format: {url}, error: {e}')
        raise ValidationError('Invalid URL format')
    
    # Check for local/private IPs
    # Handle both hostname and netloc for IPv6 addresses
    hostname_to_check = parsed.hostname
    if not hostname_to_check and parsed.netloc:
        # For IPv6 addresses, hostname might be None, so check netloc
        # Remove port if present (e.g., [::1]:8080 -> ::1)
        netloc = parsed.netloc
        if netloc.startswith('[') and ']' in netloc:
            # IPv6 with port: [::1]:8080
            hostname_to_check = netloc[1:netloc.find(']')]
        else:
            # IPv6 without port or regular hostname
            if ':' in netloc and netloc.count(':') > 1:
                # This is likely an IPv6 address (multiple colons)
                hostname_to_check = netloc
            else:
                # Regular hostname with port
                hostname_to_check = netloc.split(':')[0]
    
    if hostname_to_check:
        try:
            # Check if it's an IP address
            ip = ipaddress.ip_address(hostname_to_check)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                logger.warning(f'Private/local IP detected: {hostname_to_check}')
                raise ValidationError('Private/local IP addresses are not allowed')
        except ValueError:
            # Not an IP address, check hostname
            pass
        
        # Check for localhost variations
        localhost_patterns = [
            'localhost', '127.0.0.1', '0.0.0.0', '::1',
            'localhost.localdomain', 'local'
        ]
        
        if hostname_to_check.lower() in localhost_patterns:
            logger.warning(f'Localhost detected: {hostname_to_check}')
            raise ValidationError('Localhost URLs are not allowed')
    
    # Check for suspicious domains (example list)
    suspicious_domains = getattr(settings, 'SUSPICIOUS_DOMAINS', [
        'evil.com', 'phishing-site.net', 'malware.example',
        'fake-login.com', 'steal-password.net'
    ])
    
    if parsed.hostname and parsed.hostname.lower() in suspicious_domains:
        logger.warning(f'Suspicious domain detected: {parsed.hostname}')
        raise ValidationError('Suspicious domain detected')
    
    # Check URL length
    max_length = getattr(settings, 'MAX_URL_LENGTH', 2048)
    if len(url) > max_length:
        raise ValidationError(f'URL too long (max {max_length} characters)')
    
    return url


def check_rate_limit(request: HttpRequest, key: str = 'ip', rate: str = '10/m') -> bool:
    """
    Check if request is within rate limits
    
    Args:
        request: The HTTP request
        key: Rate limit key ('ip', 'user', etc.)
        rate: Rate limit (e.g., '10/m', '100/h')
        
    Returns:
        True if within limits, False if exceeded
    """
    # For testing purposes, disable rate limiting if not configured
    if not getattr(settings, 'RATELIMIT_ENABLE', False):
        return True
    
    # Parse rate limit
    count, period = parse_rate_limit(rate)
    
    # Generate cache key
    if key == 'ip':
        cache_key = f'rate_limit:{key}:{get_client_ip(request)}:{period}'
    else:
        cache_key = f'rate_limit:{key}:{request.user.id if request.user.is_authenticated else "anonymous"}:{period}'
    
    # Check current count
    current_count = cache.get(cache_key, 0)
    
    if current_count >= count:
        logger.warning(f'Rate limit exceeded for {cache_key}')
        return False
    
    # Increment counter
    cache.set(cache_key, current_count + 1, get_period_seconds(period))
    return True


def get_client_ip(request: HttpRequest) -> str:
    """
    Get client IP address from request
    
    Args:
        request: The HTTP request
        
    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_rate_limit(rate: str) -> tuple[int, str]:
    """
    Parse rate limit string (e.g., '10/m' -> (10, 'm'))
    
    Args:
        rate: Rate limit string
        
    Returns:
        Tuple of (count, period)
    """
    match = re.match(r'(\d+)/([smhd])', rate)
    if not match:
        raise ValueError(f'Invalid rate limit format: {rate}')
    
    count = int(match.group(1))
    period = match.group(2)
    return count, period


def get_period_seconds(period: str) -> int:
    """
    Convert period to seconds
    
    Args:
        period: Period character ('s', 'm', 'h', 'd')
        
    Returns:
        Period in seconds
    """
    periods = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    return periods.get(period, 60)


def validate_custom_slug_security(slug: str) -> str:
    """
    Validate custom slug for security
    
    Args:
        slug: The slug to validate
        
    Returns:
        The validated slug
        
    Raises:
        ValidationError: If slug is invalid
    """
    if not slug:
        return slug
    
    slug = slug.strip()
    
    # Check length
    min_length = getattr(settings, 'MIN_CUSTOM_SLUG_LENGTH', 3)
    max_length = getattr(settings, 'MAX_CUSTOM_SLUG_LENGTH', 10)
    
    if len(slug) < min_length:
        raise ValidationError(f'Slug too short (minimum {min_length} characters)')
    
    if len(slug) > max_length:
        raise ValidationError(f'Slug too long (maximum {max_length} characters)')
    
    # Check for valid characters only
    if not re.match(r'^[a-zA-Z0-9]+$', slug):
        raise ValidationError('Slug can only contain letters and numbers')
    
    # Check for reserved words
    reserved_words = getattr(settings, 'RESERVED_SLUGS', [
        'admin', 'api', 'login', 'logout', 'register', 'password',
        'reset', 'confirm', 'activate', 'deactivate', 'delete',
        'edit', 'new', 'create', 'update', 'remove', 'add'
    ])
    
    if slug.lower() in reserved_words:
        raise ValidationError('This slug is reserved and cannot be used')
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'\.\.',  # Directory traversal
        r'[<>"\']',  # HTML/script injection
        r'javascript',  # JavaScript injection
        r'data:',  # Data URLs
        r'vbscript',  # VBScript
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, slug, re.IGNORECASE):
            logger.warning(f'Suspicious slug pattern detected: {slug}')
            raise ValidationError('Suspicious characters detected in slug')
    
    return slug.lower()


def log_security_event(event_type: str, details: dict, request: HttpRequest = None):
    """
    Log security events
    
    Args:
        event_type: Type of security event
        details: Event details
        request: HTTP request (optional)
    """
    log_data = {
        'event_type': event_type,
        'details': details,
        'timestamp': str(datetime.now()),
    }
    
    if request:
        log_data.update({
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        })
    
    logger.warning(f'Security event: {log_data}')


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text.strip()


# Import datetime at the top level
from datetime import datetime
