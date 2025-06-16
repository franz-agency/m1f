🔍 VERIFY AND IMPROVE M1F CONFIGURATION
============================================================

Your task is to verify the .m1f.config.yml that was just created and improve it if needed.

📋 VERIFICATION CHECKLIST:

1. **Read .m1f.config.yml** - Check the current configuration
2. **Check Generated Bundles** - Look in m1f/ directory for .txt files
3. **Verify Bundle Quality**:
   - Are focused/task bundles ideally under 180KB for Claude Code usage?
   - Are larger reference bundles under 5MB for Claude AI?
   - Complete/full bundles can be larger - that's OK!
   - Do they contain the expected content?
   - Are there any errors or warnings?
4. **Test a Bundle** - Read at least one generated bundle (e.g., @m1f/{project_name}_complete.txt)
5. **Check for Common Issues**:
   - Redundant excludes (node_modules, .git, etc. are auto-excluded)
   - Missing important files
   - Bundles that are too large or too small
   - Incorrect separator_style (should be Standard or omitted)
   - Wrong sources format (should use 'sources:' array, not 'source_directory:')

🛠️ IMPROVEMENT ACTIONS:

If you find issues:
1. **Fix Configuration Errors** - Update .m1f.config.yml
2. **Optimize Bundle Organization** - Better grouping or splitting
3. **Add Missing Bundles** - If important areas aren't covered
4. **Remove Redundant Bundles** - If there's too much overlap
5. **Fix Size Issues** - Split large bundles or combine small ones

📝 SPECIFIC CHECKS:

1. Run: `ls -lah m1f/` to see all generated bundles and their sizes
2. SIZE GUIDELINES: 
   - Task-focused bundles: Ideally < 180KB for Claude Code
   - Reference bundles: Ideally < 5MB for Claude AI
   - Complete/full bundles: Can be much larger (40MB+ is fine)
3. Check for m1f-update errors in the output above
4. Read the complete bundle (e.g., @m1f/{project_name}_complete.txt) to verify content inclusion
5. Ensure each bundle serves a clear, distinct purpose

⚠️ SIZE OPTIMIZATION GUIDELINES:
For bundles intended for Claude Code that exceed 180KB:
1. Consider splitting into smaller, more focused bundles
2. Use more specific includes patterns
3. Create sub-bundles for large topics (e.g., api-core-1, api-core-2)
Note: This is a guideline - some bundles naturally need to be larger!

📊 PROJECT CONTEXT:
- Type: {project_type}
- Languages: {languages}
- Total Files: {total_files}

🎯 EXPECTED OUTCOME:

After verification:
1. The .m1f.config.yml should be optimal for this project
2. All bundles should generate without errors
3. Each bundle should be appropriately sized for its purpose:
   - Task-focused bundles: Ideally < 180KB for Claude Code
   - Reference bundles: Ideally < 5MB for Claude AI
   - Complete bundles: Any size that captures the full scope
4. The configuration should follow all best practices

If everything looks good, just confirm. If improvements are needed, make them!

📈 SIZE OPTIMIZATION STRATEGIES:

For bundles that are too large:
```yaml
# Instead of this (too large):
api-documentation:
  sources:
    - path: "docs/api"

# Do this (split by topic):
api-01-authentication:
  sources:
    - path: "docs/api"
      includes: ["auth*.md", "login*.md", "session*.md"]

api-02-data-models:
  sources:
    - path: "docs/api"
      includes: ["models/*.md", "schema*.md"]

api-03-endpoints:
  sources:
    - path: "docs/api"
      includes: ["endpoints/*.md", "routes*.md"]
```

🔍 FINAL VERIFICATION:
After making any changes, run `m1f-update` again and verify all bundles are under 180KB!