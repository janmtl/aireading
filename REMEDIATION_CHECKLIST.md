# Security Vulnerability Remediation Checklist

This checklist tracks the remediation of vulnerabilities identified in the security audit report.

**Audit Date:** July 1, 2026  
**Last Updated:** July 1, 2026

---

## Critical Priority (Fix within 24-48 hours)

### 🔴 VULN-001: Server-Side Request Forgery (SSRF)

**Status:** 📋 Ready to Implement  
**Files Affected:** `fetch_sources.py`  
**Solution Provided:** `security_fixes/url_validator.py`

**Action Items:**
- [ ] Import URLValidator into fetch_sources.py
- [ ] Add URL validation before all feedparser.parse() calls
- [ ] Add URL validation before any requests library calls
- [ ] Update ALLOWED_DOMAINS list with all legitimate sources
- [ ] Test with malicious URLs (AWS metadata, localhost, private IPs)
- [ ] Add logging for blocked URLs
- [ ] Update documentation with URL security requirements

**Integration Code:**
```python
from security_fixes.url_validator import URLValidator

class SourceFetcher:
    def __init__(self, config):
        self.validator = URLValidator()
        # ... rest of init
    
    def _fetch_rss(self, feed_config):
        # Validate URL first
        is_safe, error = self.validator.is_safe_url(feed_config['url'])
        if not is_safe:
            print(f"Blocked unsafe URL: {error}")
            return []
        
        feed = feedparser.parse(feed_config['url'])
        # ... rest of method
```

**Verification:**
- [ ] Unit test: Attempt to fetch AWS metadata endpoint (should fail)
- [ ] Unit test: Attempt to fetch localhost URL (should fail)
- [ ] Unit test: Attempt to fetch private IP (should fail)
- [ ] Integration test: Verify legitimate feeds still work

---

### 🔴 VULN-002: Cross-Site Scripting (XSS)

**Status:** 📋 Ready to Implement  
**Files Affected:** `generate_summary.py`, `template.html`  
**Solution Provided:** `security_fixes/safe_template_renderer.py`

**Action Items:**
- [ ] Replace Template() with Environment() + autoescape
- [ ] Import SafeTemplateRenderer
- [ ] Update generate_html() function to use SafeTemplateRenderer
- [ ] Add security meta tags to template.html
- [ ] Add safe_url filter to all URL outputs
- [ ] Test with XSS payloads in titles and descriptions
- [ ] Add CSP headers in deployment configuration

**Integration Code:**
```python
from security_fixes.safe_template_renderer import SafeTemplateRenderer, add_security_meta_tags

def generate_html(summaries, output_dir):
    renderer = SafeTemplateRenderer(".")
    html = renderer.render_template("template.html", context)
    html = add_security_meta_tags(html)
    
    # Save securely
    handler = SafeFileHandler(output_dir)
    handler.safe_write("index.html", html)
```

**Verification:**
- [ ] Unit test: Inject `<script>alert('XSS')</script>` in title (should be escaped)
- [ ] Unit test: Inject `javascript:` URL (should be filtered)
- [ ] Manual test: View source of generated HTML, verify escaping
- [ ] Browser test: Open in browser, check console for errors

---

## High Priority (Fix within 1 week)

### 🟠 VULN-003: Path Traversal

**Status:** 📋 Ready to Implement  
**Files Affected:** `generate_summary.py`  
**Solution Provided:** `security_fixes/safe_file_operations.py`

**Action Items:**
- [ ] Import SafeFileHandler
- [ ] Replace all Path() operations with SafeFileHandler
- [ ] Update save_summary() to use safe_write()
- [ ] Update load_recent_summaries() to use safe_read()
- [ ] Add path validation in config loading
- [ ] Test with path traversal attempts

**Integration Code:**
```python
from security_fixes.safe_file_operations import SafeFileHandler

def save_summary(summary, output_dir):
    handler = SafeFileHandler(output_dir)
    date_str = datetime.now().strftime("%Y-%m-%d")
    handler.safe_write(f"{date_str}.json", json.dumps(summary, indent=2))
```

**Verification:**
- [ ] Unit test: Try `../../etc/passwd` path (should raise ValueError)
- [ ] Unit test: Try absolute path `/tmp/malicious` (should raise ValueError)
- [ ] Integration test: Verify normal operation still works

---

### 🟠 VULN-004: Information Disclosure via Debug Files

**Status:** 📋 Ready to Implement  
**Files Affected:** `generate_summary.py`  
**Solution Provided:** `security_fixes/safe_file_operations.py`

**Action Items:**
- [ ] Import DebugFileHandler
- [ ] Replace direct file writes with debug_handler.write_debug_file()
- [ ] Add automatic cleanup of old debug files
- [ ] Update .gitignore to exclude debug files
- [ ] Set restrictive permissions on debug directory
- [ ] Add logging instead of file writes where appropriate

**Integration Code:**
```python
from security_fixes.safe_file_operations import DebugFileHandler

class SummaryGenerator:
    def __init__(self, config):
        self.debug_handler = DebugFileHandler("ai-digest")
        # ... rest of init
    
    def generate_summary(self, items):
        try:
            summary_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            # Write to secure temp location
            debug_file = self.debug_handler.write_debug_file(
                response_text,
                "json_parse_error"
            )
            print(f"Debug info saved to {debug_file}")
```

**Verification:**
- [ ] Unit test: Verify debug files go to temp directory
- [ ] Unit test: Verify file permissions are 0o600
- [ ] Integration test: Trigger JSON error, verify file location
- [ ] Manual test: Check that debug files are not in git

---

### 🟠 VULN-005: Insufficient Input Validation

**Status:** 📋 Ready to Implement  
**Files Affected:** `fetch_sources.py`  
**Solution Provided:** `security_fixes/input_sanitizer.py`

**Action Items:**
- [ ] Import InputSanitizer and PromptInjectionDetector
- [ ] Sanitize all RSS feed content before processing
- [ ] Sanitize all arXiv content before processing
- [ ] Add length limits to all fields
- [ ] Add prompt injection detection with logging
- [ ] Strip dangerous HTML/script tags
- [ ] Add URL validation for link fields

**Integration Code:**
```python
from security_fixes.input_sanitizer import InputSanitizer, PromptInjectionDetector

class SourceFetcher:
    def __init__(self, config):
        self.sanitizer = InputSanitizer()
        self.detector = PromptInjectionDetector()
        # ... rest of init
    
    def _fetch_rss(self, feed_config):
        # ... fetch feed ...
        
        for entry in feed.entries:
            raw_item = {
                'title': entry.get('title'),
                'url': entry.get('link'),
                'summary': entry.get('summary'),
            }
            
            # Sanitize
            sanitized = self.sanitizer.sanitize_feed_item(raw_item)
            
            # Check for prompt injection
            is_suspicious, patterns = self.detector.detect_injection(
                sanitized['title'] + ' ' + sanitized['summary']
            )
            if is_suspicious:
                print(f"⚠️  Suspicious content detected: {patterns}")
            
            items.append(sanitized)
```

**Verification:**
- [ ] Unit test: Inject `<script>` tags (should be removed)
- [ ] Unit test: Send 10,000 character title (should be truncated)
- [ ] Unit test: Test prompt injection patterns (should be detected)
- [ ] Integration test: Process real RSS feeds, verify no breakage

---

### 🟠 VULN-006: Insecure Deserialization

**Status:** 📋 Ready to Implement  
**Files Affected:** `generate_summary.py`  
**Solution Provided:** `security_fixes/safe_file_operations.py`

**Action Items:**
- [ ] Import SecureJSONHandler
- [ ] Add JSON schema validation for all loaded summaries
- [ ] Validate structure before processing
- [ ] Add size limits for JSON files
- [ ] Handle validation errors gracefully

**Integration Code:**
```python
from security_fixes.safe_file_operations import SecureJSONHandler

def load_recent_summaries(summary_dir, days=30):
    summaries = []
    
    for filepath in sorted(summary_path.glob("*.json"), reverse=True):
        try:
            # Load with size limit
            data = SecureJSONHandler.safe_json_load(filepath, max_size=10_000_000)
            
            # Validate structure
            is_valid, error = SecureJSONHandler.validate_summary(data)
            if not is_valid:
                print(f"Invalid summary {filepath}: {error}")
                continue
            
            data['date'] = filepath.stem
            summaries.append(data)
            
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    return summaries
```

**Verification:**
- [ ] Unit test: Load valid JSON (should succeed)
- [ ] Unit test: Load invalid JSON structure (should fail validation)
- [ ] Unit test: Load 100MB JSON (should fail size check)
- [ ] Integration test: Verify normal summaries load correctly

---

## Medium Priority (Fix within 2 weeks)

### 🟡 VULN-007: Regular Expression Denial of Service (ReDoS)

**Action Items:**
- [ ] Review all regex patterns for catastrophic backtracking
- [ ] Add timeout to regex operations
- [ ] Limit input size before applying regex
- [ ] Replace complex patterns with simpler alternatives

**Code Example:**
```python
import re
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Regex timeout")

def safe_regex_sub(pattern, replacement, text, timeout=1.0):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout))
    try:
        result = re.sub(pattern, replacement, text)
    finally:
        signal.alarm(0)
    return result
```

---

### 🟡 VULN-008: Missing Rate Limiting

**Action Items:**
- [ ] Implement token bucket rate limiter
- [ ] Add per-source rate limits
- [ ] Track failed requests
- [ ] Implement exponential backoff
- [ ] Add monitoring for rate limit violations

**Code Example:**
```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def allow_request(self, source):
        now = time.time()
        minute_ago = now - 60
        
        # Remove old requests
        self.requests[source] = [
            t for t in self.requests[source] if t > minute_ago
        ]
        
        # Check limit
        if len(self.requests[source]) >= self.requests_per_minute:
            return False
        
        self.requests[source].append(now)
        return True
```

---

### 🟡 VULN-009: Unsafe Git Operations

**Action Items:**
- [ ] Create separate branch for automated commits
- [ ] Add file content validation before committing
- [ ] Implement commit signing
- [ ] Add branch protection rules
- [ ] Review workflow permissions

**Workflow Update:**
```yaml
- name: Commit and push summaries
  run: |
    git checkout -b auto-update-$(date +%Y%m%d)
    git add summaries/*.json public/index.html
    
    # Validate files before committing
    python validate_generated_files.py
    
    if git diff --staged --quiet; then
      echo "No changes"
    else
      git commit -m "Auto-update AI digest - $(date +'%Y-%m-%d')"
      git push -u origin auto-update-$(date +%Y%m%d)
      
      # Create PR instead of direct push to main
      gh pr create --title "Auto-update $(date +'%Y-%m-%d')" \
                   --body "Automated digest update" \
                   --base main
    fi
```

---

### 🟡 VULN-010: Hardcoded Model Parameters

**Action Items:**
- [ ] Add configuration validation function
- [ ] Implement min/max limits for all numeric configs
- [ ] Add cost estimation and warnings
- [ ] Validate model names against allowlist
- [ ] Add monitoring for configuration changes

**Code Example:**
```python
def validate_config(config):
    llm = config.get('llm', {})
    
    # Validate max_tokens
    max_tokens = llm.get('max_tokens', 4000)
    if not 100 <= max_tokens <= 100000:
        raise ValueError("max_tokens must be between 100 and 100000")
    
    # Validate temperature
    temp = llm.get('temperature', 0.3)
    if not 0.0 <= temp <= 2.0:
        raise ValueError("temperature must be between 0.0 and 2.0")
    
    # Validate model
    allowed_models = [
        'claude-3-5-sonnet-20241022',
        'claude-sonnet-5',
        'gpt-4-turbo',
    ]
    model = llm.get('model')
    if model not in allowed_models:
        raise ValueError(f"model must be one of: {allowed_models}")
    
    return True
```

---

## Low Priority (Fix within 1 month)

### 🔵 VULN-011: Insecure File Permissions

**Action Items:**
- [ ] Set umask at process start
- [ ] Set explicit permissions on all created files
- [ ] Review directory permissions
- [ ] Document permission requirements

**Code Example:**
```python
import os

# At start of program
os.umask(0o077)  # Restrict new files to owner only

# When creating files
with open(filepath, 'w') as f:
    f.write(content)
os.chmod(filepath, 0o600)  # Read/write for owner only
```

---

### 🔵 VULN-012: Missing Security Headers

**Action Items:**
- [ ] Add security meta tags to template.html
- [ ] Document CSP configuration for web servers
- [ ] Add security headers documentation for Amplify
- [ ] Add security headers for GitHub Pages

**Template Update:**
```html
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="Content-Security-Policy" 
          content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
    <meta name="referrer" content="strict-origin-when-cross-origin">
    <!-- ... rest of head ... -->
</head>
```

---

## Ongoing Tasks

### Dependency Security

**Action Items:**
- [ ] Run `pip install safety && safety check`
- [ ] Review Dependabot alerts
- [ ] Update all dependencies to latest versions
- [ ] Pin dependency versions with hash verification
- [ ] Set up automated dependency updates

**Commands:**
```bash
# Check for vulnerabilities
pip install safety
safety check -r requirements.txt

# Update dependencies
pip install --upgrade -r requirements.txt

# Pin with hashes
pip freeze > requirements-locked.txt
pip-compile --generate-hashes requirements.txt
```

---

### Secret Management

**Action Items:**
- [ ] Verify .env files in .gitignore
- [ ] Run secret scanning tool (TruffleHog, GitLeaks)
- [ ] Add pre-commit hook for secret detection
- [ ] Document secret rotation process
- [ ] Set up secret scanning in GitHub

**Commands:**
```bash
# Install pre-commit
pip install pre-commit

# Add .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
EOF

pre-commit install
```

---

### CI/CD Security

**Action Items:**
- [ ] Pin all GitHub Actions to specific commits
- [ ] Enable Dependabot for Actions
- [ ] Review workflow permissions
- [ ] Add branch protection rules
- [ ] Enable required reviews for PRs

**Branch Protection Settings:**
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Include administrators
- ✅ Restrict who can push to matching branches

---

## Testing Plan

### Unit Tests

```bash
# Create test file
cat > test_security.py << 'EOF'
import pytest
from security_fixes.url_validator import URLValidator
from security_fixes.input_sanitizer import InputSanitizer

def test_ssrf_protection():
    validator = URLValidator()
    
    # Should block AWS metadata
    is_safe, _ = validator.is_safe_url("http://169.254.169.254/")
    assert not is_safe
    
    # Should block localhost
    is_safe, _ = validator.is_safe_url("http://localhost:8080/")
    assert not is_safe
    
    # Should allow legitimate
    is_safe, _ = validator.is_safe_url("https://huggingface.co/blog/feed.xml")
    assert is_safe

def test_xss_protection():
    sanitizer = InputSanitizer()
    
    malicious = '<script>alert("XSS")</script>Title'
    safe = sanitizer.sanitize_text(malicious, 100)
    
    assert '<script>' not in safe
    assert 'Title' in safe

def test_path_traversal():
    from security_fixes.safe_file_operations import SafeFileHandler
    
    handler = SafeFileHandler("./test_dir")
    
    with pytest.raises(ValueError):
        handler.safe_path("../../etc/passwd")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
EOF

python test_security.py
```

### Integration Tests

```bash
# Test full workflow with security fixes
python generate_summary.py

# Verify no debug files in current directory
ls debug_response_*.txt 2>/dev/null || echo "✓ No debug files in CWD"

# Verify HTML is safe
grep '<script>' public/index.html && echo "✗ XSS found" || echo "✓ No XSS"

# Verify paths are safe
python -c "
from pathlib import Path
html_path = Path('public/index.html').resolve()
base_path = Path('public').resolve()
assert html_path.is_relative_to(base_path), 'Path traversal'
print('✓ Paths are safe')
"
```

---

## Deployment Checklist

Before deploying to production:

- [ ] All Critical vulnerabilities fixed
- [ ] All High vulnerabilities fixed
- [ ] Security tests passing
- [ ] Dependencies updated
- [ ] Secret scanning completed
- [ ] Branch protection enabled
- [ ] Security headers configured
- [ ] Monitoring/alerting set up
- [ ] Incident response plan documented
- [ ] Security contact information updated

---

## Documentation Updates

- [ ] Update README.md with security considerations
- [ ] Create SECURITY.md with disclosure policy
- [ ] Document security architecture
- [ ] Add security section to CONTRIBUTING.md
- [ ] Create runbook for security incidents

---

## Sign-off

**Security Lead:** _________________  
**Date:** _________________

**Development Lead:** _________________  
**Date:** _________________

---

**Next Review Date:** August 1, 2026

