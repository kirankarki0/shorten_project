from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.db.models import F
from django.core.exceptions import ValidationError
from .models import ShortURL
from .forms import ShortenForm
from .utils import generate_slug
from .security import check_rate_limit, log_security_event, get_client_ip
import logging

logger = logging.getLogger(__name__)

def index(request):
    # Check rate limiting
    if request.method == 'POST':
        if not check_rate_limit(request, 'ip', '10/m'):
            log_security_event('rate_limit_exceeded', {
                'ip': get_client_ip(request),
                'method': 'POST',
                'endpoint': 'index'
            }, request)
            return HttpResponseForbidden('Rate limit exceeded. Please try again later.')
        
        if not check_rate_limit(request, 'ip', '100/h'):
            log_security_event('rate_limit_exceeded', {
                'ip': get_client_ip(request),
                'method': 'POST',
                'endpoint': 'index',
                'period': 'hourly'
            }, request)
            return HttpResponseForbidden('Hourly rate limit exceeded. Please try again later.')
    
    form = ShortenForm(request.POST or None)
    created = None
    
    if request.method == 'POST' and form.is_valid():
        try:
            original = form.cleaned_data['original_url']
            custom_slug = form.cleaned_data.get('custom_slug', '')
            
            # Check if URL already exists
            existing_url = ShortURL.objects.filter(original_url=original).first()
            
            if existing_url:
                # URL already exists, return existing object
                created = existing_url
                logger.info(f'Existing URL accessed: {original} -> {existing_url.slug}')
            else:
                # Create new URL with custom slug or auto-generated slug
                if custom_slug:
                    # Use custom slug
                    created = ShortURL.objects.create(
                        original_url=original,
                        slug=custom_slug
                    )
                    logger.info(f'Custom slug created: {original} -> {custom_slug}')
                else:
                    # Use auto-generated slug
                    created = ShortURL.objects.create(
                        original_url=original,
                        slug=generate_slug()
                    )
                    logger.info(f'Auto-generated slug created: {original} -> {created.slug}')
            
            # Log successful creation
            log_security_event('url_created', {
                'original_url': original,
                'slug': created.slug,
                'is_custom': bool(custom_slug)
            }, request)
            
        except Exception as e:
            logger.error(f'Error creating URL: {str(e)}')
            log_security_event('url_creation_error', {
                'error': str(e),
                'original_url': request.POST.get('original_url', ''),
                'custom_slug': request.POST.get('custom_slug', '')
            }, request)
            # Re-raise the exception to show form errors
            raise
    
    return render(request, 'shorten/index.html', {
        'form': form,
        'created': created,
        'recent': ShortURL.objects.order_by('-created_at')[:10],
        'domain': request.get_host(),
    })

def redirect_slug(request, slug):
    # Check rate limiting for redirects
    if not check_rate_limit(request, 'ip', '100/m'):
        log_security_event('redirect_rate_limit_exceeded', {
            'ip': get_client_ip(request),
            'slug': slug
        }, request)
        return HttpResponseForbidden('Rate limit exceeded. Please try again later.')
    
    try:
        obj = get_object_or_404(ShortURL, slug=slug)
        
        # Increment hit counter atomically
        ShortURL.objects.filter(pk=obj.pk).update(hits=F('hits') + 1)
        
        # Log redirect
        log_security_event('url_redirected', {
            'slug': slug,
            'original_url': obj.original_url,
            'hits': obj.hits + 1
        }, request)
        
        return HttpResponseRedirect(obj.original_url)
        
    except Exception as e:
        logger.error(f'Error redirecting slug {slug}: {str(e)}')
        log_security_event('redirect_error', {
            'slug': slug,
            'error': str(e)
        }, request)
        raise
