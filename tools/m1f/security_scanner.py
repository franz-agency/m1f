"""
Security scanner module for detecting sensitive information in files.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import List, Tuple, Dict

from .config import Config
from .logging import LoggerManager

# Try to import detect_secrets
try:
    from detect_secrets.core.scan import scan_file
    from detect_secrets.settings import get_settings, default_settings
    import detect_secrets.plugins

    DETECT_SECRETS_AVAILABLE = True
except Exception:
    DETECT_SECRETS_AVAILABLE = False


class SecurityScanner:
    """Handles security scanning for sensitive information."""

    # Regex patterns for fallback detection
    SENSITIVE_PATTERNS = [
        re.compile(r'password\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(r'passwd\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(r'pwd\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(r'secret[_-]?key\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(r'api[_-]?key\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(r'apikey\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(r'token\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(r'auth[_-]?token\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(r'access[_-]?token\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(r'private[_-]?key\s*[=:]\s*["\']?[\w\-\.]+["\']?', re.IGNORECASE),
        re.compile(
            r'aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*["\']?[\w\-\.]+["\']?',
            re.IGNORECASE,
        ),
        re.compile(
            r'aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["\']?[\w\-\.]+["\']?',
            re.IGNORECASE,
        ),
    ]

    def __init__(self, config: Config, logger_manager: LoggerManager):
        self.config = config
        self.logger = logger_manager.get_logger(__name__)
        self.preset_manager = None  # Will be set by core.py if available

        if DETECT_SECRETS_AVAILABLE:
            self.logger.info("Security scanning will use 'detect-secrets' library")
            # Initialize detect-secrets
            try:
                get_settings()
            except Exception as e:
                self.logger.warning(f"Failed to initialize detect-secrets: {e}")
        else:
            self.logger.info(
                "'detect-secrets' not available. Using regex-based scanning"
            )

    async def scan_files(
        self, files_to_process: List[Tuple[Path, str]]
    ) -> List[Dict[str, any]]:
        """Scan files for sensitive information."""
        if not self.config.security.security_check:
            return []

        self.logger.info("Starting security scan...")

        findings = []

        for file_path, rel_path in files_to_process:
            file_findings = await self._scan_single_file(file_path, rel_path)
            findings.extend(file_findings)

        if findings:
            self.logger.warning(f"Security scan found {len(findings)} potential issues")
        else:
            self.logger.info("Security scan completed. No issues found")

        return findings

    async def _scan_single_file(
        self, file_path: Path, rel_path: str
    ) -> List[Dict[str, any]]:
        """Scan a single file for sensitive information."""
        findings = []

        # Check if file has specific security_check override
        if self.preset_manager:
            file_settings = self.preset_manager.get_file_specific_settings(file_path)
            if file_settings and "security_check" in file_settings:
                security_check = file_settings["security_check"]
                if security_check is None or security_check == "null":
                    # Security check disabled for this file type
                    self.logger.debug(
                        f"Security check disabled for {file_path} by preset"
                    )
                    return []
                # Note: We could also handle file-specific abort/skip/warn here if needed

        if DETECT_SECRETS_AVAILABLE:
            # Use detect-secrets
            try:
                with default_settings():
                    secrets_collection = scan_file(str(file_path))

                    for secret in secrets_collection:
                        findings.append(
                            {
                                "path": rel_path,
                                "type": secret.type,
                                "line": secret.line_number,
                                "message": f"Detected '{secret.type}' on line {secret.line_number}",
                            }
                        )

            except Exception as e:
                self.logger.warning(f"detect-secrets failed on {file_path}: {e}")
                # Fall back to regex scanning
                findings.extend(await self._regex_scan_file(file_path, rel_path))
        else:
            # Use regex-based scanning
            findings.extend(await self._regex_scan_file(file_path, rel_path))

        return findings

    async def _regex_scan_file(
        self, file_path: Path, rel_path: str
    ) -> List[Dict[str, any]]:
        """Scan a file using regex patterns."""
        findings = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern in self.SENSITIVE_PATTERNS:
                    if pattern.search(line):
                        # Try to determine the type of secret
                        secret_type = self._determine_secret_type(line)

                        findings.append(
                            {
                                "path": rel_path,
                                "type": secret_type,
                                "line": line_num,
                                "message": f"Potential {secret_type} detected on line {line_num}",
                            }
                        )
                        break  # Only report once per line

        except Exception as e:
            self.logger.warning(f"Could not scan {file_path} for security: {e}")

        return findings

    def _determine_secret_type(self, line: str) -> str:
        """Determine the type of secret based on the line content."""
        line_lower = line.lower()

        if any(word in line_lower for word in ["password", "passwd", "pwd"]):
            return "Password"
        elif "api" in line_lower and "key" in line_lower:
            return "API Key"
        elif "secret" in line_lower and "key" in line_lower:
            return "Secret Key"
        elif "token" in line_lower:
            return "Auth Token"
        elif "private" in line_lower and "key" in line_lower:
            return "Private Key"
        elif "aws" in line_lower:
            return "AWS Credential"
        else:
            return "Secret"
