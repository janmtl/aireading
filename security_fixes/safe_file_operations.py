#!/usr/bin/env python3
"""
Safe file operations to prevent path traversal attacks.
Addresses VULN-003 from security audit.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
import json
from datetime import datetime


class SafeFileHandler:
    """Handle file operations with security checks."""
    
    def __init__(self, base_directory: str):
        """
        Initialize handler with base directory.
        
        Args:
            base_directory: The root directory for all operations
        """
        self.base_dir = Path(base_directory).resolve()
        
        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions on base directory (owner only)
        os.chmod(self.base_dir, 0o700)
    
    def safe_path(self, relative_path: str) -> Path:
        """
        Resolve a path safely within the base directory.
        
        Args:
            relative_path: User-provided relative path
            
        Returns:
            Resolved Path object
            
        Raises:
            ValueError: If path escapes base directory
        """
        # Remove null bytes
        if '\x00' in relative_path:
            raise ValueError("Path contains null bytes")
        
        # Construct target path
        target = (self.base_dir / relative_path).resolve()
        
        # Check if target is within base directory
        try:
            target.relative_to(self.base_dir)
        except ValueError:
            raise ValueError(
                f"Path traversal detected: {relative_path} "
                f"resolves outside base directory"
            )
        
        return target
    
    def safe_write(self, relative_path: str, content: str, 
                   mode: str = 'w', permissions: int = 0o600) -> Path:
        """
        Safely write content to a file.
        
        Args:
            relative_path: Relative path within base directory
            content: Content to write
            mode: File open mode
            permissions: Unix file permissions (default: owner read/write only)
            
        Returns:
            Path to written file
            
        Raises:
            ValueError: If path is invalid
        """
        target_path = self.safe_path(relative_path)
        
        # Create parent directories if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write with secure permissions
        old_umask = os.umask(0o077)  # Temporarily restrict permissions
        try:
            with open(target_path, mode) as f:
                f.write(content)
            
            # Set explicit permissions
            os.chmod(target_path, permissions)
        finally:
            os.umask(old_umask)
        
        return target_path
    
    def safe_read(self, relative_path: str, mode: str = 'r', 
                  max_size: Optional[int] = None) -> str:
        """
        Safely read content from a file.
        
        Args:
            relative_path: Relative path within base directory
            mode: File open mode
            max_size: Maximum file size to read (bytes)
            
        Returns:
            File content
            
        Raises:
            ValueError: If path is invalid or file too large
        """
        target_path = self.safe_path(relative_path)
        
        # Check file exists
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        # Check file size if limit specified
        if max_size is not None:
            file_size = target_path.stat().st_size
            if file_size > max_size:
                raise ValueError(
                    f"File too large: {file_size} bytes "
                    f"(max: {max_size} bytes)"
                )
        
        with open(target_path, mode) as f:
            return f.read()
    
    def safe_delete(self, relative_path: str) -> bool:
        """
        Safely delete a file.
        
        Args:
            relative_path: Relative path within base directory
            
        Returns:
            True if file was deleted, False if it didn't exist
            
        Raises:
            ValueError: If path is invalid
        """
        target_path = self.safe_path(relative_path)
        
        if target_path.exists():
            target_path.unlink()
            return True
        return False
    
    def list_files(self, relative_path: str = "", 
                  pattern: str = "*") -> list[Path]:
        """
        List files in a directory.
        
        Args:
            relative_path: Relative directory path
            pattern: Glob pattern for filtering
            
        Returns:
            List of Path objects
        """
        dir_path = self.safe_path(relative_path)
        
        if not dir_path.is_dir():
            return []
        
        return list(dir_path.glob(pattern))


class DebugFileHandler:
    """Handle debug files securely in temp directory."""
    
    def __init__(self, app_name: str = "ai-digest"):
        """
        Initialize debug handler.
        
        Args:
            app_name: Application name for temp directory
        """
        self.debug_dir = Path(tempfile.gettempdir()) / f"{app_name}-debug"
        self.debug_dir.mkdir(exist_ok=True, mode=0o700)
        
        # Keep track of created files
        self._created_files: list[Path] = []
    
    def write_debug_file(self, content: str, prefix: str = "debug") -> Path:
        """
        Write a debug file with timestamp.
        
        Args:
            content: Debug content
            prefix: Filename prefix
            
        Returns:
            Path to debug file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{prefix}_{timestamp}.txt"
        filepath = self.debug_dir / filename
        
        # Write with restrictive permissions
        with open(filepath, 'w') as f:
            f.write(content)
        
        os.chmod(filepath, 0o600)
        self._created_files.append(filepath)
        
        return filepath
    
    def cleanup_old_files(self, max_age_seconds: int = 86400, 
                          max_files: int = 100) -> int:
        """
        Clean up old debug files.
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 24 hours)
            max_files: Maximum number of files to keep
            
        Returns:
            Number of files deleted
        """
        now = datetime.now().timestamp()
        deleted = 0
        
        files = sorted(
            self.debug_dir.glob("*.txt"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        for idx, filepath in enumerate(files):
            file_age = now - filepath.stat().st_mtime
            
            # Delete if too old or beyond max count
            if file_age > max_age_seconds or idx >= max_files:
                try:
                    filepath.unlink()
                    deleted += 1
                except Exception:
                    pass
        
        return deleted
    
    def cleanup_all(self) -> int:
        """
        Delete all debug files.
        
        Returns:
            Number of files deleted
        """
        deleted = 0
        for filepath in self.debug_dir.glob("*.txt"):
            try:
                filepath.unlink()
                deleted += 1
            except Exception:
                pass
        return deleted


class SecureJSONHandler:
    """Handle JSON operations securely with validation."""
    
    # JSON Schema for summary validation
    SUMMARY_SCHEMA = {
        "type": "object",
        "required": ["items", "trends", "summary", "generated_at", "model"],
        "properties": {
            "items": {
                "type": "array",
                "maxItems": 1000,
                "items": {
                    "type": "object",
                    "required": ["title", "url", "core_innovation", 
                                "significance", "practical_readiness", 
                                "significance_score", "category"],
                    "properties": {
                        "title": {"type": "string", "maxLength": 1000},
                        "url": {"type": "string", "maxLength": 2048},
                        "core_innovation": {"type": "string", "maxLength": 500},
                        "significance": {"type": "string", "maxLength": 500},
                        "practical_readiness": {
                            "type": "string",
                            "enum": ["research", "prototype", "production-ready"]
                        },
                        "significance_score": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        },
                        "category": {"type": "string", "maxLength": 100}
                    }
                }
            },
            "trends": {
                "type": "array",
                "maxItems": 100,
                "items": {"type": "string", "maxLength": 500}
            },
            "summary": {"type": "string", "maxLength": 5000},
            "generated_at": {"type": "string"},
            "model": {"type": "string", "maxLength": 100},
            "total_items_analyzed": {"type": "number", "minimum": 0}
        }
    }
    
    @staticmethod
    def safe_json_load(filepath: Path, max_size: int = 10 * 1024 * 1024) -> dict:
        """
        Safely load and validate JSON file.
        
        Args:
            filepath: Path to JSON file
            max_size: Maximum file size in bytes (default: 10MB)
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If file is invalid or too large
        """
        # Check file size
        file_size = filepath.stat().st_size
        if file_size > max_size:
            raise ValueError(f"JSON file too large: {file_size} bytes")
        
        # Load JSON
        with open(filepath, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        
        # Basic validation
        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")
        
        return data
    
    @classmethod
    def validate_summary(cls, data: dict) -> tuple[bool, Optional[str]]:
        """
        Validate summary data against schema.
        
        Args:
            data: Summary data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required fields
            for field in cls.SUMMARY_SCHEMA["required"]:
                if field not in data:
                    return False, f"Missing required field: {field}"
            
            # Validate items array
            if not isinstance(data["items"], list):
                return False, "items must be an array"
            
            if len(data["items"]) > 1000:
                return False, "Too many items"
            
            # Validate trends array
            if not isinstance(data["trends"], list):
                return False, "trends must be an array"
            
            # Validate summary
            if not isinstance(data["summary"], str):
                return False, "summary must be a string"
            
            if len(data["summary"]) > 5000:
                return False, "summary too long"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {e}"


# Example usage
if __name__ == '__main__':
    # Test safe file operations
    print("Testing Safe File Operations:\n")
    
    # Create handler for summaries
    handler = SafeFileHandler("./test_summaries")
    
    # Test valid path
    try:
        safe_path = handler.safe_write("2026-07-01.json", '{"test": "data"}')
        print(f"✓ Created file: {safe_path}")
        
        content = handler.safe_read("2026-07-01.json")
        print(f"✓ Read content: {content}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test path traversal attack
    try:
        handler.safe_write("../../../etc/passwd", "malicious")
        print("✗ Path traversal was not blocked!")
    except ValueError as e:
        print(f"✓ Blocked path traversal: {e}")
    
    # Test debug handler
    print("\nTesting Debug Handler:\n")
    debug_handler = DebugFileHandler("test-app")
    
    debug_file = debug_handler.write_debug_file("Debug content", "test")
    print(f"✓ Created debug file: {debug_file}")
    
    deleted = debug_handler.cleanup_all()
    print(f"✓ Cleaned up {deleted} debug files")
