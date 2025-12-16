# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.3.x   | :white_check_mark: |
| < 2.3   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, please report it privately:

1. **GitHub Security Advisory:** Use GitHub's private vulnerability reporting feature (recommended)
2. **Email:** Open a GitHub issue with the `[SECURITY]` tag in the title

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue before making it public.

## Security Best Practices

When using this tool:

- **Never commit sensitive data:** Keep `release.json` and `artist-defaults.json` out of version control (they're gitignored)
- **Validate inputs:** Always validate configuration files before running
- **Review dependencies:** Regularly update dependencies for security patches
- **Use trusted sources:** Only download from official repository

## Known Security Considerations

- This tool processes local files only - no network requests are made
- No authentication or API keys are required
- Configuration files may contain sensitive artist information - keep them private

