# m1f-claude Timeout Improvements

## Problem Statement

The `m1f-claude --advanced-setup` command was experiencing timeout issues ("dauert ewigkeiten" - takes forever) due to:

1. **Blocking subprocess calls** - No progress feedback during execution
2. **No timeout handling** - Could hang indefinitely  
3. **Poor user experience** - Users see nothing while Claude analyzes large projects

## Solution: Apply html2md Improvements

Based on successful improvements in the html2md tool, we've implemented:

### 1. Streaming Output with Timestamps

```python
# OLD: Blocking call with no feedback
result = subprocess.run(cmd, cwd=self.project_path, capture_output=False, text=True)

# NEW: Streaming with progress
runner = M1FClaudeRunner()
returncode, stdout, stderr = runner.run_claude_streaming(
    prompt=prompt,
    timeout=300,  # 5 minutes
    show_output=True
)
```

Users now see:
```
[  0.5s] Reading project structure...
[ 12.3s] Analyzing 1,234 files...
[ 45.6s] Creating bundle configuration...
[123.4s] Writing .m1f.config.yml...
```

### 2. Robust Timeout Handling

- **Absolute timeout**: Default 10 minutes (configurable)
- **Inactivity timeout**: 60 seconds without output
- **Conservative minimums**: `max(60, timeout)` ensures reasonable timeouts
- **Graceful interruption**: Ctrl-C handling with cleanup

### 3. Progress Indicators

During waiting periods:
```
⏳ Waiting for Claude... ⠏ [45s]
```

### 4. Better Error Handling

- Clear timeout messages
- Preservation of partial output
- Proper process cleanup
- Informative error reporting

## Implementation Details

### New M1FClaudeRunner Class

Located in `tools/m1f_claude_runner.py`:

- **Binary detection**: Checks PATH and common installation locations
- **Streaming subprocess**: Uses `Popen` for line-by-line output
- **Signal handling**: Graceful interruption support
- **Output collection**: Preserves all output even on timeout

### Integration Points

Modified in `m1f_claude.py`:

1. **advanced_setup() method** (lines 1481-1510)
   - Phase 1: Segmentation with streaming
   - Phase 2: Verification with streaming

2. **Timeout configuration**:
   - 5 minutes for each phase
   - Suitable for large projects
   - Can be increased if needed

## Usage Improvements

### Before (User Experience)
```bash
$ m1f-claude --advanced-setup
🤖 Sending to Claude Code...
⏳ Claude will now analyze your project...
[Nothing for minutes... appears frozen]
```

### After (User Experience)  
```bash
$ m1f-claude --advanced-setup
🤖 Sending to Claude Code...
⏳ Claude will now analyze your project...

[  0.5s] Let me analyze your project structure...
[  2.1s] Reading m1f/project_analysis_filelist.txt
[  3.4s] Found 1,234 files across 156 directories
[ 15.6s] Creating topic-specific bundle configuration...
[ 45.2s] Writing updated .m1f.config.yml
[120.3s] ✅ Configuration complete!

✅ Claude completed in 125.4s
```

## Testing

Run the test script to verify improvements:
```bash
python test_claude_runner_improvements.py
```

## Benefits

1. **Transparency**: Users see what Claude is doing
2. **Reliability**: Automatic timeout prevents infinite hangs  
3. **Debuggability**: Timestamps help identify slow operations
4. **Control**: Can interrupt gracefully with Ctrl-C
5. **Consistency**: Uses same proven approach as html2md

## Future Enhancements

1. **Parallel processing**: Run multiple Claude tasks concurrently
2. **Resume capability**: Save state for interrupted operations
3. **Progress estimation**: Show percentage completion
4. **Configurable timeouts**: Per-phase timeout settings

## Troubleshooting

### If timeouts still occur:

1. **Increase timeout**: Modify timeout parameter in code
2. **Simplify project**: Use `.m1f.config.yml` excludes
3. **Check Claude installation**: Ensure latest version
4. **Review project size**: Very large projects may need chunking

### Debug mode:

Set `--debug` flag for detailed output:
```bash
m1f-claude --advanced-setup --debug
```