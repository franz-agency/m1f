# m1f-research CLI Reference

Complete command-line interface reference for m1f-research.

## Synopsis

```bash
m1f-research [QUERY] [OPTIONS]
```

## Positional Arguments

### `query`

Research topic or query (required for new jobs, optional when using job
management commands)

## Options

### General Options

| Option            | Short | Description                            | Default |
| ----------------- | ----- | -------------------------------------- | ------- |
| `--help`          | `-h`  | Show help message and exit             | -       |
| `--version`       |       | Show program version                   | -       |
| `--verbose`       | `-v`  | Increase verbosity (use -vv for debug) | Warning |
| `--quiet`         | `-q`  | Suppress non-error output              | False   |
| `--dry-run`       |       | Preview without executing              | False   |
| `--yes`           | `-y`  | Answer yes to all prompts              | False   |
| `--config CONFIG` | `-c`  | Path to configuration file             | None    |

### Output Options

| Option                  | Short | Description                  | Default |
| ----------------------- | ----- | ---------------------------- | ------- |
| `--format {text,json}`  |       | Output format                | text    |
| `--no-color`            |       | Disable colored output       | False   |

### Extended Help

| Option             | Description                     |
| ------------------ | ------------------------------- |
| `--help-examples`  | Show extended usage examples    |
| `--help-filters`   | Show filtering guide            |
| `--help-providers` | Show LLM provider setup guide   |

### LLM Provider Options

| Option                | Short | Description                                                          | Default          |
| --------------------- | ----- | -------------------------------------------------------------------- | ---------------- |
| `--provider PROVIDER` | `-p`  | LLM provider: claude, claude-cli, gemini, gemini-cli, openai         | claude           |
| `--model MODEL`       | `-m`  | Specific model to use                                                | Provider default |
| `--template TEMPLATE` | `-t`  | Analysis template: general, technical, academic, tutorial, reference | general          |

### Research Options

| Option           | Short | Description                        | Default |
| ---------------- | ----- | ---------------------------------- | ------- |
| `--urls N`       |       | Number of URLs to search for       | 20      |
| `--scrape N`     |       | Maximum URLs to scrape             | 10      |
| `--concurrent N` |       | Max concurrent scraping operations | 5       |
| `--no-filter`    |       | Disable content filtering          | False   |
| `--no-analysis`  |       | Skip AI analysis (just scrape)     | False   |
| `--interactive`  | `-i`  | Start in interactive mode          | False   |

### Output Options

| Option         | Short | Description                     | Default         |
| -------------- | ----- | ------------------------------- | --------------- |
| `--output DIR` | `-o`  | Output directory                | ./research-data |
| `--name NAME`  | `-n`  | Custom name for research bundle | Auto-generated  |

### Job Management

| Option             | Description                                |
| ------------------ | ------------------------------------------ |
| `--resume JOB_ID`  | Resume an existing research job            |
| `--list-jobs`      | List all research jobs                     |
| `--status JOB_ID`  | Show detailed status of a specific job     |
| `--watch JOB_ID`   | Watch job progress in real-time            |
| `--urls-file FILE` | File containing URLs to add (one per line) |

### List Filtering Options

| Option                                            | Description                 | Example             |
| ------------------------------------------------- | --------------------------- | ------------------- |
| `--limit N`                                       | Limit number of results     | `--limit 10`        |
| `--offset N`                                      | Skip N results (pagination) | `--offset 20`       |
| `--date DATE`                                     | Filter by date              | `--date 2025-07-23` |
| `--search TERM`                                   | Search jobs by query term   | `--search "react"`  |
| `--status-filter {active,completed,failed}`      | Filter by job status        | `--status-filter completed` |

### Data Management Options

| Option               | Description                          |
| -------------------- | ------------------------------------ |
| `--clean-raw JOB_ID` | Clean raw HTML data for specific job |
| `--clean-all-raw`    | Clean raw HTML data for all jobs     |
| `--export JOB_ID`    | Export job data to JSON              |

## Command Examples

### Basic Research

```bash
# Simple research
m1f-research "python async programming"

# With custom settings
m1f-research "react hooks" --urls 30 --scrape 15

# Using different provider
m1f-research "machine learning" --provider gemini --model gemini-1.5-pro

# Skip analysis for faster results
m1f-research "tailwind css" --no-analysis

# Custom output location
m1f-research "rust ownership" --output ~/research --name rust-guide
```

### Job Management

```bash
# List all jobs
m1f-research --list-jobs

# List with pagination
m1f-research --list-jobs --limit 10 --offset 0

# Filter by date
m1f-research --list-jobs --date 2025-07-23  # Specific day
m1f-research --list-jobs --date 2025-07     # Month
m1f-research --list-jobs --date 2025        # Year

# Search for jobs
m1f-research --list-jobs --search "python"

# Combined filters
m1f-research --list-jobs --date 2025-07 --search "async" --limit 5

# Check job status
m1f-research --status abc123

# Resume a job
m1f-research --resume abc123

# Add URLs to existing job
m1f-research --resume abc123 --urls-file additional-urls.txt
```

### Manual URL Management

```bash
# Start with manual URLs only
m1f-research "my topic" --urls 0 --urls-file my-urls.txt

# Combine LLM search with manual URLs
m1f-research "my topic" --urls 20 --urls-file my-urls.txt

# Add URLs to existing job
m1f-research --resume abc123 --urls-file more-urls.txt
```

### Data Cleanup

```bash
# Clean specific job
m1f-research --clean-raw abc123

# Clean all jobs (with confirmation)
m1f-research --clean-all-raw
```

### Advanced Workflows

```bash
# Dry run to preview
m1f-research "test query" --dry-run

# Very verbose output for debugging
m1f-research "test query" -vv

# Interactive mode
m1f-research --interactive

# Technical analysis with high URL count
m1f-research "kubernetes networking" --template technical --urls 50 --scrape 25
```

## Date Format Examples

The `--date` filter supports multiple formats:

| Format | Example      | Matches               |
| ------ | ------------ | --------------------- |
| Y-M-D  | `2025-07-23` | Specific day          |
| Y-M    | `2025-07`    | All jobs in July 2025 |
| Y      | `2025`       | All jobs in 2025      |

## Exit Codes

| Code | Meaning                      |
| ---- | ---------------------------- |
| 0    | Success                      |
| 1    | General error                |
| 130  | Interrupted by user (Ctrl+C) |

## Environment Variables

| Variable            | Description        |
| ------------------- | ------------------ |
| `ANTHROPIC_API_KEY` | API key for Claude |
| `GOOGLE_API_KEY`    | API key for Gemini |
| `OPENAI_API_KEY`    | API key for OpenAI |

## Configuration File

Create `.m1f.config.yml` for persistent settings:

```yaml
research:
  llm:
    provider: claude
    model: claude-3-opus-20240229

  defaults:
    url_count: 30
    scrape_count: 15

  output:
    directory: ~/research-data
```

## Tips

1. **Save Job IDs**: Copy job IDs for easy resume/reference
2. **Use Filters**: Combine date and search for precise results
3. **Pagination**: Use limit/offset for large job lists
4. **Cleanup**: Regularly clean raw data to save space
5. **Manual URLs**: Supplement with your own curated links
