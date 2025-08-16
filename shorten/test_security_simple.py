"""
Simplified Security Tests for URL Shortener
Core security validation tests without rate limiting conflicts
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from .security import (
    validate_url_security, 
    validate_custom_slug_security, 
    sanitize_input,
    get_client_ip
)
from .forms import ShortenForm


class CoreSecurityValidationTests(TestCase):
    """Core security validation tests"""
    
    def test_dangerous_protocols_blocked(self):
        """Test that dangerous protocols are blocked"""
        dangerous_urls = [
            'javascript:alert("xss")',
            'data:text/html,<script>alert("xss")</script>',
            'vbscript:msgbox("xss")',
            'file:///etc/passwd',
            'ftp://evil.com',
            'mailto:evil@evil.com',
            'tel:+1234567890',
            'sms:+1234567890',
            'whatsapp://send?text=evil'
        ]
        
        for url in dangerous_urls:
            with self.assertRaises(ValidationError):
                validate_url_security(url)
    
    def test_valid_urls_accepted(self):
        """Test that valid URLs are accepted"""
        valid_urls = [
            'https://google.com',
            'http://example.com/test',
            'https://github.com/user/repo',
            'http://stackoverflow.com/questions/123',
            'https://www.wikipedia.org/wiki/Django'
        ]
        
        for url in valid_urls:
            try:
                validated = validate_url_security(url)
                self.assertEqual(validated, url)
            except ValidationError:
                self.fail(f"Valid URL {url} was incorrectly rejected")
    
    def test_custom_slug_security(self):
        """Test custom slug security validation"""
        # Test reserved words
        reserved_slugs = ['admin', 'api', 'login', 'logout', 'register']
        for slug in reserved_slugs:
            with self.assertRaises(ValidationError):
                validate_custom_slug_security(slug)
        
        # Test suspicious patterns
        suspicious_slugs = [
            '..',  # Directory traversal
            'test<script>',  # XSS attempt
            'javascript',  # JavaScript injection
            'data:test',  # Data URL
            'vbscript',  # VBScript
            'test"test',  # Quote injection
            'test<test>',  # HTML injection
        ]
        
        for slug in suspicious_slugs:
            with self.assertRaises(ValidationError):
                validate_custom_slug_security(slug)
        
        # Test valid slugs
        valid_slugs = ['mycompany', 'test123', 'blog', 'product']
        for slug in valid_slugs:
            try:
                validated = validate_custom_slug_security(slug)
                self.assertEqual(validated, slug.lower())
            except ValidationError:
                self.fail(f"Valid slug {slug} was incorrectly rejected")
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        dangerous_inputs = [
            '<script>alert("xss")</script>',
            'test<script>alert("xss")</script>test',
            'test"test',
            'test<test>',
            'test&test',
            'test\'test'
        ]
        
        for dangerous in dangerous_inputs:
            sanitized = sanitize_input(dangerous)
            self.assertNotIn('<script>', sanitized)
            self.assertNotIn('"', sanitized)
            self.assertNotIn('<', sanitized)
            self.assertNotIn('>', sanitized)
            self.assertNotIn('&', sanitized)
            self.assertNotIn("'", sanitized)


class FormSecurityTests(TestCase):
    """Form security tests"""
    
    def test_form_dangerous_url_rejection(self):
        """Test that forms reject dangerous URLs"""
        dangerous_urls = [
            'javascript:alert("xss")',
            'data:text/html,<script>alert("xss")</script>',
        ]
        
        for url in dangerous_urls:
            form_data = {'original_url': url}
            form = ShortenForm(data=form_data)
            self.assertFalse(form.is_valid())
            self.assertIn('original_url', form.errors)
    
    def test_form_dangerous_slug_rejection(self):
        """Test that forms reject dangerous custom slugs"""
        # Test reserved words (these should be caught by validation)
        reserved_slugs = ['admin', 'api', 'login']
        
        for slug in reserved_slugs:
            form_data = {
                'original_url': 'https://example.com/test',
                'custom_slug': slug
            }
            form = ShortenForm(data=form_data)
            self.assertFalse(form.is_valid())
            self.assertIn('custom_slug', form.errors)
        
        # Test suspicious patterns that should be caught
        suspicious_slugs = [
            '..',  # Directory traversal
            'test<script>',  # XSS attempt
            'javascript',  # JavaScript injection
        ]
        
        for slug in suspicious_slugs:
            form_data = {
                'original_url': 'https://example.com/test',
                'custom_slug': slug
            }
            form = ShortenForm(data=form_data)
            self.assertFalse(form.is_valid())
            self.assertIn('custom_slug', form.errors)
    
    def test_form_valid_input_acceptance(self):
        """Test that forms accept valid input"""
        form_data = {
            'original_url': 'https://example.com/test',
            'custom_slug': 'mycompany'
        }
        form = ShortenForm(data=form_data)
        self.assertTrue(form.is_valid())


class ClientIPTests(TestCase):
    """Client IP detection tests"""
    
    def test_client_ip_detection(self):
        """Test client IP detection from request"""
        client = Client()
        
        # Test with X-Forwarded-For header
        response = client.get(reverse('shorten:index'), 
                            HTTP_X_FORWARDED_FOR='192.168.1.1, 10.0.0.1')
        request = response.wsgi_request
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
        
        # Test without X-Forwarded-For
        response = client.get(reverse('shorten:index'))
        request = response.wsgi_request
        ip = get_client_ip(request)
        self.assertIsNotNone(ip)


class BasicViewSecurityTests(TestCase):
    """Basic view security tests"""
    
    def setUp(self):
        self.client = Client()
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        # Create a client that doesn't automatically handle CSRF
        client = Client(enforce_csrf_checks=True)
        
        # Test without CSRF token - should fail
        response = client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test'
        })
        
        # Should get a 403 Forbidden due to CSRF failure
        self.assertEqual(response.status_code, 403)
    
    def test_valid_url_creation(self):
        """Test valid URL creation"""
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test',
            'custom_slug': 'mycompany'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].is_valid())
        
        if response.context.get('created'):
            self.assertEqual(response.context['created'].slug, 'mycompany')
    
    def test_invalid_url_rejection(self):
        """Test invalid URL rejection"""
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'javascript:alert("xss")',
            'custom_slug': 'test'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())


class SecurityIntegrationTests(TestCase):
    """Integration security tests"""
    
    def setUp(self):
        self.client = Client()
    
    def test_end_to_end_security_workflow(self):
        """Test complete security workflow"""
        # Test creating a valid URL
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test',
            'custom_slug': 'mycompany'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].is_valid())
        
        # Test accessing the created URL
        if response.context.get('created'):
            slug = response.context['created'].slug
            redirect_response = self.client.get(reverse('shorten:redirect', args=[slug]))
            self.assertEqual(redirect_response.status_code, 302)
    
    def test_security_logging_functionality(self):
        """Test that security logging works"""
        # This test just ensures the application doesn't crash
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test'
        })
        self.assertEqual(response.status_code, 200)
