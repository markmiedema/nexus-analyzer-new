#!/usr/bin/env python3
"""
Test SECRET_KEY validation logic.

This script tests various SECRET_KEY values to ensure validation works correctly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_secret_key_validation():
    """Test SECRET_KEY validation with various inputs."""

    test_cases = [
        {
            "name": "Valid strong key",
            "key": "aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5zA7bC9dE1fG3hI5jK7lM9nO1pQ3",
            "should_pass": True,
            "environment": "development"
        },
        {
            "name": "Too short (less than 32 chars)",
            "key": "short-key-only-20chars",
            "should_pass": False,
            "environment": "development"
        },
        {
            "name": "Weak key with 'password'",
            "key": "my-super-password-that-is-long-enough-32-characters",
            "should_pass": True,  # Passes in dev with warning
            "environment": "development",
            "expects_warning": True
        },
        {
            "name": "Weak key with 'password' in production",
            "key": "my-super-password-that-is-long-enough-32-characters",
            "should_pass": False,  # Fails in production
            "environment": "production"
        },
        {
            "name": "Example key from .env.example",
            "key": "your-secret-key-min-32-chars-change-in-production",
            "should_pass": True,  # Passes in dev with warning
            "environment": "development",
            "expects_warning": True
        },
        {
            "name": "Low entropy key",
            "key": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # 36 a's
            "should_pass": True,
            "environment": "development",
            "expects_warning": True
        },
    ]

    print("="*70)
    print("SECRET_KEY Validation Tests")
    print("="*70)

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"  Key: {test['key'][:40]}{'...' if len(test['key']) > 40 else ''}")
        print(f"  Environment: {test['environment']}")
        print(f"  Expected: {'PASS' if test['should_pass'] else 'FAIL'}")

        # Set environment variable
        os.environ['SECRET_KEY'] = test['key']
        os.environ['ENVIRONMENT'] = test['environment']
        os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'

        try:
            # Import config (this triggers validation)
            # Need to reload module to re-run validation
            import importlib
            if 'config' in sys.modules:
                importlib.reload(sys.modules['config'])
            else:
                import config

            # If we get here, validation passed
            if test['should_pass']:
                print(f"  Result: ✅ PASSED (as expected)")
                passed += 1
            else:
                print(f"  Result: ❌ FAILED (should have raised error)")
                failed += 1

        except ValueError as e:
            # Validation failed
            if not test['should_pass']:
                print(f"  Result: ✅ PASSED (correctly rejected)")
                print(f"  Error: {str(e)[:60]}...")
                passed += 1
            else:
                print(f"  Result: ❌ FAILED (unexpected error)")
                print(f"  Error: {e}")
                failed += 1
        except Exception as e:
            print(f"  Result: ❌ FAILED (unexpected exception: {type(e).__name__})")
            print(f"  Error: {e}")
            failed += 1

    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70)

    return failed == 0

if __name__ == '__main__':
    success = test_secret_key_validation()
    sys.exit(0 if success else 1)
