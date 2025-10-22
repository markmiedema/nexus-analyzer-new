# Security Guide

Security best practices and configuration for Nexus Analyzer.

## Table of Contents

- [SECRET_KEY Management](#secret_key-management)
- [Environment Configuration](#environment-configuration)
- [JWT Token Security](#jwt-token-security)
- [Database Security](#database-security)
- [API Security](#api-security)
- [Deployment Security](#deployment-security)

## SECRET_KEY Management

The `SECRET_KEY` is the most critical security configuration. It's used for:
- JWT token signing and verification
- Session management
- CSRF token generation

### Generating a Secure SECRET_KEY

**Never use example or weak keys!** Always generate cryptographically secure keys:

```bash
# Generate a secure 64-character key
python backend/scripts/generate_secret_key.py

# Generate a longer 128-character key (recommended for production)
python backend/scripts/generate_secret_key.py --length 128

# Generate keys for multiple environments
python backend/scripts/generate_secret_key.py --multiple 3
```

### SECRET_KEY Requirements

The application enforces the following requirements:

1. **Minimum Length:** 32 characters (256 bits)
2. **High Entropy:** Must contain variety of characters (16+ unique chars)
3. **No Weak Patterns:** Cannot contain common words like:
   - "password", "secret", "example"
   - "change-me", "your-secret-key"
   - "test", "demo", "dev"

### Validation Behavior

**Development:**
- ⚠️ Warns about weak keys but allows startup
- Displays detailed error messages

**Production (ENVIRONMENT=production):**
- ❌ **Fails immediately** if weak key detected
- Prevents application startup
- Protects against accidental weak key usage

### Adding SECRET_KEY to .env

1. Generate a key:
   ```bash
   python backend/scripts/generate_secret_key.py
   ```

2. Copy the output to your `.env` file:
   ```bash
   SECRET_KEY=aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5zA7bC9dE1fG3hI5jK7lM9nO1pQ3
   ```

3. Restart your backend:
   ```bash
   docker compose restart backend
   ```

### Key Rotation

Rotate SECRET_KEY periodically for security:

**Recommended Schedule:**
- Development: Rotate when compromised
- Staging: Every 90 days
- Production: Every 90 days or when compromised

**Rotation Process:**

1. Generate new key:
   ```bash
   python backend/scripts/generate_secret_key.py --length 128
   ```

2. Update secrets manager or environment variables

3. Deploy with new key

4. **Note:** Rotating SECRET_KEY will invalidate all existing JWT tokens!
   - Users will need to log in again
   - Plan rotation during low-traffic periods
   - Consider implementing a grace period with dual-key support

### Storing SECRET_KEY Securely

**Development:**
- Store in `.env` file (never commit to Git!)
- Add `.env` to `.gitignore` (already configured)

**Staging/Production:**
- Use secrets manager:
  - AWS Secrets Manager
  - Azure Key Vault
  - Google Cloud Secret Manager
  - HashiCorp Vault
- Or use environment variable injection from your deployment platform

**Never:**
- ❌ Commit SECRET_KEY to Git
- ❌ Share via email, Slack, or other insecure channels
- ❌ Use the same key across environments
- ❌ Store in plain text in documentation
- ❌ Include in Docker images

## Environment Configuration

### Environment Separation

Use different configurations for each environment:

```
Development  → .env (local, weak passwords OK)
Staging      → Secrets Manager (production-like)
Production   → Secrets Manager (strong everything)
```

### Required Environment Variables

```bash
# Minimum required for startup
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=<64+ character secure key>
```

### Recommended Security Settings

```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
ENABLE_EMAIL_VERIFICATION=true
ACCESS_TOKEN_EXPIRE_MINUTES=15  # Shorter for production

# Disable registration if not needed
ENABLE_REGISTRATION=false
```

## JWT Token Security

### Current Implementation

- Algorithm: HS256 (HMAC with SHA-256)
- Token expiration: 30 minutes (configurable)
- Signed with SECRET_KEY

### Token Expiration

**Development:**
```bash
ACCESS_TOKEN_EXPIRE_MINUTES=30  # 30 minutes
```

**Production:**
```bash
ACCESS_TOKEN_EXPIRE_MINUTES=15  # 15 minutes for better security
```

### Future Improvements (Phase 1, Task 6)

- Move tokens to httpOnly cookies
- Implement refresh tokens
- Add token rotation
- Consider asymmetric keys (RS256)

## Database Security

### Password Requirements

**Development:**
```bash
POSTGRES_PASSWORD=nexus_password_change_me  # Weak OK for local dev
```

**Production:**
```bash
POSTGRES_PASSWORD=<strong-random-password-32+chars>
```

Generate strong database passwords:
```bash
python backend/scripts/generate_secret_key.py --length 32
```

### Database Security Checklist

- ✅ Use strong passwords (32+ characters)
- ✅ Restrict network access (localhost or private network only)
- ✅ Enable SSL/TLS for database connections
- ✅ Regular backups with encryption
- ✅ Principle of least privilege for database users
- ✅ Audit logging enabled

## API Security

### CORS Configuration

Restrict allowed origins:

```bash
# Development
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Production - only your domain
CORS_ORIGINS=https://app.yourcompany.com,https://api.yourcompany.com
```

### Rate Limiting

Implemented in Phase 1, Task 5:
- Prevents brute force attacks
- Limits API abuse
- Protects against DDoS

### Input Validation

- All input validated with Pydantic schemas
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention in frontend

## Deployment Security

### Docker Security

**Don't run as root:**
```dockerfile
USER appuser  # Run as non-root user
```

**Scan images for vulnerabilities:**
```bash
docker scan nexus-backend:latest
```

### Secrets Management

**AWS Example:**
```bash
# Store SECRET_KEY in AWS Secrets Manager
aws secretsmanager create-secret \
  --name nexus-analyzer/production/secret-key \
  --secret-string "your-generated-key"

# Retrieve in deployment
SECRET_KEY=$(aws secretsmanager get-secret-value \
  --secret-id nexus-analyzer/production/secret-key \
  --query SecretString --output text)
```

### HTTPS/TLS

**Always use HTTPS in production:**
- Obtain SSL certificate (Let's Encrypt recommended)
- Configure reverse proxy (nginx, Caddy, Traefik)
- Redirect HTTP → HTTPS
- Use HSTS headers

### Security Headers

Add these headers in your reverse proxy:

```nginx
# nginx example
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

## Incident Response

### If SECRET_KEY is Compromised

1. **Immediately** generate a new SECRET_KEY
2. Update all environments
3. Invalidate all existing sessions/tokens
4. Notify users to log in again
5. Review access logs for suspicious activity
6. Document the incident

### Security Checklist

Before going to production:

- [ ] SECRET_KEY is strong (64+ characters, high entropy)
- [ ] Different SECRET_KEY per environment
- [ ] SECRET_KEY stored in secrets manager
- [ ] Database password is strong
- [ ] CORS origins restricted to production domains
- [ ] HTTPS/TLS enabled
- [ ] Security headers configured
- [ ] Email verification enabled
- [ ] Rate limiting enabled
- [ ] Audit logging enabled
- [ ] Regular backups configured
- [ ] Monitoring and alerts set up

## Security Updates

Keep dependencies updated:

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade fastapi

# Update all packages (test thoroughly!)
pip install --upgrade -r requirements.txt
```

## Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Email: security@yourcompany.com (update with your contact)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We'll respond within 48 hours and keep you updated on the fix.

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Pydantic Security](https://docs.pydantic.dev/latest/concepts/validators/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
