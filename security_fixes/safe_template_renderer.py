#!/usr/bin/env python3
"""
Safe template rendering with XSS protection.
Addresses VULN-002 from security audit.
"""

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Any, Dict
import re


class SafeTemplateRenderer:
    """
    Secure HTML template renderer with automatic escaping.
    Prevents XSS attacks in generated content.
    """
    
    def __init__(self, template_dir: str = "."):
        """
        Initialize renderer with auto-escaping enabled.
        
        Args:
            template_dir: Directory containing templates
        """
        self.template_dir = Path(template_dir)
        
        # Create Jinja2 environment with security features
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),  # Auto-escape HTML/XML
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Add custom filters for additional safety
        self.env.filters['safe_url'] = self.safe_url_filter
        self.env.filters['truncate_safe'] = self.truncate_safe
    
    @staticmethod
    def safe_url_filter(url: str) -> str:
        """
        Filter for safely rendering URLs.
        
        Args:
            url: URL to filter
            
        Returns:
            Filtered URL or empty string
        """
        if not url or not isinstance(url, str):
            return ""
        
        # Only allow http and https URLs
        if not (url.startswith('http://') or url.startswith('https://')):
            return ""
        
        # Remove dangerous characters
        url = url.strip()
        url = re.sub(r'[\s<>"\']', '', url)
        
        # Length limit
        if len(url) > 2048:
            return ""
        
        return url
    
    @staticmethod
    def truncate_safe(text: str, length: int, suffix: str = '...') -> str:
        """
        Safely truncate text without breaking HTML entities.
        
        Args:
            text: Text to truncate
            length: Maximum length
            suffix: Suffix for truncated text
            
        Returns:
            Truncated text
        """
        if not text or len(text) <= length:
            return text
        
        truncated = text[:length]
        
        # Check if we're in the middle of an HTML entity
        last_ampersand = truncated.rfind('&')
        if last_ampersand != -1:
            remaining = truncated[last_ampersand:]
            if ';' not in remaining:
                # We're in the middle of an entity, remove it
                truncated = truncated[:last_ampersand]
        
        return truncated + suffix
    
    def render_template(self, template_name: str, 
                       context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name of template file
            context: Template context dictionary
            
        Returns:
            Rendered HTML string
        """
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def render_string(self, template_string: str, 
                     context: Dict[str, Any]) -> str:
        """
        Render a template string with the given context.
        
        Args:
            template_string: Template string
            context: Template context dictionary
            
        Returns:
            Rendered HTML string
        """
        template = self.env.from_string(template_string)
        return template.render(**context)


class ContentSecurityPolicy:
    """Generate Content Security Policy headers."""
    
    # Default CSP directives
    DEFAULT_DIRECTIVES = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'"],  # Note: unsafe-inline needed for inline scripts
        'style-src': ["'self'", "'unsafe-inline'"],   # Note: unsafe-inline needed for inline styles
        'img-src': ["'self'", "data:", "https:"],
        'font-src': ["'self'"],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
    }
    
    @classmethod
    def generate_policy(cls, custom_directives: Dict[str, list] = None) -> str:
        """
        Generate CSP header value.
        
        Args:
            custom_directives: Custom directives to override defaults
            
        Returns:
            CSP header value string
        """
        directives = cls.DEFAULT_DIRECTIVES.copy()
        if custom_directives:
            directives.update(custom_directives)
        
        policy_parts = []
        for directive, sources in directives.items():
            sources_str = ' '.join(sources)
            policy_parts.append(f"{directive} {sources_str}")
        
        return '; '.join(policy_parts)
    
    @classmethod
    def get_security_headers(cls) -> Dict[str, str]:
        """
        Get recommended security headers.
        
        Returns:
            Dictionary of security headers
        """
        return {
            'Content-Security-Policy': cls.generate_policy(),
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        }


def add_security_meta_tags(html_content: str) -> str:
    """
    Add security meta tags to HTML if not present.
    
    Args:
        html_content: HTML content
        
    Returns:
        HTML with security meta tags
    """
    security_tags = [
        '<meta http-equiv="X-Content-Type-Options" content="nosniff">',
        '<meta http-equiv="X-Frame-Options" content="DENY">',
        '<meta name="referrer" content="strict-origin-when-cross-origin">',
    ]
    
    # Check if <head> tag exists
    if '<head>' not in html_content.lower():
        return html_content
    
    # Find the position after <head>
    head_pattern = re.compile(r'<head[^>]*>', re.IGNORECASE)
    match = head_pattern.search(html_content)
    
    if not match:
        return html_content
    
    insert_pos = match.end()
    
    # Insert security tags
    tags_html = '\n    ' + '\n    '.join(security_tags)
    html_content = html_content[:insert_pos] + tags_html + html_content[insert_pos:]
    
    return html_content


# Example usage showing the difference
if __name__ == '__main__':
    print("Testing Safe Template Renderer:\n")
    
    # Test data with potential XSS
    context = {
        'title': '<script>alert("XSS")</script>Normal Title',
        'url': 'javascript:alert("XSS")',
        'description': 'This has <b>HTML</b> tags & entities',
    }
    
    # UNSAFE: Using Template() directly without autoescape
    print("❌ UNSAFE (no autoescape):")
    from jinja2 import Template
    unsafe_template = Template('<h1>{{ title }}</h1><a href="{{ url }}">Link</a>')
    unsafe_result = unsafe_template.render(**context)
    print(f"  Result: {unsafe_result}")
    print(f"  ⚠️  Script tag NOT escaped, XSS possible!\n")
    
    # SAFE: Using SafeTemplateRenderer with autoescape
    print("✅ SAFE (with autoescape):")
    renderer = SafeTemplateRenderer()
    safe_result = renderer.render_string(
        '<h1>{{ title }}</h1><a href="{{ url | safe_url }}">Link</a>',
        context
    )
    print(f"  Result: {safe_result}")
    print(f"  ✓ Script tag escaped, safe to render!\n")
    
    # Test CSP generation
    print("Content Security Policy:")
    csp = ContentSecurityPolicy()
    print(f"  {csp.generate_policy()}\n")
    
    # Test security headers
    print("Security Headers:")
    headers = csp.get_security_headers()
    for header, value in headers.items():
        print(f"  {header}: {value}")
