#!/usr/bin/env python3
"""
Generate a cryptographically secure SECRET_KEY for the application.

Usage:
    python backend/scripts/generate_secret_key.py [--length LENGTH]

The generated key will be suitable for use with JWT tokens and session management.
Minimum recommended length is 64 characters (32 bytes).
"""

import secrets
import string
import argparse
import sys


def generate_secret_key(length: int = 64) -> str:
    """
    Generate a cryptographically secure random string.

    Args:
        length: Length of the key in characters (default: 64)

    Returns:
        A secure random string suitable for SECRET_KEY
    """
    if length < 32:
        print("WARNING: SECRET_KEY length should be at least 32 characters for security.", file=sys.stderr)
        print("Using minimum length of 32.", file=sys.stderr)
        length = 32

    # Use URL-safe characters (A-Z, a-z, 0-9, -, _)
    # This is compatible with environment variables and doesn't need escaping
    alphabet = string.ascii_letters + string.digits + '-_'

    # Generate cryptographically secure random string
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))

    return secret_key


def main():
    parser = argparse.ArgumentParser(
        description="Generate a cryptographically secure SECRET_KEY",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/scripts/generate_secret_key.py
  python backend/scripts/generate_secret_key.py --length 128

Add the generated key to your .env file:
  SECRET_KEY=<generated-key-here>

SECURITY NOTES:
- Never commit SECRET_KEY to version control
- Use different keys for development, staging, and production
- Rotate keys periodically (every 90 days recommended)
- If a key is compromised, generate a new one immediately
        """
    )
    parser.add_argument(
        '--length',
        type=int,
        default=64,
        help='Length of the secret key in characters (default: 64, minimum: 32)'
    )
    parser.add_argument(
        '--multiple',
        type=int,
        default=1,
        help='Generate multiple keys (useful for rotating keys across environments)'
    )

    args = parser.parse_args()

    if args.multiple == 1:
        key = generate_secret_key(args.length)
        print(f"SECRET_KEY={key}")
    else:
        print(f"# Generated {args.multiple} SECRET_KEYs for different environments")
        print("# Use different keys for development, staging, and production\n")

        environments = ['development', 'staging', 'production']
        for i in range(args.multiple):
            key = generate_secret_key(args.length)
            env_name = environments[i] if i < len(environments) else f'env{i+1}'
            print(f"# {env_name.upper()}")
            print(f"SECRET_KEY={key}\n")


if __name__ == '__main__':
    main()
