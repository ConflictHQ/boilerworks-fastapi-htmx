# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Boilerworks, please report it responsibly.

**Do not open a public issue.**

Instead, email **security@weareconflict.com** with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge your report within 48 hours and aim to release a fix within 7 days for critical issues.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| latest  | Yes       |

## Security Best Practices

When deploying Boilerworks:

- Set a strong, unique `SECRET_KEY` — the default (`change-me-in-production`) signs session tokens and must never reach production
- Change the seeded admin credentials (`admin@boilerworks.dev` / `password` from `app/seed.py`) or skip the seed entirely in production
- Change the default PostgreSQL credentials (`postgres` / `postgres`) and do not publish the database or Redis ports beyond what your deployment needs
- Serve over HTTPS only, and add `secure=True` to the session cookie in `app/routers/auth.py` (the template sets `httponly` and `samesite="strict"` but not `Secure`, since local dev is plain HTTP)
- Set `DEBUG=false` (the default) in production
