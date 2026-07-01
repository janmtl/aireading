# Security Fixes Reference

This directory contains example implementations of security fixes for vulnerabilities identified in the security audit.

## Overview

These modules provide secure alternatives to vulnerable code patterns found in the main codebase. They can be integrated directly or used as reference for implementing fixes.

## Modules

### 1. URL Validator (`url_validator.py`)

**Fixes:** VULN-001 (SSRF)

Validates URLs before fetching to prevent Server-Side Request Forgery attacks.

**Features:**
- Domain allowlisting
- Private IP blocking (RFC 1918, AWS metadata, etc.)
- DNS resolution with IP checks
- Port filtering
- Timeout protection

**Usage:**
```python
from security_fixes.url_validator import URLValidator

validator = URLValidator()

# Validate before fetching
is_safe, error = validator.is_safe_url(feed_url)
if not is_safe:
    print(f"Blocked unsafe URL: {error}")
    return

# Or raise exception on invalid URL
try:
    validator.validate_or_raise(feed_url)
    feed = feedparser.parse(feed_url)
except ValueError as e:
    print(f"Invalid URL: {e}")
```

### 2. Input Sanitizer (`input_sanitizer.py`)

**Fixes:** VULN-005 (Input Validation)

Sanitizes and validates external content from RSS feeds and arXiv.

**Features:**
- HTML/script tag stripping
- Control character removal
- Length limits
- URL validation
- Prompt injection detection
- Whitespace normalization

**Usage:**
```python
from security_fixes.input_sanitizer import InputSanitizer, PromptInjectionDetector

sanitizer = InputSanitizer()
detector = PromptInjectionDetector()

# Sanitize individual fields
safe_title = sanitizer.sanitize_text(raw_title, max_length=500)
safe_url = sanitizer.sanitize_url(raw_url)

# Sanitize entire feed item
sanitized_item = sanitizer.sanitize_feed_item(raw_item)

# Detect prompt injection
is_suspicious, patterns = detector.detect_injection(text)
if is_suspicious:
    print(f"Warning: Potential prompt injection: {patterns}")
```

### 3. Safe File Operations (`safe_file_operations.py`)

**Fixes:** VULN-003 (Path Traversal), VULN-004 (Debug Files)

Provides secure file operations with path validation.

**Features:**
- Path traversal prevention
- Automatic permission setting
- Size limits for reads
- Secure debug file handling
- JSON validation
- Automatic cleanup

**Usage:**
```python
from security_fixes.safe_file_operations import SafeFileHandler, DebugFileHandler

# For regular file operations
handler = SafeFileHandler("summaries")

# Write safely - path traversal is blocked
try:
    handler.safe_write("2026-07-01.json", json_content)
except ValueError as e:
    print(f"Invalid path: {e}")

# Read safely with size limit
content = handler.safe_read("2026-07-01.json", max_size=10_000_000)

# For debug files - automatically uses temp directory
debug_handler = DebugFileHandler("ai-digest")
debug_file = debug_handler.write_debug_file(error_content, "json_parse_error")

# Cleanup old debug files
debug_handler.cleanup_old_files(max_age_seconds=86400)
```

### 4. Safe Template Renderer (`safe_template_renderer.py`)

**Fixes:** VULN-002 (XSS)

Renders templates with automatic HTML escaping to prevent XSS attacks.

**Features:**
- Jinja2 auto-escaping enabled
- Safe URL filter
- Content Security Policy generator
- Security headers
- Meta tag injection

**Usage:**
```python
from security_fixes.safe_template_renderer import SafeTemplateRenderer, ContentSecurityPolicy

# Create renderer with auto-escaping
renderer = SafeTemplateRenderer(".")

# Render template - all variables are auto-escaped
html = renderer.render_template("template.html", context)

# Add security meta tags
from security_fixes.safe_template_renderer import add_security_meta_tags
secure_html = add_security_meta_tags(html)

# Generate CSP header
csp = ContentSecurityPolicy()
headers = csp.get_security_headers()
```

## Integration Guide

### Step 1: Install in Main Codebase

Copy these modules to your project:

```bash
cp -r security_fixes/ /path/to/project/
```

### Step 2: Update `fetch_sources.py`

Replace unsafe URL fetching:

```python
# OLD - VULNERABLE
def _fetch_rss(self, feed_config: Dict[str, str]) -> List[Dict[str, Any]]:
    feed = feedparser.parse(feed_config['url'])

# NEW - SECURE
from security_fixes.url_validator import URLValidator
from security_fixes.input_sanitizer import InputSanitizer

class SourceFetcher:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.url_validator = URLValidator()
        self.input_sanitizer = InputSanitizer()
        # ... rest of init
    
    def _fetch_rss(self, feed_config: Dict[str, str]) -> List[Dict[str, Any]]:
        # Validate URL first
        url = feed_config['url']
        is_safe, error = self.url_validator.is_safe_url(url)
        if not is_safe:
            print(f"    Blocked unsafe URL: {error}")
            return []
        
        # Fetch feed
        feed = feedparser.parse(url)
        
        # Sanitize each item
        items = []
        for entry in feed.entries:
            raw_item = {
                'title': entry.get('title', 'Untitled'),
                'url': entry.get('link', ''),
                'summary': entry.get('summary', ''),
                # ... other fields
            }
            sanitized = self.input_sanitizer.sanitize_feed_item(raw_item)
            items.append(sanitized)
        
        return items
```

### Step 3: Update `generate_summary.py`

Replace unsafe file operations and template rendering:

```python
# OLD - VULNERABLE
from jinja2 import Template

with open(template_path, 'r') as f:
    template = Template(f.read())  # No autoescape!

# NEW - SECURE
from security_fixes.safe_template_renderer import SafeTemplateRenderer
from security_fixes.safe_file_operations import SafeFileHandler, DebugFileHandler

class SummaryGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # ... other init
        
        # Initialize secure handlers
        self.file_handler = SafeFileHandler("summaries")
        self.debug_handler = DebugFileHandler("ai-digest")
    
    def generate_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        # ... existing code ...
        
        # On JSON parsing error
        try:
            summary_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            # Use secure debug handler instead of writing to CWD
            debug_file = self.debug_handler.write_debug_file(
                response_text,
                "json_parse_error"
            )
            print(f"Raw response saved to {debug_file}")
            # ... rest of error handling

def generate_html(summaries: List[Dict[str, Any]], output_dir: str):
    """Generate the HTML page from summaries."""
    
    # Use secure template renderer
    renderer = SafeTemplateRenderer(".")
    html_content = renderer.render_template("template.html", {
        'latest_summary': latest_summary,
        'weekly_items': weekly_items[:10],
        # ... rest of context
    })
    
    # Add security meta tags
    from security_fixes.safe_template_renderer import add_security_meta_tags
    html_content = add_security_meta_tags(html_content)
    
    # Write with secure file handler
    handler = SafeFileHandler(output_dir)
    handler.safe_write("index.html", html_content, permissions=0o644)
```

### Step 4: Update Configuration Validation

Add validation for `config.yaml`:

```python
from security_fixes.input_sanitizer import InputSanitizer

def validate_config(config: dict) -> tuple[bool, Optional[str]]:
    """Validate configuration file."""
    
    # Validate lookback_days
    lookback = config.get('build', {}).get('lookback_days', 7)
    if not isinstance(lookback, int) or lookback < 1 or lookback > 90:
        return False, "lookback_days must be between 1 and 90"
    
    # Validate max_tokens
    max_tokens = config.get('llm', {}).get('max_tokens', 4000)
    if not isinstance(max_tokens, int) or max_tokens < 100 or max_tokens > 100000:
        return False, "max_tokens must be between 100 and 100000"
    
    # Validate directory paths don't contain traversal
    for path_key in ['summary_storage', 'output_dir']:
        path = config.get('build', {}).get(path_key, '')
        if '..' in path or path.startswith('/'):
            return False, f"{path_key} contains invalid path"
    
    return True, None

# In main():
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

is_valid, error = validate_config(config)
if not is_valid:
    print(f"Invalid configuration: {error}")
    sys.exit(1)
```

### Step 5: Update Template

The template should already work with auto-escaping, but you can add explicit escaping:

```html
<!-- In template.html, URLs should use the safe_url filter -->
<a href="{{ item.url | safe_url }}" target="_blank" rel="noopener noreferrer">
    {{ item.title }}
</a>

<!-- Other content is automatically escaped, but you can be explicit -->
<div>{{ item.core_innovation | e }}</div>
```

## Testing the Fixes

### Test URL Validator

```bash
python security_fixes/url_validator.py
```

Expected output:
- ✓ Safe URLs pass
- ✗ Unsafe URLs blocked (localhost, private IPs, AWS metadata)

### Test Input Sanitizer

```bash
python security_fixes/input_sanitizer.py
```

Expected output:
- Script tags removed
- Control characters stripped
- Long text truncated
- Prompt injection detected

### Test File Operations

```bash
python security_fixes/safe_file_operations.py
```

Expected output:
- Valid paths work
- Path traversal blocked
- Debug files go to temp directory

### Test Template Renderer

```bash
python security_fixes/safe_template_renderer.py
```

Expected output:
- Unsafe template allows XSS
- Safe template escapes XSS

## Security Testing

After integration, perform these security tests:

### 1. Test SSRF Protection

Try adding these URLs to `config.yaml`:

```yaml
sources:
  rss_feeds:
    - name: "AWS Metadata"
      url: "http://169.254.169.254/latest/meta-data/"
    - name: "Localhost"
      url: "http://localhost:8080/"
    - name: "Private IP"
      url: "http://192.168.1.1/"
```

Expected: All should be blocked with error messages.

### 2. Test XSS Protection

Create a malicious RSS feed XML:

```xml
<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>&lt;script&gt;alert('XSS')&lt;/script&gt;</title>
      <link>javascript:alert('XSS')</link>
    </item>
  </channel>
</rss>
```

Expected: Script tags escaped in output HTML, JavaScript URL removed.

### 3. Test Path Traversal

Modify `config.yaml`:

```yaml
build:
  summary_storage: "../../../etc/cron.d/"
  output_dir: "/tmp/malicious/"
```

Expected: Validation error or exception on startup.

### 4. Test Input Validation

Create RSS feed with extremely long content:

```xml
<title>A very long title that exceeds the maximum length limit...</title>
```

Expected: Title truncated to MAX_TITLE_LENGTH.

## Security Checklist

After integrating these fixes, verify:

- [ ] URL validator is called before all external requests
- [ ] Input sanitizer processes all external content
- [ ] Safe file handler is used for all file operations
- [ ] Template renderer has auto-escaping enabled
- [ ] Config validation runs on startup
- [ ] Debug files go to temp directory with restricted permissions
- [ ] Security meta tags added to HTML output
- [ ] CSP headers configured (if deploying with web server)
- [ ] Dependencies updated to latest versions
- [ ] `.gitignore` includes debug files
- [ ] Security tests pass

## Performance Considerations

These security fixes add overhead:

- **URL Validation**: DNS lookup adds ~100-500ms per URL
- **Input Sanitization**: Regex processing adds ~1-10ms per item
- **Path Validation**: Path resolution adds ~1ms per operation
- **Template Escaping**: Minimal overhead (~5% slower rendering)

For the AI Digest use case (nightly batch processing), this overhead is acceptable.

### Optimization Tips

1. **Cache DNS lookups** for repeated domains:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def cached_dns_check(hostname):
       # DNS lookup logic
   ```

2. **Pre-compile regex patterns** (already done in the modules)

3. **Batch process items** instead of one-by-one validation

4. **Skip DNS checks in development** by passing `enable_dns_check=False`

## Maintenance

### Regular Security Tasks

1. **Weekly**: Review debug files for anomalies
2. **Monthly**: Update dependencies and re-run security tests
3. **Quarterly**: Review and update domain allowlists
4. **Annually**: Full security audit

### Updating Allowlists

When adding new RSS feeds, update the allowlist:

```python
# In url_validator.py
ALLOWED_DOMAINS = [
    'huggingface.co',
    'blog.vllm.ai',
    # ... existing domains
    'your-new-domain.com',  # Add here
]
```

Or pass custom domains at runtime:

```python
custom_domains = ALLOWED_DOMAINS + config.get('custom_domains', [])
validator = URLValidator(allowed_domains=custom_domains)
```

## Additional Resources

- Full security audit: `../SECURITY_AUDIT_REPORT.md`
- Security policy: `../SECURITY.md`
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Python Security: https://python.readthedocs.io/en/latest/library/security_warnings.html

## Support

For questions or issues:

1. Review the security audit report
2. Check the example usage in each module
3. Open a GitHub issue with the `security` label
4. See SECURITY.md for vulnerability disclosure

## License

Same as main project (MIT License).
