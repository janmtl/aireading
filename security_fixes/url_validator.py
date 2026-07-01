#!/usr/bin/env python3
"""
URL validation and SSRF protection module.
Addresses VULN-001 from security audit.
"""

import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse
import re


class URLValidator:
    """Validates URLs to prevent SSRF attacks."""
    
    # Allowlist of trusted domains
    ALLOWED_DOMAINS = [
        'huggingface.co',
        'blog.vllm.ai',
        'modal.com',
        'fireworks.ai',
        'sebastianraschka.com',
        'substack.com',
        'jack-clark.net',
        'arxiv.org',
        'export.arxiv.org'
    ]
    
    # Blocked ports
    BLOCKED_PORTS = {
        22,    # SSH
        23,    # Telnet
        25,    # SMTP
        135,   # Windows RPC
        139,   # NetBIOS
        445,   # SMB
        3306,  # MySQL
        3389,  # RDP
        5432,  # PostgreSQL
        6379,  # Redis
        27017, # MongoDB
    }
    
    # Private IP ranges to block (RFC 1918, RFC 4193, etc.)
    PRIVATE_RANGES = [
        '0.0.0.0/8',        # "This" Network
        '10.0.0.0/8',       # Private-Use
        '100.64.0.0/10',    # Shared Address Space
        '127.0.0.0/8',      # Loopback
        '169.254.0.0/16',   # Link Local (AWS metadata!)
        '172.16.0.0/12',    # Private-Use
        '192.0.0.0/24',     # IETF Protocol Assignments
        '192.0.2.0/24',     # Documentation (TEST-NET-1)
        '192.168.0.0/16',   # Private-Use
        '198.18.0.0/15',    # Benchmarking
        '198.51.100.0/24',  # Documentation (TEST-NET-2)
        '203.0.113.0/24',   # Documentation (TEST-NET-3)
        '224.0.0.0/4',      # Multicast
        '240.0.0.0/4',      # Reserved
        '255.255.255.255/32', # Broadcast
        # IPv6
        '::1/128',          # Loopback
        'fc00::/7',         # Unique Local
        'fe80::/10',        # Link Local
    ]
    
    def __init__(self, allowed_domains: Optional[list] = None, 
                 enable_dns_check: bool = True):
        """
        Initialize validator.
        
        Args:
            allowed_domains: Optional list of allowed domains (overrides default)
            enable_dns_check: Whether to perform DNS resolution checks
        """
        self.allowed_domains = allowed_domains or self.ALLOWED_DOMAINS
        self.enable_dns_check = enable_dns_check
        self._compile_private_ranges()
    
    def _compile_private_ranges(self):
        """Pre-compile IP networks for faster checking."""
        self.private_networks = [
            ipaddress.ip_network(net) for net in self.PRIVATE_RANGES
        ]
    
    def is_safe_url(self, url: str, timeout: float = 5.0) -> tuple[bool, Optional[str]]:
        """
        Check if a URL is safe to fetch.
        
        Args:
            url: The URL to validate
            timeout: DNS resolution timeout
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "Invalid URL format"
        
        # Length check
        if len(url) > 2048:
            return False, "URL too long"
        
        try:
            parsed = urlparse(url)
            
            # Scheme validation
            if parsed.scheme not in ['http', 'https']:
                return False, f"Invalid scheme: {parsed.scheme}"
            
            # Hostname validation
            if not parsed.hostname:
                return False, "Missing hostname"
            
            # Domain allowlist check
            hostname_lower = parsed.hostname.lower()
            if not any(allowed in hostname_lower for allowed in self.allowed_domains):
                return False, f"Domain not in allowlist: {parsed.hostname}"
            
            # Port validation
            port = parsed.port
            if port and port in self.BLOCKED_PORTS:
                return False, f"Blocked port: {port}"
            
            # DNS resolution and IP checks
            if self.enable_dns_check:
                try:
                    # Set socket timeout
                    old_timeout = socket.getdefaulttimeout()
                    socket.setdefaulttimeout(timeout)
                    
                    # Resolve hostname
                    ip_addresses = socket.getaddrinfo(
                        parsed.hostname, 
                        parsed.port or (443 if parsed.scheme == 'https' else 80),
                        socket.AF_UNSPEC,
                        socket.SOCK_STREAM
                    )
                    
                    # Check each resolved IP
                    for addr_info in ip_addresses:
                        ip_str = addr_info[4][0]
                        
                        # Parse IP address
                        try:
                            ip_obj = ipaddress.ip_address(ip_str)
                        except ValueError:
                            continue
                        
                        # Check if IP is private/special
                        if ip_obj.is_private:
                            return False, f"Private IP address: {ip_str}"
                        
                        if ip_obj.is_loopback:
                            return False, f"Loopback address: {ip_str}"
                        
                        if ip_obj.is_link_local:
                            return False, f"Link-local address: {ip_str}"
                        
                        if ip_obj.is_multicast:
                            return False, f"Multicast address: {ip_str}"
                        
                        if ip_obj.is_reserved:
                            return False, f"Reserved address: {ip_str}"
                        
                        # Check against private ranges
                        for network in self.private_networks:
                            if ip_obj in network:
                                return False, f"IP in private range: {ip_str}"
                    
                    # Restore socket timeout
                    socket.setdefaulttimeout(old_timeout)
                    
                except socket.gaierror as e:
                    return False, f"DNS resolution failed: {e}"
                except socket.timeout:
                    return False, "DNS resolution timeout"
                except Exception as e:
                    return False, f"DNS check error: {e}"
            
            return True, None
            
        except Exception as e:
            return False, f"URL validation error: {e}"
    
    def validate_or_raise(self, url: str) -> None:
        """
        Validate URL or raise exception.
        
        Args:
            url: The URL to validate
            
        Raises:
            ValueError: If URL is not safe
        """
        is_safe, error = self.is_safe_url(url)
        if not is_safe:
            raise ValueError(f"Unsafe URL: {error}")


# Example usage
if __name__ == '__main__':
    validator = URLValidator()
    
    # Test cases
    test_urls = [
        # Safe URLs
        ('https://huggingface.co/blog/feed.xml', True),
        ('https://blog.vllm.ai/feed.xml', True),
        ('https://arxiv.org/abs/1234.5678', True),
        
        # Unsafe URLs
        ('http://169.254.169.254/latest/meta-data/', False),  # AWS metadata
        ('http://localhost:8080/', False),  # Localhost
        ('http://10.0.0.1/', False),  # Private IP
        ('http://192.168.1.1/', False),  # Private IP
        ('ftp://example.com/file', False),  # Invalid scheme
        ('http://malicious.com/feed', False),  # Not in allowlist
    ]
    
    print("Testing URL Validator:\n")
    for url, should_pass in test_urls:
        is_safe, error = validator.is_safe_url(url)
        status = "✓" if is_safe == should_pass else "✗"
        print(f"{status} {url}")
        if error:
            print(f"  Error: {error}")
        print()
