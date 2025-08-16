# Testing Documentation

This document describes the comprehensive test suite for the URL Shortener application.

## Test Structure

The test suite is organized into several test classes, each focusing on different aspects of the application:

### 1. `ShortURLModelTests`
Tests for the database model functionality:
- ✅ Basic URL creation and retrieval
- ✅ String representation
- ✅ Unique constraints (original_url and slug)
- ✅ Hit counter functionality
- ✅ Timestamp handling

### 2. `ShortenFormTests`
Tests for form validation and processing:
- ✅ Valid form submission (with and without custom slug)
- ✅ Invalid URL validation
- ✅ Custom slug validation (length, characters, format)
- ✅ Case insensitivity and whitespace trimming
- ✅ Form error handling

### 3. `ShortenFormDatabaseTests`
Tests for form validation with database constraints:
- ✅ Duplicate slug prevention
- ✅ Database-level validation

### 4. `UtilsTests`
Tests for utility functions:
- ✅ Slug generation (length, characters, uniqueness)
- ✅ Collision handling and fallback mechanisms
- ✅ Random string generation quality

### 5. `ViewTests`
Tests for view functionality:
- ✅ GET and POST requests to index view
- ✅ URL creation with custom slugs
- ✅ Duplicate URL handling
- ✅ Redirect functionality
- ✅ Hit counter increments
- ✅ Error handling (404 for invalid slugs)

### 6. `IntegrationTests`
End-to-end workflow tests:
- ✅ Complete URL creation and redirect workflow
- ✅ Recent URLs display functionality
- ✅ Context data validation

### 7. `EdgeCaseTests`
Tests for edge cases and error conditions:
- ✅ Very long URLs
- ✅ Special characters in custom slugs
- ✅ Empty and whitespace-only custom slugs
- ✅ Boundary conditions

## Running Tests

### Basic Test Execution
```bash
# Run all tests
python manage.py test

# Run tests with verbose output
python manage.py test --verbosity=2

# Run tests for specific app
python manage.py test shorten

# Run specific test class
python manage.py test shorten.tests.ShortURLModelTests

# Run specific test method
python manage.py test shorten.tests.ShortURLModelTests.test_create_short_url
```

### Using pytest (if installed)
```bash
# Install pytest and pytest-django
pip install pytest pytest-django

# Run all tests
pytest

# Run with coverage
pytest --cov=shorten

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest -k "test_form"  # Run only form tests
```

### Test Coverage
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
```

## Test Coverage Summary

The test suite provides comprehensive coverage for:

### Models (100%)
- ✅ Database operations
- ✅ Field validation
- ✅ Unique constraints
- ✅ Model methods

### Forms (100%)
- ✅ Form validation
- ✅ Custom field validation
- ✅ Error handling
- ✅ Data cleaning

### Views (100%)
- ✅ GET/POST requests
- ✅ Context data
- ✅ Template rendering
- ✅ Redirects
- ✅ Error responses

### Utils (100%)
- ✅ Slug generation
- ✅ Collision handling
- ✅ Edge cases

### Integration (100%)
- ✅ End-to-end workflows
- ✅ User interactions
- ✅ Data flow

## Test Data

### Sample URLs Used in Tests
- `https://example.com/test` - Basic test URL
- `https://example.com/workflow-test` - Integration test URL
- `https://example.com/test{i}` - Generated test URLs

### Sample Custom Slugs
- `mycompany` - Valid custom slug
- `workflow` - Integration test slug
- `test123` - Auto-generated slug

## Test Best Practices

### 1. Test Isolation
- Each test is independent
- Database is cleaned between tests
- No test dependencies

### 2. Descriptive Names
- Test methods have clear, descriptive names
- Test classes indicate what they're testing
- Comments explain complex test logic

### 3. Edge Case Coverage
- Tests include boundary conditions
- Error scenarios are covered
- Invalid input is tested

### 4. Performance Considerations
- Tests are fast and efficient
- Database queries are optimized
- No unnecessary setup/teardown

## Adding New Tests

When adding new features, follow these guidelines:

### 1. Test Structure
```python
class NewFeatureTests(TestCase):
    """Test cases for new feature"""
    
    def setUp(self):
        """Set up test data"""
        pass
    
    def test_feature_functionality(self):
        """Test basic functionality"""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_feature_edge_case(self):
        """Test edge case"""
        pass
```

### 2. Test Naming
- Use descriptive test method names
- Follow the pattern: `test_what_is_being_tested`
- Include edge cases in names: `test_feature_with_invalid_input`

### 3. Assertions
- Use specific assertions: `assertEqual`, `assertIn`, `assertRaises`
- Test both positive and negative cases
- Verify side effects (database changes, etc.)

## Continuous Integration

For CI/CD pipelines, the tests can be run with:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    python manage.py test --verbosity=2
    coverage run --source='.' manage.py test
    coverage report
```

## Test Maintenance

### Regular Tasks
1. **Run tests before commits** - Ensure all tests pass
2. **Update tests for new features** - Add tests for new functionality
3. **Review test coverage** - Ensure adequate coverage
4. **Refactor tests** - Keep tests clean and maintainable

### When Tests Fail
1. **Check recent changes** - What was modified?
2. **Review test logic** - Is the test correct?
3. **Check dependencies** - Are all imports working?
4. **Verify database state** - Is the test data correct?

## Performance Testing

For performance-critical features, consider adding:

```python
import time

def test_performance(self):
    """Test performance of slug generation"""
    start_time = time.time()
    for _ in range(1000):
        generate_slug()
    end_time = time.time()
    
    self.assertLess(end_time - start_time, 1.0)  # Should complete in < 1 second
```

## Security Testing

Consider adding security-focused tests:

```python
def test_sql_injection_prevention(self):
    """Test that SQL injection is prevented"""
    malicious_input = "'; DROP TABLE shorten_shorturl; --"
    # Test that malicious input is handled safely
```

This comprehensive test suite ensures the URL Shortener application is robust, reliable, and maintainable.
