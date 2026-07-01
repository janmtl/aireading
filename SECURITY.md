# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

We take the security of this project seriously. If you believe you have found a security vulnerability, please report it to us responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **GitHub Security Advisories** (Preferred)
   - Go to the Security tab
   - Click "Report a vulnerability"
   - Fill out the advisory form

2. **Email**
   - Send details to the repository maintainers
   - Include "SECURITY" in the subject line

### What to Include

Please include the following information in your report:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability
- Suggested fix (if available)

### What to Expect

- **Acknowledgment:** Within 48 hours
- **Initial Assessment:** Within 1 week
- **Status Update:** Every week until resolution
- **Fix Timeline:** 
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: 1 month

### Disclosure Policy

- **Coordinated Disclosure:** We follow a coordinated disclosure process
- **Public Disclosure:** After a fix is released, typically within 90 days
- **Credit:** Security researchers will be credited (unless they prefer to remain anonymous)

### Security Update Process

1. Vulnerability is reported and confirmed
2. Fix is developed and tested
3. Security advisory is prepared
4. Fix is released
5. Advisory is published
6. CVE is requested (if applicable)

## Security Best Practices for Users

### API Key Security

- Never commit API keys to version control
- Use environment variables or secrets management
- Rotate keys regularly
- Use different keys for dev/staging/production
- Monitor API usage for anomalies

### Deployment Security

- Keep dependencies updated
- Use latest Python version
- Enable GitHub security alerts
- Review Dependabot PRs promptly
- Implement least privilege access

### Configuration Security

- Review config.yaml changes carefully
- Only add trusted RSS feed sources
- Validate external URLs before adding
- Use branch protection for main branch
- Require PR reviews for config changes

### GitHub Actions Security

- Regularly audit workflow permissions
- Use pinned action versions
- Monitor workflow runs for anomalies
- Rotate GitHub tokens periodically
- Limit secrets to necessary workflows

## Known Security Considerations

### External Content

This application fetches and processes content from external sources (RSS feeds, arXiv). While we implement security measures:

- Always review new sources before adding
- Be cautious with user-submitted feeds
- Monitor for unusual content patterns
- Keep the application updated

### LLM API Usage

The application sends external content to LLM APIs:

- Review API provider's security practices
- Be aware of data retention policies
- Avoid including sensitive information in sources
- Monitor API usage and costs

### Generated Content

HTML output is generated from external content:

- Regularly review generated pages
- Monitor for suspicious content
- Keep Jinja2 and dependencies updated
- Use Content Security Policy headers when deploying

## Security Features

### Current Security Measures

- Environment-based API key management
- Gitignore for sensitive files
- HTTPS-only external requests
- Rate limiting for API calls
- Input length limits

### Planned Security Enhancements

See SECURITY_AUDIT_REPORT.md for detailed vulnerability information and remediation plans.

## Compliance

### Data Handling

- No personal user data is collected
- External content is processed transiently
- Generated summaries are stored locally
- API keys are not logged

### Open Source Responsibilities

- Security updates are provided promptly
- CVEs are tracked and disclosed
- Dependencies are monitored for vulnerabilities
- Security advisories are published

## Security Contacts

- **Maintainer:** See repository contributors
- **Security Team:** Open a security advisory
- **Response Time:** 48 hours for acknowledgment

## Security Hall of Fame

We recognize security researchers who help improve our security:

*No reports yet - be the first!*

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Python Security Guide](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [CI/CD Security Best Practices](https://owasp.org/www-community/vulnerabilities/CI_CD_Security)

---

**Last Updated:** July 1, 2026

Thank you for helping keep this project secure!
