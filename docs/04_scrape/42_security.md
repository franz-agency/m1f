# m1f-scrape Security Documentation

## Overview

m1f-scrape implements multiple layers of security to protect against common web scraping vulnerabilities and ensure safe operation. This document covers all security features, potential risks, and best practices.

## Security Features

### 1. SSRF (Server-Side Request Forgery) Protection ✅

**Implementation**: Blocks requests to private IP addresses and cloud metadata endpoints.

**Location**: `tools/scrape_tool/scrapers/base.py:133-179`

**Protected Against**:
- Private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Localhost (127.0.0.0/8, ::1)
- Link-local addresses (169.254.0.0/16)
- Cloud metadata endpoints (169.254.169.254)
- Multicast addresses

**Configuration**: 
```yaml
check_ssrf: true  # Enable/disable SSRF protection (default: true)
```

**CLI**: `--disable-ssrf-check` to disable (use with caution)

### 2. Path Traversal Protection ✅

**Implementation**: Aggressive sanitization of file paths and names.

**Location**: `tools/scrape_tool/crawlers.py:1085-1162`

**Security Measures**:
- Removes `..` and `./` patterns from paths
- Sanitizes filenames to alphanumeric + `._-` characters
- Validates resolved paths stay within output directory
- Blocks dangerous file extensions (.exe, .dll, .bat, .cmd, .sh, etc.)

**Example Protection**:
```python
# Dangerous paths are blocked:
../../../etc/passwd  → Blocked
../../sensitive.txt  → Blocked
file/../../../etc    → Blocked

# Safe sanitized output:
my-file_name.jpg     → my-file_name.jpg
dangerous...file     → dangerous_file
.hidden..file        → hidden_file
```

### 3. File Type Validation ✅

**Implementation**: Magic number validation and content type checking.

**Location**: `tools/scrape_tool/file_validator.py`

**Features**:
- Magic number checking for 30+ file types
- Content-Type header validation
- File structure validation (images with Pillow, PDFs with PyPDF2)
- Detection of mismatched file extensions

**Dangerous Content Types Blocked**:
- application/x-executable
- application/x-msdownload
- application/x-msdos-program
- application/x-sh
- application/x-shellscript
- application/x-httpd-php
- application/x-httpd-cgi

### 4. HTML Content Security ⚠️

**Implementation**: HTML validation and malicious pattern detection.

**Location**: `tools/scrape_tool/file_validator.py:260-370`

**Security Checks**:
- Detection of eval() in scripts
- JavaScript URL detection in iframes/objects
- Inline binary detection (data: URLs)
- External resource tracking
- Malicious event handler detection

**Current Limitations**:
- ⚠️ **No HTML Sanitization**: Dangerous content is detected but not removed
- ⚠️ **Scripts Preserved**: JavaScript code remains in scraped content
- ⚠️ **Event Handlers Preserved**: onclick, onload, etc. are not stripped

### 5. Content Deduplication ✅

**Implementation**: SHA-256 based duplicate detection.

**Benefits**:
- Prevents duplicate downloads
- Saves bandwidth and storage
- Database-backed for memory efficiency

### 6. robots.txt Compliance ✅

**Implementation**: Automatic robots.txt checking with caching.

**Features**:
- Respects crawl delays
- Honors disallow rules
- Caches robots.txt per domain

## Security Risks and Mitigations

### High Risk Issues ⚠️

#### 1. XSS (Cross-Site Scripting) Vulnerability
**Risk**: Scraped HTML contains unsanitized JavaScript that could execute if rendered.

**Current State**: Scripts and event handlers are preserved in scraped content.

**Mitigation Needed**:
```python
# Recommended: Add HTML sanitization
from bleach import clean

allowed_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
               'strong', 'em', 'ul', 'ol', 'li', 'a', 'img']
allowed_attributes = {'a': ['href'], 'img': ['src', 'alt']}

sanitized = clean(html_content, tags=allowed_tags, 
                 attributes=allowed_attributes, strip=True)
```

#### 2. Malicious JavaScript Preservation
**Risk**: Downloaded pages may contain malicious scripts that remain active.

**Mitigation Needed**:
```python
# Remove all script tags
for script in soup.find_all("script"):
    script.decompose()

# Remove event handlers
for tag in soup.find_all(True):
    for attr in list(tag.attrs.keys()):
        if attr.startswith('on'):
            del tag[attr]
```

### Medium Risk Issues ⚠️

#### 3. Inline Binary Data
**Risk**: Data URLs can embed malicious content bypassing file type restrictions.

**Current State**: Detected but not removed.

**Mitigation Needed**:
```python
# Remove or validate data URLs
for tag in soup.find_all(True):
    for attr in ['src', 'href', 'data']:
        if tag.get(attr) and tag[attr].startswith('data:'):
            # Validate MIME type or remove
            tag[attr] = ''
```

#### 4. External Resource References
**Risk**: External scripts and resources could be compromised.

**Current State**: Tracked but preserved.

## Configuration for Security

### Recommended Secure Configuration

```yaml
# .m1f-scrape-config.yml
crawler:
  check_ssrf: true           # Block private IPs
  check_canonical: true      # Prevent duplicates
  check_content_duplicates: true
  respect_robots_txt: true   # Always respect robots.txt
  verify_ssl: true          # Verify SSL certificates
  download_assets: false    # Don't download binaries by default
  download_external_assets: false  # Block external CDN assets
  
  # Conservative rate limiting
  request_delay: 5.0
  concurrent_requests: 2
  timeout: 30
  
  # File size limits
  max_asset_size: 10485760  # 10MB max for assets
  
  # Restricted asset types (safer subset)
  asset_types:
    - .jpg
    - .jpeg
    - .png
    - .gif
    - .css
    - .pdf
```

### High-Security Configuration

```yaml
# For maximum security (may break functionality)
crawler:
  check_ssrf: true
  download_assets: false    # No binary downloads
  download_external_assets: false
  allowed_domains:          # Whitelist specific domains
    - example.com
    - docs.example.com
  excluded_paths:           # Block sensitive paths
    - /admin/
    - /api/
    - /private/
  max_pages: 100           # Limit scope
  max_depth: 3             # Shallow crawling only
```

## BeautifulSoup Security Features

### What BeautifulSoup Provides:
- **Safe HTML Parsing**: Handles malformed HTML without code execution
- **Entity Decoding**: Properly decodes HTML entities
- **No Code Execution**: Parser doesn't execute JavaScript

### What BeautifulSoup Does NOT Provide:
- **No Sanitization**: All dangerous content is preserved
- **No Script Filtering**: JavaScript remains intact
- **No URL Validation**: Doesn't validate href/src attributes
- **No Event Handler Removal**: onclick, onload preserved
- **No Security Features**: It's a parser, not a security tool

## Security Best Practices

### 1. Always Validate Output
```bash
# Check for suspicious patterns in downloaded content
grep -r "eval(" ./downloaded_html/
grep -r "javascript:" ./downloaded_html/
grep -r "onclick=" ./downloaded_html/
```

### 2. Use Sandboxed Environments
- Run m1f-scrape in Docker containers
- Use virtual machines for untrusted sites
- Limit file system permissions

### 3. Post-Process for Safety
```python
# Example post-processing script
from pathlib import Path
from bs4 import BeautifulSoup

for html_file in Path("./downloaded_html").glob("**/*.html"):
    soup = BeautifulSoup(html_file.read_text(), 'html.parser')
    
    # Remove dangerous elements
    for script in soup.find_all("script"):
        script.decompose()
    
    for tag in soup.find_all(True):
        # Remove event handlers
        for attr in list(tag.attrs.keys()):
            if attr.startswith('on'):
                del tag[attr]
        
        # Remove javascript: URLs
        if tag.get('href') and 'javascript:' in tag['href']:
            tag['href'] = '#'
    
    html_file.write_text(str(soup))
```

### 4. Monitor and Audit
- Review logs for blocked requests
- Check for SSRF attempts
- Monitor file sizes and counts
- Audit downloaded content regularly

## Malware and Virus Scanning

### Post-Download Scanning

After downloading content with m1f-scrape, it's recommended to scan the files for malware and viruses, especially when scraping untrusted sites.

### 1. ClamAV (Open Source, Cross-Platform)

**Installation**:
```bash
# Ubuntu/Debian
sudo apt-get install clamav clamav-daemon
sudo freshclam  # Update virus definitions

# macOS
brew install clamav
freshclam

# Windows
# Download from https://www.clamav.net/downloads
```

**Scanning Downloaded Content**:
```bash
# Update virus definitions first
sudo freshclam

# Scan entire download directory
clamscan -r ./downloaded_html/

# Scan with automatic removal of infected files
clamscan -r --remove ./downloaded_html/

# Scan with detailed output and log
clamscan -r -v --log=/tmp/scan.log ./downloaded_html/

# Move infected files to quarantine
clamscan -r --move=/tmp/quarantine ./downloaded_html/
```

### 2. VirusTotal Integration (API-Based)

**Using vt-py (Python)**:
```python
# Install: pip install vt-py

import vt
import hashlib
from pathlib import Path

client = vt.Client("YOUR_API_KEY")

def scan_file(file_path):
    # Calculate file hash
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    # Check if file is already known
    try:
        file_report = client.get_object(f"/files/{file_hash}")
        stats = file_report.last_analysis_stats
        if stats["malicious"] > 0:
            print(f"⚠️ MALICIOUS: {file_path}")
            print(f"   Detections: {stats['malicious']}/{sum(stats.values())}")
        else:
            print(f"✅ Clean: {file_path}")
    except:
        # File not in database, upload for scanning
        with open(file_path, "rb") as f:
            analysis = client.scan_file(f)
        print(f"📤 Uploaded for analysis: {file_path}")
        print(f"   Check: https://www.virustotal.com/gui/file/{file_hash}")

# Scan all downloaded files
for file in Path("./downloaded_html").rglob("*"):
    if file.is_file():
        scan_file(file)

client.close()
```

### 3. YARA Rules (Pattern-Based Detection)

**Installation**:
```bash
# Ubuntu/Debian
sudo apt-get install yara

# macOS
brew install yara

# Python integration
pip install yara-python
```

**Create Custom Rules** (`web_threats.yar`):
```yara
rule Suspicious_JavaScript_Eval
{
    strings:
        $eval1 = "eval(" nocase
        $eval2 = "eval (" nocase
        $eval3 = ".eval(" nocase
        $obfuscated = /eval\s*\(\s*unescape/
        
    condition:
        any of them
}

rule Crypto_Miner_Scripts
{
    strings:
        $coinhive = "coinhive" nocase
        $cryptoloot = "cryptoloot" nocase
        $webminer = "webminer" nocase
        $miner1 = "CryptoNoter"
        $miner2 = "JSMiner"
        
    condition:
        any of them
}

rule Phishing_Patterns
{
    strings:
        $phish1 = "verify your account" nocase
        $phish2 = "suspended account" nocase
        $phish3 = "click here immediately" nocase
        $form = /<form[^>]+action\s*=\s*["'][^"']+phishing/
        
    condition:
        2 of them
}

rule Malicious_Iframe
{
    strings:
        $iframe1 = /<iframe[^>]+style\s*=\s*["']display\s*:\s*none/
        $iframe2 = /<iframe[^>]+width\s*=\s*["']0/
        $iframe3 = /<iframe[^>]+height\s*=\s*["']0/
        $suspicious_src = /<iframe[^>]+src\s*=\s*["']https?:\/\/[0-9]{1,3}\.[0-9]{1,3}/
        
    condition:
        any of them
}
```

**Scan with YARA**:
```bash
# Scan with rules file
yara web_threats.yar -r ./downloaded_html/

# Python script for detailed scanning
```

```python
import yara
from pathlib import Path

# Compile rules
rules = yara.compile(filepath='web_threats.yar')

# Scan files
for file_path in Path("./downloaded_html").rglob("*.html"):
    matches = rules.match(str(file_path))
    if matches:
        print(f"⚠️ Threats detected in {file_path}:")
        for match in matches:
            print(f"   - {match.rule}: {match.strings}")
```

### 4. Automated Scanning Pipeline

**Create a Post-Download Scanner** (`scan_downloads.sh`):
```bash
#!/bin/bash

DOWNLOAD_DIR="$1"
QUARANTINE_DIR="/tmp/quarantine"
LOG_FILE="/tmp/scan_$(date +%Y%m%d_%H%M%S).log"

echo "🔍 Starting security scan of $DOWNLOAD_DIR" | tee -a "$LOG_FILE"

# 1. ClamAV Scan
echo "Running ClamAV scan..." | tee -a "$LOG_FILE"
clamscan -r --move="$QUARANTINE_DIR/clamav" "$DOWNLOAD_DIR" >> "$LOG_FILE" 2>&1

# 2. YARA Scan
echo "Running YARA scan..." | tee -a "$LOG_FILE"
yara web_threats.yar -r "$DOWNLOAD_DIR" >> "$LOG_FILE" 2>&1

# 3. Check for suspicious patterns
echo "Checking for suspicious patterns..." | tee -a "$LOG_FILE"
grep -r "eval(" "$DOWNLOAD_DIR" >> "$LOG_FILE" 2>&1
grep -r "document.write" "$DOWNLOAD_DIR" >> "$LOG_FILE" 2>&1
grep -r "unescape(" "$DOWNLOAD_DIR" >> "$LOG_FILE" 2>&1

# 4. File type validation
echo "Validating file types..." | tee -a "$LOG_FILE"
find "$DOWNLOAD_DIR" -type f -exec file {} \; | grep -v "HTML\|text" >> "$LOG_FILE" 2>&1

echo "✅ Scan complete. Results saved to $LOG_FILE"

# Check if quarantine has files
if [ -d "$QUARANTINE_DIR" ] && [ "$(ls -A $QUARANTINE_DIR)" ]; then
    echo "⚠️ WARNING: Suspicious files quarantined in $QUARANTINE_DIR"
    exit 1
fi
```

### 5. Integration with m1f-scrape

**Automated Post-Download Scanning**:
```bash
# Create wrapper script
cat > scrape_and_scan.sh << 'EOF'
#!/bin/bash

# Run m1f-scrape
m1f-scrape "$@"

# Get output directory from arguments
OUTPUT_DIR=""
for i in "$@"; do
    if [[ "$prev" == "-o" ]]; then
        OUTPUT_DIR="$i"
        break
    fi
    prev="$i"
done

if [[ -n "$OUTPUT_DIR" ]]; then
    echo "🔍 Scanning downloaded content..."
    
    # Run ClamAV
    clamscan -r "$OUTPUT_DIR"
    
    # Run custom checks
    python3 check_security.py "$OUTPUT_DIR"
    
    echo "✅ Security scan complete"
fi
EOF

chmod +x scrape_and_scan.sh
```

### 6. Docker-Based Scanning (Isolated Environment)

**Dockerfile for Secure Scanning**:
```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    clamav \
    clamav-daemon \
    yara \
    python3 \
    python3-pip

RUN pip3 install vt-py yara-python

# Update ClamAV database
RUN freshclam

WORKDIR /scan

COPY scan_downloads.sh /usr/local/bin/
COPY web_threats.yar /etc/yara/

ENTRYPOINT ["scan_downloads.sh"]
```

**Usage**:
```bash
# Build scanner image
docker build -t web-scanner .

# Scan downloaded content in isolated container
docker run --rm -v $(pwd)/downloaded_html:/scan:ro web-scanner
```

### 7. Commercial Solutions

For enterprise environments, consider:

1. **Sophos CLI Scanner**
   ```bash
   savscan -all -archive -mime ./downloaded_html/
   ```

2. **ESET Command Line Scanner**
   ```bash
   /opt/eset/esets/sbin/esets_scan --clean-mode=delete ./downloaded_html/
   ```

3. **Kaspersky Endpoint Security**
   ```bash
   kavshell scan ./downloaded_html/ --action=disinfect
   ```

### Best Practices for Malware Scanning

1. **Always Update Definitions**
   ```bash
   # Before each scan
   sudo freshclam  # ClamAV
   yara-rules-update  # YARA
   ```

2. **Scan Immediately After Download**
   - Integrate scanning into your download workflow
   - Quarantine suspicious files before processing

3. **Use Multiple Scanners**
   - Different engines detect different threats
   - Combine signature-based and heuristic detection

4. **Monitor System Resources**
   ```bash
   # Watch for unusual activity during/after downloads
   htop
   netstat -tulpn
   ```

5. **Regular Scheduled Scans**
   ```cron
   # Add to crontab
   0 2 * * * /usr/local/bin/scan_downloads.sh /var/www/scraped/
   ```

### Security Checklist

Before scraping untrusted sites:

- [ ] Enable all security checks (SSRF, SSL verification)
- [ ] Set reasonable limits (max_pages, max_depth, timeouts)
- [ ] Configure allowed_domains if possible
- [ ] Disable asset downloads unless needed
- [ ] Use a sandboxed environment
- [ ] Plan post-processing sanitization
- [ ] Review robots.txt compliance
- [ ] Test with small page limits first
- [ ] Monitor resource usage
- [ ] Have incident response plan

## Reporting Security Issues

If you discover a security vulnerability in m1f-scrape:

1. **Do NOT** create a public GitHub issue
2. Contact the maintainers privately
3. Provide detailed reproduction steps
4. Allow time for a fix before disclosure

## Future Security Enhancements

Planned improvements:

1. **Built-in HTML Sanitization**
   - Integration with bleach library
   - Configurable sanitization levels
   - Preserve structure while removing dangerous content

2. **Content Security Policy Analysis**
   - Extract and analyze CSP headers
   - Warn about weak policies
   - Generate CSP recommendations

3. **Enhanced Binary Validation**
   - Deeper file format validation
   - Virus scanning integration
   - Sandboxed preview generation

4. **Security Scoring**
   - Rate scraped content for risk level
   - Provide security reports
   - Automated remediation options

## Conclusion

m1f-scrape provides robust security features for safe web scraping, but scraped content should always be treated as potentially dangerous. The tool detects but doesn't sanitize malicious content by default. Always post-process scraped content before use in production environments, especially if it will be rendered in browsers or processed by other systems.

For maximum security, combine m1f-scrape's built-in protections with post-processing sanitization and sandboxed environments.
