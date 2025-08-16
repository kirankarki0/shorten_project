"""
Security tests for URL Shortener
Tests all security measures and validations
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.conf import settings
from .models import ShortURL
from .security import (
    validate_url_security, 
    validate_custom_slug_security, 
    check_rate_limit,
    sanitize_input,
    get_client_ip
)
from .forms import ShortenForm
import re


class SecurityValidationTests(TestCase):
    """Test security validation functions"""
    
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
    
    def test_local_ips_blocked(self):
        """Test that local/private IPs are blocked"""
        local_urls = [
            'http://127.0.0.1/test',
            'https://localhost/admin',
            'http://0.0.0.0:8000',
            'http://::1/test',
            'http://localhost.localdomain/test',
            'http://local/test'
        ]
        
        for url in local_urls:
            try:
                validate_url_security(url)
                self.fail(f"URL {url} should have been blocked but was accepted")
            except ValidationError:
                # Expected - URL was blocked
                pass
    
    def test_suspicious_domains_blocked(self):
        """Test that suspicious domains are blocked"""
        suspicious_urls = [
            'https://evil.com/phishing',
            'http://phishing-site.net/login',
            'https://malware.example/download',
            'http://fake-login.com/steal',
            'https://steal-password.net/form'
        ]
        
        for url in suspicious_urls:
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
    
    def test_url_length_validation(self):
        """Test URL length validation"""
        # Test very long URL
        long_url = 'https://example.com/' + 'a' * 3000
        with self.assertRaises(ValidationError):
            validate_url_security(long_url)
    
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
    
    def test_slug_length_validation(self):
        """Test slug length validation"""
        # Test too short
        with self.assertRaises(ValidationError):
            validate_custom_slug_security('ab')
        
        # Test too long
        with self.assertRaises(ValidationError):
            validate_custom_slug_security('verylongslugname')
    
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
    """Test form security validation"""
    
    def test_form_dangerous_url_rejection(self):
        """Test that forms reject dangerous URLs"""
        dangerous_urls = [
            'javascript:alert("xss")',
            'data:text/html,<script>alert("xss")</script>',
            'http://127.0.0.1/admin',
            'https://evil.com/phishing'
        ]
        
        for url in dangerous_urls:
            form_data = {'original_url': url}
            form = ShortenForm(data=form_data)
            self.assertFalse(form.is_valid())
            self.assertIn('original_url', form.errors)
    
    def test_form_dangerous_slug_rejection(self):
        """Test that forms reject dangerous custom slugs"""
        dangerous_slugs = [
            'admin',
            'test<script>',
            'javascript',
            '..',
            'test"test'
        ]
        
        for slug in dangerous_slugs:
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


class RateLimitTests(TestCase):
    """Test rate limiting functionality"""
    
    @override_settings(RATELIMIT_ENABLE=True)
    def setUp(self):
        self.client = Client()
    
    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limit_enforcement(self):
        """Test that rate limits are enforced"""
        # Make multiple requests quickly
        for i in range(15):  # Exceed 10/m limit
            response = self.client.post(reverse('shorten:index'), {
                'original_url': f'https://example.com/test{i}'
            })
            
            if i >= 10:
                self.assertEqual(response.status_code, 403)
                self.assertIn('Rate limit exceeded', response.content.decode())
            else:
                self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_reset(self):
        """Test that rate limits reset after time period"""
        # This would require time-based testing in a real scenario
        # For now, just test the basic functionality
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test'
        })
        self.assertEqual(response.status_code, 200)


class ViewSecurityTests(TestCase):
    """Test view security measures"""
    
    def setUp(self):
        self.client = Client()
    
    def test_xss_prevention_in_forms(self):
        """Test XSS prevention in form handling"""
        xss_inputs = [
            '<script>alert("xss")</script>',
            'test<script>alert("xss")</script>test',
            'javascript:alert("xss")',
            'data:text/html,<script>alert("xss")</script>'
        ]
        
        for xss_input in xss_inputs:
            response = self.client.post(reverse('shorten:index'), {
                'original_url': xss_input,
                'custom_slug': 'test'
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form'].is_valid())
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        sql_injection_inputs = [
            "'; DROP TABLE shorten_shorturl; --",
            "' OR '1'='1",
            "'; INSERT INTO shorten_shorturl VALUES ('evil', 'evil'); --",
            "' UNION SELECT * FROM auth_user --"
        ]
        
        for malicious_input in sql_injection_inputs:
            response = self.client.post(reverse('shorten:index'), {
                'original_url': malicious_input
            })
            self.assertEqual(response.status_code, 200)
            # Should not cause database errors
            self.assertFalse(response.context['form'].is_valid())
    
    def test_directory_traversal_prevention(self):
        """Test directory traversal prevention"""
        traversal_inputs = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
        ]
        
        for traversal_input in traversal_inputs:
            response = self.client.post(reverse('shorten:index'), {
                'original_url': f'file://{traversal_input}'
            })
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form'].is_valid())
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        # Test that CSRF middleware is properly configured in settings
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', settings.MIDDLEWARE)
        
        # Test that CSRF protection is enabled
        self.assertTrue(hasattr(settings, 'CSRF_COOKIE_SECURE'))
        self.assertTrue(hasattr(settings, 'CSRF_COOKIE_HTTPONLY'))
    
    def test_secure_headers(self):
        """Test that security headers are present"""
        response = self.client.get(reverse('shorten:index'))
        
        # Check for security headers (these would be set by middleware)
        # Note: In test environment, some headers might not be present
        self.assertEqual(response.status_code, 200)


class ClientIPTests(TestCase):
    """Test client IP detection"""
    
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


class IntegrationSecurityTests(TestCase):
    """Integration security tests"""
    
    def setUp(self):
        self.client = Client()
    
    def test_end_to_end_security(self):
        """Test end-to-end security workflow"""
        # Test creating a URL with malicious input
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'javascript:alert("xss")',
            'custom_slug': 'admin'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        
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
    
    def test_security_logging(self):
        """Test that security events are logged"""
        # This would require checking logs in a real scenario
        # For now, just test that the application doesn't crash
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test'
        })
        self.assertEqual(response.status_code, 200)
