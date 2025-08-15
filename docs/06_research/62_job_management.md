# Job Management in m1f-research

m1f-research uses a SQLite-based job management system that tracks all research
tasks, enabling persistence, resume functionality, and advanced filtering.

## Overview

Every research task creates a **job** with:

- Unique job ID
- SQLite databases for tracking
- Hierarchical directory structure
- Full resume capability
- Advanced search and filtering

## Job Structure

### Directory Layout

```
research-data/
├── research_jobs.db          # Main job tracking database
├── latest_research.md        # Symlink to most recent bundle
└── 2025/
    └── 07/
        └── 23/
            └── abc123_query-name/
                ├── research.db           # Job-specific database
                ├── RESEARCH_BUNDLE.md    # Main research bundle
                ├── EXECUTIVE_SUMMARY.md  # Executive summary
                └── metadata.json         # Job metadata
```

### Database Architecture

**Main Database (`research_jobs.db`)**

- Tracks all jobs across the system
- Stores job metadata and statistics
- Enables cross-job queries and filtering

**Per-Job Database (`research.db`)**

- URL tracking and status
- Content storage (markdown)
- Analysis results
- Filtering decisions

## Job Management Commands

### Listing Jobs

```bash
# List all jobs
m1f-research --list-jobs

# List with pagination
m1f-research --list-jobs --limit 10 --offset 20

# Filter by date
m1f-research --list-jobs --date 2025-07-23  # Specific day
m1f-research --list-jobs --date 2025-07     # Specific month
m1f-research --list-jobs --date 2025        # Specific year

# Search by query term
m1f-research --list-jobs --search "react"
m1f-research --list-jobs --search "tailwind"

# Combine filters
m1f-research --list-jobs --date 2025-07 --search "python" --limit 5
```

### Viewing Job Details

```bash
# Show detailed job status
m1f-research --status abc123
```

Output includes:

- Job ID and query
- Creation/update timestamps
- URL statistics
- Bundle availability
- Output directory

### Resuming Jobs

```bash
# Resume an interrupted job
m1f-research --resume abc123

# Add more URLs to existing job
m1f-research --resume abc123 --urls-file additional-urls.txt
```

## Advanced Filtering

### Pagination

Use `--limit` and `--offset` for large job lists:

```bash
# First page (10 items)
m1f-research --list-jobs --limit 10

# Second page
m1f-research --list-jobs --limit 10 --offset 10

# Third page
m1f-research --list-jobs --limit 10 --offset 20
```

### Date Filtering

Filter jobs by creation date:

```bash
# Jobs from today
m1f-research --list-jobs --date 2025-07-23

# Jobs from this month
m1f-research --list-jobs --date 2025-07

# Jobs from this year
m1f-research --list-jobs --date 2025
```

### Search Filtering

Find jobs by query content:

```bash
# Find all React-related research
m1f-research --list-jobs --search "react"

# Case-insensitive search
m1f-research --list-jobs --search "PYTHON"
```

Search terms are highlighted in the output for easy identification.

## Data Cleanup

### Cleaning Individual Jobs

Remove raw HTML data while preserving analysis:

```bash
# Clean specific job
m1f-research --clean-raw abc123
```

This removes:

- Raw HTML files
- Temporary download data

This preserves:

- Markdown content
- Analysis results
- Research bundles
- Job metadata

### Bulk Cleanup

Clean all jobs at once:

```bash
# Clean all raw data (with confirmation)
m1f-research --clean-all-raw
```

**Warning**: This action cannot be undone. You'll be prompted to confirm.

## Job Deletion

### Deleting Individual Jobs

Completely remove a job including all data:

```bash
# Delete specific job (with confirmation)
m1f-research --delete abc123

# Delete without confirmation prompt
m1f-research --delete abc123 --yes
```

When deleting a job, the system will:

1. Show job details (query, status, creation date, output path)
2. Request confirmation (unless `--yes` is used)
3. Remove the job from the database
4. Delete the entire job directory and all its contents
5. Report success or any errors encountered

**What gets deleted:**

- Database entry in `research_jobs.db`
- Job statistics in the database
- Entire job directory including:
  - Job-specific database (`research.db`)
  - Research bundle (`RESEARCH_BUNDLE.md`)
  - Executive summary (`EXECUTIVE_SUMMARY.md`)
  - All scraped content and analysis
  - Any metadata files

### Bulk Job Deletion

Delete multiple jobs based on filters:

```bash
# Delete all failed jobs
m1f-research --delete-bulk --status-filter failed

# Delete jobs from a specific month
m1f-research --delete-bulk --date 2025-01

# Delete jobs matching a search term
m1f-research --delete-bulk --search "test"

# Combine filters
m1f-research --delete-bulk --status-filter failed --date 2025-01

# Skip confirmation (use with caution!)
m1f-research --delete-bulk --status-filter failed --yes
```

**Bulk deletion process:**

1. Lists all jobs matching the filters
2. Shows a preview of jobs to be deleted (first 10)
3. Requests confirmation with total count
4. Deletes each job with progress tracking
5. Reports success/failure statistics

### Safety Features

#### Confirmation Prompts

By default, all deletion operations require confirmation:

```
Job to delete: abc123
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query: python async best practices
Status: completed
Created: 2025-07-23 14:30:22
Output: research-data/2025/07/23/abc123_python-async-best-practices

⚠️  Delete job abc123 and all its data? [y/N]:
```

#### Error Handling

The deletion system handles errors gracefully:

- **Partial failures**: If filesystem deletion fails but database deletion succeeds, both are reported
- **Permission errors**: Attempts recovery with fallback methods
- **Missing jobs**: Clear error messages for non-existent job IDs
- **Failed deletions**: Detailed error reporting for troubleshooting

### Deletion vs Cleanup

| Operation | Database Entry | Job Directory | Research Bundle | Raw HTML | Recovery |
|-----------|---------------|---------------|-----------------|----------|----------|
| Clean Raw | ✓ Kept | ✓ Kept | ✓ Kept | ✗ Deleted | Can resume |
| Delete Job | ✗ Deleted | ✗ Deleted | ✗ Deleted | ✗ Deleted | Not recoverable |

**When to use cleanup:**
- Free disk space while keeping research results
- Job is complete but you want to keep the analysis
- Temporary space management

**When to use deletion:**
- Remove failed or test jobs
- Clean up old research no longer needed
- Complete removal of sensitive or outdated data
- Permanent space recovery

## Job Status

Jobs can have the following statuses:

| Status      | Description               |
| ----------- | ------------------------- |
| `active`    | Job is currently running  |
| `completed` | Job finished successfully |
| `failed`    | Job encountered errors    |

## Manual URL Management

Add URLs from a file:

```bash
# Create URL file
cat > my-urls.txt << EOF
https://example.com/article1
https://example.com/article2
EOF

# Start new job with URLs
m1f-research "my topic" --urls-file my-urls.txt

# Add to existing job
m1f-research --resume abc123 --urls-file more-urls.txt
```

## Smart Delay Management

The scraper implements intelligent per-host delays:

- **No delay** for first 3 requests to any host
- **1-3 second random delay** after 3 requests
- **Parallel scraping** across different hosts

This ensures:

- Fast scraping for diverse sources
- Respectful behavior for repeated requests
- Optimal performance

## Examples

### Research Workflow

```bash
# 1. Start research
m1f-research "python async best practices"
# Output: Job ID: abc123

# 2. Check progress
m1f-research --status abc123

# 3. Add more URLs if needed
m1f-research --resume abc123 --urls-file extra-urls.txt

# 4. View all Python research
m1f-research --list-jobs --search "python"

# 5. Clean up old data
m1f-research --clean-raw abc123

# 6. Delete old or failed jobs
m1f-research --delete old-job-id
```

### Monthly Research Review

```bash
# List all research from July 2025
m1f-research --list-jobs --date 2025-07

# Page through results
m1f-research --list-jobs --date 2025-07 --limit 20
m1f-research --list-jobs --date 2025-07 --limit 20 --offset 20

# Find specific topic
m1f-research --list-jobs --date 2025-07 --search "react hooks"
```

### Disk Space Management

```bash
# Check job sizes (future feature)
# m1f-research --list-jobs --show-size

# Clean raw data from specific job
m1f-research --clean-raw old-job-id

# Bulk cleanup of raw data
m1f-research --clean-all-raw

# Delete specific job completely
m1f-research --delete old-job-id

# Delete all failed jobs
m1f-research --delete-bulk --status-filter failed

# Delete old jobs from previous month
m1f-research --delete-bulk --date 2025-06
```

### Job Maintenance Workflow

```bash
# 1. List all jobs to review
m1f-research --list-jobs

# 2. Check failed jobs
m1f-research --list-jobs --status-filter failed

# 3. Delete all failed jobs after review
m1f-research --delete-bulk --status-filter failed

# 4. Clean raw data from completed jobs
m1f-research --clean-all-raw

# 5. Delete old test jobs
m1f-research --delete-bulk --search "test" --yes
```

## Tips

1. **Use job IDs**: Save job IDs for easy resume/reference
2. **Regular cleanup**: Clean raw data after analysis is complete
3. **Combine filters**: Use multiple filters for precise searches
4. **Manual URLs**: Supplement LLM search with your own URLs
5. **Check status**: Monitor long-running jobs with --status
6. **Review before deletion**: Always check job details before deleting
7. **Use --yes carefully**: Only use automatic confirmation in scripts you trust
8. **Delete failed jobs**: Regularly remove failed jobs to keep workspace clean
9. **Backup important research**: Export important jobs before deletion

## Future Enhancements

- Export job lists to CSV/JSON
- Job size statistics
- Automatic cleanup policies
- Job tagging system
- Cross-job deduplication
- Job templates
- Scheduled deletion policies
- Job archiving before deletion
- Undo/recovery for recently deleted jobs
