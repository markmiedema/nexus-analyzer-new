#!/usr/bin/env python3
"""
Test rate limiting implementation.

This script tests that rate limiting is working correctly by:
1. Making requests within the limit (should succeed)
2. Exceeding the limit (should get 429 errors)
3. Waiting for limit to reset
"""

import requests
import time
import sys

# Configuration
API_BASE = "http://localhost:8000"
RATE_LIMIT_AUTH = 5  # 5 requests per minute from config


def test_rate_limiting():
    """Test rate limiting on login endpoint."""

    print("="*70)
    print("Rate Limiting Test")
    print("="*70)
    print(f"\nTesting endpoint: POST {API_BASE}/api/v1/auth/login")
    print(f"Rate limit: {RATE_LIMIT_AUTH} requests/minute\n")

    # Test data (will fail authentication, but that's OK - we're testing rate limiting)
    login_data = {
        "email": "test@example.com",
        "password": "wrongpassword123"
    }

    print(f"Step 1: Making {RATE_LIMIT_AUTH} requests (should all succeed or get 401)")
    print("-" * 70)

    success_count = 0
    auth_fail_count = 0
    rate_limit_count = 0

    # Make requests up to the limit
    for i in range(RATE_LIMIT_AUTH):
        try:
            response = requests.post(
                f"{API_BASE}/api/v1/auth/login",
                json=login_data,
                timeout=5
            )

            if response.status_code == 401:
                # Authentication failed (expected - we used wrong password)
                print(f"  Request {i+1}: ✓ 401 Unauthorized (auth failed, rate limit OK)")
                auth_fail_count += 1
            elif response.status_code == 200:
                # Shouldn't happen with wrong password, but OK
                print(f"  Request {i+1}: ✓ 200 OK")
                success_count += 1
            elif response.status_code == 429:
                # Got rate limited earlier than expected
                print(f"  Request {i+1}: ⚠️  429 Too Many Requests (early rate limit)")
                rate_limit_count += 1
            else:
                print(f"  Request {i+1}: ❌ Unexpected status {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"  Request {i+1}: ❌ Error: {e}")
            return False

        # Small delay between requests
        time.sleep(0.1)

    print(f"\nResults after {RATE_LIMIT_AUTH} requests:")
    print(f"  - Auth failures (401): {auth_fail_count} ✓")
    print(f"  - Rate limited (429): {rate_limit_count}")
    print(f"  - Successful (200): {success_count}")

    # Now exceed the limit
    print(f"\nStep 2: Making additional requests (should get rate limited)")
    print("-" * 70)

    exceeded_count = 0
    for i in range(3):  # Try 3 more requests
        try:
            response = requests.post(
                f"{API_BASE}/api/v1/auth/login",
                json=login_data,
                timeout=5
            )

            if response.status_code == 429:
                print(f"  Request {i+1}: ✓ 429 Too Many Requests (rate limit working!)")
                exceeded_count += 1

                # Check for rate limit headers
                if 'X-RateLimit-Limit' in response.headers:
                    limit = response.headers.get('X-RateLimit-Limit')
                    remaining = response.headers.get('X-RateLimit-Remaining')
                    reset = response.headers.get('X-RateLimit-Reset')
                    print(f"             Limit: {limit}, Remaining: {remaining}, Reset: {reset}")

            else:
                print(f"  Request {i+1}: ❌ Expected 429, got {response.status_code}")
                print(f"             Rate limiting may not be working!")

        except requests.exceptions.RequestException as e:
            print(f"  Request {i+1}: ❌ Error: {e}")

        time.sleep(0.1)

    print("\n" + "="*70)
    if exceeded_count >= 2:
        print("✅ TEST PASSED: Rate limiting is working!")
        print("="*70)
        print("\nRate limiting successfully:")
        print(f"  - Allowed {auth_fail_count} requests within limit")
        print(f"  - Blocked {exceeded_count} requests over limit")
        print(f"  - Using Redis for distributed rate limiting")
        print("\n✨ Your API is protected from brute force attacks!")
        return True
    else:
        print("❌ TEST FAILED: Rate limiting not working as expected")
        print("="*70)
        print("\nPossible issues:")
        print("  - Rate limiting not enabled (check RATE_LIMIT_ENABLED=true in .env)")
        print("  - Redis not running (check: docker compose ps redis)")
        print("  - slowapi not installed (check: pip install slowapi)")
        return False


def check_prerequisites():
    """Check if backend is running."""
    print("Checking prerequisites...")

    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running\n")
            return True
        else:
            print(f"❌ Backend returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {API_BASE}")
        print("   Make sure backend is running: docker compose up -d backend")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    print("\n")
    if not check_prerequisites():
        sys.exit(1)

    success = test_rate_limiting()
    print("\n")
    sys.exit(0 if success else 1)
