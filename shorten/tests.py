from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import ShortURL
from .forms import ShortenForm
from .utils import generate_slug
import re


class ShortURLModelTests(TestCase):
    """Test cases for the ShortURL model"""
    
    def test_create_short_url(self):
        """Test creating a basic short URL"""
        url = ShortURL.objects.create(
            original_url='https://example.com/test',
            slug='test123'
        )
        self.assertEqual(url.original_url, 'https://example.com/test')
        self.assertEqual(url.slug, 'test123')
        self.assertEqual(url.hits, 0)
        self.assertIsNotNone(url.created_at)
    
    def test_string_representation(self):
        """Test the string representation of ShortURL"""
        url = ShortURL.objects.create(
            original_url='https://example.com/test',
            slug='test123'
        )
        self.assertEqual(str(url), 'test123 -> https://example.com/test')
    
    def test_unique_original_url(self):
        """Test that original URLs must be unique"""
        ShortURL.objects.create(
            original_url='https://example.com/test',
            slug='test123'
        )
        with self.assertRaises(IntegrityError):
            ShortURL.objects.create(
                original_url='https://example.com/test',
                slug='test456'
            )
    
    def test_unique_slug(self):
        """Test that slugs must be unique"""
        ShortURL.objects.create(
            original_url='https://example.com/test1',
            slug='test123'
        )
        with self.assertRaises(IntegrityError):
            ShortURL.objects.create(
                original_url='https://example.com/test2',
                slug='test123'
            )
    
    def test_hit_counter(self):
        """Test that hit counter increments correctly"""
        url = ShortURL.objects.create(
            original_url='https://example.com/test',
            slug='test123'
        )
        self.assertEqual(url.hits, 0)
        
        # Simulate a hit
        url.hits += 1
        url.save()
        url.refresh_from_db()
        self.assertEqual(url.hits, 1)


class ShortenFormTests(TestCase):
    """Test cases for the ShortenForm"""
    
    def test_valid_form_without_custom_slug(self):
        """Test form validation without custom slug"""
        form_data = {
            'original_url': 'https://example.com/test'
        }
        form = ShortenForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['original_url'], 'https://example.com/test')
        self.assertEqual(form.cleaned_data['custom_slug'], '')
    
    def test_valid_form_with_custom_slug(self):
        """Test form validation with valid custom slug"""
        form_data = {
            'original_url': 'https://example.com/test',
            'custom_slug': 'mycompany'
        }
        form = ShortenForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['custom_slug'], 'mycompany')
    
    def test_invalid_url(self):
        """Test form validation with invalid URL"""
        form_data = {
            'original_url': 'not-a-valid-url',
            'custom_slug': 'test'
        }
        form = ShortenForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('original_url', form.errors)
    
    def test_custom_slug_with_invalid_characters(self):
        """Test custom slug validation with invalid characters"""
        form_data = {
            'original_url': 'https://example.com/test',
            'custom_slug': 'my-company'  # Hyphen not allowed
        }
        form = ShortenForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('custom_slug', form.errors)
    
    def test_custom_slug_too_short(self):
        """Test custom slug validation with too short slug"""
        form_data = {
            'original_url': 'https://example.com/test',
            'custom_slug': 'ab'  # Less than 3 characters
        }
        form = ShortenForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('custom_slug', form.errors)
    
    def test_custom_slug_too_long(self):
        """Test custom slug validation with too long slug"""
        form_data = {
            'original_url': 'https://example.com/test',
            'custom_slug': 'verylongslugname'  # More than 10 characters
        }
        form = ShortenForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('custom_slug', form.errors)
    
    def test_custom_slug_case_insensitive(self):
        """Test that custom slug is converted to lowercase"""
        form_data = {
            'original_url': 'https://example.com/test',
            'custom_slug': 'MyCompany'
        }
        form = ShortenForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['custom_slug'], 'mycompany')
    
    def test_custom_slug_whitespace_trimming(self):
        """Test that custom slug whitespace is trimmed"""
        form_data = {
            'original_url': 'https://example.com/test',
            'custom_slug': '  mycompany  '
        }
        form = ShortenForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['custom_slug'], 'mycompany')


class ShortenFormDatabaseTests(TestCase):
    """Test cases for form validation with database constraints"""
    
    def test_custom_slug_already_exists(self):
        """Test that custom slug validation fails if slug already exists"""
        # Create a URL with the slug first
        ShortURL.objects.create(
            original_url='https://example.com/existing',
            slug='mycompany'
        )
        
        # Try to create another URL with the same slug
        form_data = {
            'original_url': 'https://example.com/new',
            'custom_slug': 'mycompany'
        }
        form = ShortenForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('custom_slug', form.errors)


class UtilsTests(TestCase):
    """Test cases for utility functions"""
    
    def test_generate_slug_length(self):
        """Test that generated slugs have correct length"""
        slug = generate_slug()
        self.assertEqual(len(slug), 6)
    
    def test_generate_slug_characters(self):
        """Test that generated slugs contain only valid characters"""
        slug = generate_slug()
        self.assertTrue(re.match(r'^[a-zA-Z0-9]+$', slug))
    
    def test_generate_slug_uniqueness(self):
        """Test that generated slugs are unique"""
        slugs = set()
        for _ in range(100):
            slug = generate_slug()
            self.assertNotIn(slug, slugs)
            slugs.add(slug)
    
    def test_generate_slug_fallback(self):
        """Test that generate_slug handles collisions gracefully"""
        # Create many URLs to increase collision probability
        for i in range(50):
            ShortURL.objects.create(
                original_url=f'https://example.com/test{i}',
                slug=generate_slug()
            )
        
        # Generate one more slug - should still work
        slug = generate_slug()
        self.assertIsInstance(slug, str)
        self.assertTrue(len(slug) >= 6)


class ViewTests(TestCase):
    """Test cases for views"""
    
    def setUp(self):
        self.client = Client()
    
    def test_index_view_get(self):
        """Test GET request to index view"""
        response = self.client.get(reverse('shorten:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shorten/index.html')
        self.assertIn('form', response.context)
        self.assertIn('recent', response.context)
    
    def test_index_view_post_valid_url(self):
        """Test POST request with valid URL"""
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('created', response.context)
        
        # Check that URL was created
        url = ShortURL.objects.get(original_url='https://example.com/test')
        self.assertEqual(url.slug, response.context['created'].slug)
    
    def test_index_view_post_with_custom_slug(self):
        """Test POST request with custom slug"""
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test',
            'custom_slug': 'mycompany'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('created', response.context)
        
        # Check that URL was created with custom slug
        url = ShortURL.objects.get(original_url='https://example.com/test')
        self.assertEqual(url.slug, 'mycompany')
    
    def test_index_view_post_duplicate_url(self):
        """Test POST request with duplicate URL"""
        # Create first URL
        ShortURL.objects.create(
            original_url='https://example.com/test',
            slug='test123'
        )
        
        # Try to create same URL again
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('created', response.context)
        
        # Should return existing URL, not create new one
        self.assertEqual(response.context['created'].slug, 'test123')
        self.assertEqual(ShortURL.objects.filter(original_url='https://example.com/test').count(), 1)
    
    def test_index_view_post_invalid_form(self):
        """Test POST request with invalid form data"""
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'not-a-valid-url'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('created', response.context)
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())
    
    def test_redirect_view_valid_slug(self):
        """Test redirect view with valid slug"""
        url = ShortURL.objects.create(
            original_url='https://example.com/test',
            slug='test123'
        )
        
        response = self.client.get(reverse('shorten:redirect', args=['test123']))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://example.com/test')
        
        # Check that hit counter was incremented
        url.refresh_from_db()
        self.assertEqual(url.hits, 1)
    
    def test_redirect_view_invalid_slug(self):
        """Test redirect view with invalid slug"""
        response = self.client.get(reverse('shorten:redirect', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)
    
    def test_redirect_view_hit_counter(self):
        """Test that hit counter increments correctly on redirect"""
        url = ShortURL.objects.create(
            original_url='https://example.com/test',
            slug='test123'
        )
        
        # Make multiple redirects
        for i in range(5):
            response = self.client.get(reverse('shorten:redirect', args=['test123']))
            self.assertEqual(response.status_code, 302)
        
        # Check hit counter
        url.refresh_from_db()
        self.assertEqual(url.hits, 5)


class IntegrationTests(TestCase):
    """Integration test cases"""
    
    def setUp(self):
        self.client = Client()
    
    def test_full_workflow(self):
        """Test complete workflow from URL creation to redirect"""
        # Step 1: Create a short URL
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/workflow-test',
            'custom_slug': 'workflow'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Verify URL was created
        url = ShortURL.objects.get(original_url='https://example.com/workflow-test')
        self.assertEqual(url.slug, 'workflow')
        self.assertEqual(url.hits, 0)
        
        # Step 3: Test redirect
        response = self.client.get(reverse('shorten:redirect', args=['workflow']))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://example.com/workflow-test')
        
        # Step 4: Verify hit counter
        url.refresh_from_db()
        self.assertEqual(url.hits, 1)
    
    def test_recent_urls_display(self):
        """Test that recent URLs are displayed correctly"""
        # Create some URLs
        urls = []
        for i in range(5):
            url = ShortURL.objects.create(
                original_url=f'https://example.com/test{i}',
                slug=f'test{i}'
            )
            urls.append(url)
        
        response = self.client.get(reverse('shorten:index'))
        self.assertEqual(response.status_code, 200)
        
        # Check that recent URLs are in context
        recent_urls = response.context['recent']
        self.assertEqual(len(recent_urls), 5)
        
        # Check that they're ordered by creation date (newest first)
        for i, recent_url in enumerate(recent_urls):
            self.assertEqual(recent_url.slug, f'test{4-i}')


class EdgeCaseTests(TestCase):
    """Test edge cases and error conditions"""
    
    def test_very_long_url(self):
        """Test handling of very long URLs"""
        long_url = 'https://example.com/' + 'a' * 2000
        response = self.client.post(reverse('shorten:index'), {
            'original_url': long_url
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('created', response.context)
    
    def test_special_characters_in_custom_slug(self):
        """Test handling of special characters in custom slug"""
        special_slugs = ['my@company', 'my_company', 'my company', 'my+company']
        
        for slug in special_slugs:
            response = self.client.post(reverse('shorten:index'), {
                'original_url': 'https://example.com/test',
                'custom_slug': slug
            })
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('created', response.context)  # Should fail validation
    
    def test_empty_custom_slug(self):
        """Test handling of empty custom slug"""
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test',
            'custom_slug': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('created', response.context)  # Should use auto-generated slug
    
    def test_whitespace_only_custom_slug(self):
        """Test handling of whitespace-only custom slug"""
        response = self.client.post(reverse('shorten:index'), {
            'original_url': 'https://example.com/test',
            'custom_slug': '   '
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('created', response.context)  # Should use auto-generated slug
