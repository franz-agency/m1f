# Job Deletion Guide for m1f-research

This guide covers the job deletion functionality in m1f-research, including best practices, safety features, and common workflows.

## Overview

Job deletion provides complete removal of research jobs from both the database and filesystem. Unlike cleanup operations that only remove raw data, deletion permanently removes all traces of a job.

## Why Delete Jobs?

- **Failed Jobs**: Remove jobs that encountered errors and cannot be resumed
- **Test Jobs**: Clean up experimental or test research runs
- **Outdated Research**: Remove old research that is no longer relevant
- **Space Management**: Recover disk space completely
- **Privacy**: Remove sensitive or confidential research data
- **Organization**: Keep your research workspace clean and manageable

## Deletion Commands

### Single Job Deletion

Delete a specific job by its ID:

```bash
m1f-research --delete JOB_ID
```

**Example:**
```bash
# Delete job with confirmation
m1f-research --delete abc123

# Skip confirmation (automation-friendly)
m1f-research --delete abc123 --yes
```

### Bulk Deletion

Delete multiple jobs based on filters:

```bash
m1f-research --delete-bulk [FILTERS]
```

**Available Filters:**
- `--status-filter {active,completed,failed}` - Filter by job status
- `--date DATE` - Filter by creation date (Y-M-D, Y-M, or Y format)
- `--search TERM` - Filter by search term in query
- `--yes` - Skip confirmation prompt

**Examples:**
```bash
# Delete all failed jobs
m1f-research --delete-bulk --status-filter failed

# Delete jobs from January 2025
m1f-research --delete-bulk --date 2025-01

# Delete test jobs
m1f-research --delete-bulk --search "test"

# Combine filters
m1f-research --delete-bulk --status-filter failed --date 2025-07

# Automated deletion (no confirmation)
m1f-research --delete-bulk --status-filter failed --yes
```

## What Gets Deleted?

When you delete a job, the following items are permanently removed:

### Database Entries
- Main job record in `research_jobs.db`
- Job statistics in the database
- All references and foreign key relationships

### Filesystem Data
- Entire job directory at `research-data/YYYY/MM/DD/job_id_query/`
- Job-specific database (`research.db`)
- Research bundle (`RESEARCH_BUNDLE.md`)
- Executive summary (`EXECUTIVE_SUMMARY.md`)
- All scraped HTML content
- All converted Markdown content
- Analysis results and metadata
- Any temporary or cache files

## Safety Features

### Confirmation Prompts

By default, all deletion operations show job details and require confirmation:

```
Job to delete: abc123
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query: python async best practices
Status: completed
Created: 2025-07-23 14:30:22
Output: research-data/2025/07/23/abc123_python-async-best-practices

⚠️  Delete job abc123 and all its data? [y/N]:
```

For bulk deletion, you'll see a preview:

```
Jobs to delete (15 total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. [abc123] test query 1 (failed)
2. [def456] test query 2 (failed)
3. [ghi789] test query 3 (failed)
... and 12 more

⚠️  Delete 15 jobs with filters: status=failed? [y/N]:
```

### Error Handling

The deletion system handles various error scenarios:

- **Non-existent jobs**: Clear error message if job ID not found
- **Permission errors**: Attempts recovery with fallback methods
- **Partial failures**: Reports both successful and failed operations
- **Database integrity**: Uses transactions to prevent corruption

### Progress Tracking

Bulk deletions show real-time progress:

```
Deleting 25 jobs...
[████████████████████████████████████████] 100.0% Deletion complete
✅ Successfully deleted 23 jobs
❌ Failed to delete 2 jobs
  - job123: Permission denied
  - job456: Directory not found
```

## Deletion vs Cleanup Comparison

| Aspect | Clean Raw (`--clean-raw`) | Delete Job (`--delete`) |
|--------|---------------------------|-------------------------|
| **Database entry** | ✅ Preserved | ❌ Deleted |
| **Job directory** | ✅ Preserved | ❌ Deleted |
| **Research bundle** | ✅ Preserved | ❌ Deleted |
| **Analysis results** | ✅ Preserved | ❌ Deleted |
| **Raw HTML** | ❌ Deleted | ❌ Deleted |
| **Can resume** | ✅ Yes | ❌ No |
| **Recoverable** | ✅ Partially | ❌ No |
| **Space saved** | 🟡 Moderate | 🟢 Maximum |

## Common Workflows

### Regular Maintenance

Clean up failed jobs weekly:

```bash
# Review failed jobs
m1f-research --list-jobs --status-filter failed

# Delete all failed jobs
m1f-research --delete-bulk --status-filter failed
```

### Monthly Cleanup

Remove old research monthly:

```bash
# List jobs from 2 months ago
m1f-research --list-jobs --date 2025-05

# Review and delete old jobs
m1f-research --delete-bulk --date 2025-05
```

### Project Cleanup

Clean up after a project:

```bash
# Find all project-related jobs
m1f-research --list-jobs --search "project-name"

# Delete project jobs
m1f-research --delete-bulk --search "project-name"
```

### Automated Cleanup Script

```bash
#!/bin/bash
# cleanup-research.sh

# Delete failed jobs older than 7 days
m1f-research --delete-bulk --status-filter failed --yes

# Clean raw data from completed jobs
m1f-research --clean-all-raw --yes

echo "Cleanup complete!"
```

## Best Practices

### Before Deleting

1. **Review job details**: Always check what you're about to delete
2. **Export important data**: Use `--export` to save job data if needed
3. **Check research bundles**: Ensure you have copies of important results
4. **Consider cleanup first**: Try `--clean-raw` if you only need space

### Safe Deletion

1. **Use filters carefully**: Test filters with `--list-jobs` first
2. **Start small**: Delete individual jobs before bulk operations
3. **Keep confirmations**: Only use `--yes` in trusted scripts
4. **Document deletions**: Keep a log of what was deleted and why

### Recovery Planning

Since deletion is permanent:

1. **Regular exports**: Export important jobs to JSON regularly
2. **Backup bundles**: Copy research bundles to a backup location
3. **Version control**: Consider committing important research to git
4. **Archive first**: Move old jobs to archive storage before deleting

## Troubleshooting

### Common Issues

**"Job not found" error:**
- Verify job ID with `--list-jobs`
- Check you're in the correct directory
- Ensure the job hasn't already been deleted

**"Permission denied" errors:**
- Check file ownership and permissions
- Run with appropriate user privileges
- Consider using `sudo` if appropriate

**Partial deletion failures:**
- Check disk space and permissions
- Review error messages for specific issues
- Manually remove remaining files if needed

### Recovery from Mistakes

Unfortunately, deletion is permanent. To minimize risk:

1. Always review before confirming
2. Test with dry runs when possible
3. Keep backups of important research
4. Use cleanup instead of deletion when unsure

## FAQ

**Q: Can I undo a deletion?**
A: No, deletion is permanent. Always confirm before deleting.

**Q: What's the difference between cleanup and deletion?**
A: Cleanup removes only raw HTML data. Deletion removes everything.

**Q: Can I delete active jobs?**
A: Yes, but it's not recommended. Stop the job first if possible.

**Q: How do I delete jobs older than X days?**
A: Use date filters, e.g., `--delete-bulk --date 2025-06` for June 2025.

**Q: Is there a way to archive before deleting?**
A: Use `--export` to save job data, then manually archive files before deletion.

**Q: Can I recover a deleted job from the database?**
A: No, deletion removes all database entries permanently.

## Command Reference

### Options
- `--delete JOB_ID` - Delete a specific job
- `--delete-bulk` - Delete multiple jobs with filters
- `--yes` - Skip confirmation prompts
- `--status-filter` - Filter by job status
- `--date` - Filter by creation date
- `--search` - Filter by query content

### Examples
```bash
# Delete specific job
m1f-research --delete abc123

# Delete with auto-confirmation
m1f-research --delete abc123 --yes

# Delete failed jobs
m1f-research --delete-bulk --status-filter failed

# Delete old jobs
m1f-research --delete-bulk --date 2025-01

# Delete test jobs
m1f-research --delete-bulk --search "test"

# Combined filters
m1f-research --delete-bulk --status-filter failed --date 2025-07 --yes
```

## Summary

Job deletion is a powerful feature for managing your research workspace. Use it wisely:

- ✅ Delete failed and test jobs regularly
- ✅ Review before confirming deletions
- ✅ Use filters to target specific jobs
- ⚠️ Remember deletion is permanent
- ⚠️ Keep backups of important research
- ⚠️ Use `--yes` only in trusted automation
