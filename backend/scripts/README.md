# Backend Scripts

Utility scripts for the Nexus Analyzer backend.

## Security Scripts

### generate_secret_key.py

Generate cryptographically secure SECRET_KEY values for JWT token signing.

**Usage:**

```bash
# Generate a single key (64 characters)
python backend/scripts/generate_secret_key.py

# Generate a longer key
python backend/scripts/generate_secret_key.py --length 128

# Generate keys for multiple environments
python backend/scripts/generate_secret_key.py --multiple 3
```

**Output:**

```
SECRET_KEY=aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5zA7bC9dE1fG3hI5jK7lM9nO1pQ3
```

**Important:**

1. **Never commit SECRET_KEY to version control**
2. **Use different keys for each environment** (development, staging, production)
3. **Rotate keys periodically** (every 90 days recommended)
4. **If compromised, generate a new key immediately**

**Adding to .env:**

Copy the generated key to your `.env` file:

```bash
# Generate key and copy to clipboard (Linux)
python backend/scripts/generate_secret_key.py | tail -1 | xclip -selection clipboard

# Or manually copy the output
python backend/scripts/generate_secret_key.py
# Then paste into .env file
```

**Security Requirements:**

- Minimum length: 32 characters (enforced by validation)
- High entropy: Must have variety of characters
- Cryptographically random: Generated using Python's `secrets` module
- No weak patterns: Cannot contain "password", "secret", "example", etc.

**Validation:**

The application validates SECRET_KEY on startup:

- ✅ Checks minimum length (32 characters)
- ✅ Detects weak/example keys
- ✅ Measures entropy (unique characters)
- ✅ **Fails in production** if weak key detected
- ⚠️ **Warns in development** if weak key detected

**Example Error:**

```
ValueError: SECRET_KEY must be at least 32 characters (got 16).
Generate a secure key with: python backend/scripts/generate_secret_key.py
```

**Example Warning:**

```
======================================================================
WARNING: SECRET_KEY appears to contain weak/example text: 'change-me'
This is a SECURITY RISK in production!
Generate a secure key with:
  python backend/scripts/generate_secret_key.py
======================================================================
```

## Best Practices

### Development Environment

```bash
# Generate a development key
python backend/scripts/generate_secret_key.py > .env.dev
# Edit .env.dev and copy SECRET_KEY line to .env
```

### Staging Environment

```bash
# Generate a different key for staging
python backend/scripts/generate_secret_key.py --length 128
# Add to your staging .env or secrets manager
```

### Production Environment

```bash
# Generate a production key
python backend/scripts/generate_secret_key.py --length 128

# Store in secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
# Or use environment variable injection in your deployment platform
```

**Never:**
- ❌ Use the same key across environments
- ❌ Commit keys to Git
- ❌ Share keys via email or chat
- ❌ Use predictable patterns
- ❌ Ignore validation warnings

**Always:**
- ✅ Use the generation script
- ✅ Store in secrets manager
- ✅ Use different keys per environment
- ✅ Rotate keys periodically
- ✅ Monitor for compromises
