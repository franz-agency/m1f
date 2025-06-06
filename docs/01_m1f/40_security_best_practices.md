# Security Best Practices Guide for m1f Toolkit

## Overview

This guide documents security best practices and protective measures implemented in the m1f toolkit v3.2. Following these practices ensures safe operation and prevents common security vulnerabilities.

## Path Validation and Traversal Protection

### Why It Matters
Path traversal attacks can allow malicious actors to access files outside intended directories, potentially exposing sensitive system files or overwriting critical data.

### Best Practices

1. **Always validate resolved paths**:
   ```python
   # Good practice - validate after resolving
   from tools.m1f.utils import validate_safe_path
   
   target_path = Path(user_input).resolve()
   validate_safe_path(target_path, base_path)
   ```

2. **Use the provided validation utilities**:
   - `validate_safe_path()` in `tools/m1f/utils.py` ensures paths stay within allowed boundaries
   - All user-provided paths should be validated before use

3. **Symlink safety**:
   - Symlinks are resolved and validated to prevent escaping directories
   - Target of symlinks must be within the allowed base path

### Common Pitfalls to Avoid
- Never use user input directly in file paths without validation
- Don't trust relative paths without resolving and validating them
- Always validate paths from configuration files and presets

## Web Scraping Security

### SSRF (Server-Side Request Forgery) Protection

The toolkit blocks access to:
- Private IP ranges (10.x.x.x, 172.16.x.x, 192.168.x.x)
- Localhost and loopback addresses (127.0.0.1, ::1)
- Link-local addresses (169.254.x.x)
- Cloud metadata endpoints (169.254.169.254)

### SSL/TLS Validation

1. **Default behavior**: SSL certificates are validated by default
2. **Disabling validation** (use with caution):
   ```bash
   # Only for trusted internal sites or testing
   m1f-scrape --ignore-https-errors https://internal-site.com
   ```
   
   ⚠️ **Warning**: Disabling SSL validation exposes you to man-in-the-middle attacks. Only use for trusted internal resources.

### robots.txt Compliance

All scrapers automatically respect robots.txt files:
- Automatically fetched and parsed for each domain
- Scraping is blocked for disallowed paths
- User-agent specific rules are respected
- This is always enabled - no configuration option to disable

### JavaScript Execution Safety

When using Playwright with custom scripts:
- Scripts are validated for dangerous patterns
- Avoid executing untrusted JavaScript code
- Use built-in actions instead of custom scripts when possible

## Command Injection Prevention

### Safe Command Execution

The toolkit uses proper escaping for all system commands:
```python
# Good - using shlex.quote()
import shlex
command = f"httrack {shlex.quote(url)} -O {shlex.quote(output_dir)}"

# Bad - direct string interpolation
command = f"httrack {url} -O {output_dir}"  # DON'T DO THIS
```

## Preset System Security

### File Size Limits
- Preset files are limited to 10MB to prevent memory exhaustion
- Large preset files are rejected with an error

### Path Validation in Presets
- All paths in preset files are validated
- Paths cannot escape the project directory
- Absolute paths outside the project are blocked

### Custom Processor Validation
- Processor names must be alphanumeric with underscores only
- Special characters that could enable code injection are blocked

## Secure Temporary File Handling

The toolkit uses Python's `tempfile` module for all temporary files:
- Temporary directories are created with restricted permissions
- All temporary files are cleaned up after use
- No sensitive data is left in temporary locations

## Security Scanning for Sensitive Data

### Built-in Secret Detection

m1f includes automatic scanning for:
- API keys and tokens
- Passwords and credentials
- Private keys
- High-entropy strings that might be secrets

### Security Check Modes

1. **Error mode** (default): Stops processing if secrets are found
   ```bash
   m1f -s ./src -o output.txt --security-check error
   ```

2. **Warn mode**: Logs warnings but continues processing
   ```bash
   m1f -s ./src -o output.txt --security-check warn
   ```

3. **Skip mode**: Disables security scanning (not recommended)
   ```bash
   m1f -s ./src -o output.txt --security-check skip
   ```

### Handling False Positives

If legitimate content is flagged as sensitive:
1. Review the warnings carefully
2. Use `--security-check warn` if you're certain the content is safe
3. Consider refactoring code to avoid patterns that trigger detection

## Input Validation Best Practices

### File Type Validation
- Use include/exclude patterns to limit processed file types
- Be explicit about allowed file extensions
- Validate file contents match expected formats

### Size and Resource Limits
- Set appropriate limits for file sizes
- Use `--max-file-size` to prevent processing huge files
- Monitor memory usage for large file sets

### Encoding Safety
- The toolkit automatically detects file encodings
- UTF-8 is preferred for text files by default
- Binary files are handled safely without interpretation

## Deployment Security Recommendations

### Environment Configuration
1. Run with minimal required permissions
2. Use dedicated service accounts when possible
3. Avoid running as root/administrator

### Network Security
1. Use HTTPS for all web scraping when possible
2. Configure firewall rules to limit outbound connections
3. Monitor for unusual network activity

### Logging and Monitoring
1. Enable verbose logging for security-sensitive operations
2. Review logs regularly for suspicious patterns
3. Set up alerts for security check failures

## Reporting Security Issues

If you discover a security vulnerability in m1f:
1. Do NOT open a public issue
2. Email security details to the maintainers
3. Include steps to reproduce the issue
4. Allow time for a fix before public disclosure

## Security Checklist for Users

Before running m1f in production:

- [ ] Validate all input paths and patterns
- [ ] Review security check mode settings
- [ ] Enable SSL validation for web scraping
- [ ] Set appropriate file size limits
- [ ] Use minimal required permissions
- [ ] Review preset files for suspicious content
- [ ] Test security scanning on sample data
- [ ] Configure proper logging and monitoring
- [ ] Keep the toolkit updated to the latest version

## Updates and Security Patches

Stay informed about security updates:
- Check the CHANGELOG for security-related fixes
- Update to new versions promptly
- Review breaking changes that might affect security

Remember: Security is a shared responsibility. While m1f implements many protective measures, proper configuration and usage are essential for maintaining a secure environment.