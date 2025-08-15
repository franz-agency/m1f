# Coordinated Parallel HTML Analysis with Subagents

You will coordinate the parallel analysis of multiple HTML files using the Task tool to delegate work to subagents for maximum efficiency.

## Context

Analyzing {num_files} HTML files to understand their structure for optimal content extraction.
{project_description}

## Files to Analyze

{file_list}

## Your Task

1. **Setup tracking**: Use TodoWrite to create a task list for all {num_files} files
2. **Launch parallel subagents**: Use the Task tool to analyze ALL files simultaneously
3. **Track completion**: Update todo items as subagents complete
4. **Verify results**: Ensure all analysis files are created in {analysis_dir}

## CRITICAL: Parallel Execution

**You MUST launch ALL {num_files} Task tool calls in a SINGLE message for true parallel execution.**

For each file, create a Task with:
- `subagent_type`: "general-purpose"  
- `description`: "Analyze HTML file N"
- `prompt`: The specific analysis instructions for that file

## Subagent Instructions Template

Each subagent should receive instructions to:
1. Read their assigned HTML file
2. Analyze the structure following the criteria
3. Write findings to the specified output path
4. Confirm completion with "ANALYSIS_COMPLETE_OK"

{detailed_instructions}

## Expected Workflow

1. Create todo list with all {num_files} files
2. Launch ALL {num_files} Task tool calls simultaneously (in one message)
3. Monitor completion and update todos
4. Verify all analysis files exist
5. Report final status

## Success Criteria

- All {num_files} analysis files created in {analysis_dir}
- Each file contains proper structural analysis
- Clear summary of results

Remember: The key to speed is launching ALL tasks at once, not sequentially!
