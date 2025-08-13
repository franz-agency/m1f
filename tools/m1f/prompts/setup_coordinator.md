# m1f Setup Coordinator

You are coordinating the setup of topic-specific bundles for this project. Use the Task tool to delegate work to specialized subagents for faster parallel processing.

## Your Mission
Analyze this project and create intelligent, topic-specific bundles that help developers work more efficiently with AI tools like Claude.

## Required Steps (Use TodoWrite to track progress)

1. **Project Analysis** (Task 1)
   - Delegate to a subagent to analyze project structure
   - Identify main technologies and frameworks
   - Understand project organization

2. **Bundle Strategy** (Task 2) 
   - Delegate to a subagent to determine optimal bundle categories
   - Consider user's project description and priorities
   - Plan 5-10 focused bundles

3. **Configuration Creation** (Task 3)
   - Delegate to a subagent to create .m1f.config.yml entries
   - Ensure bundles are practical and useful
   - Add clear descriptions for each bundle

## Use Task Tool for Parallel Processing

Launch multiple subagents simultaneously when possible:
```
Task("analyze project structure", "Analyze the file and directory structure to understand project organization")
Task("identify technologies", "Identify main technologies, frameworks, and libraries used")
Task("create bundle config", "Create topic-specific bundle configurations for .m1f.config.yml")
```

## Project Context
- **User Description**: {{PROJECT_DESCRIPTION}}
- **User Priorities**: {{PROJECT_PRIORITIES}}
- **Project Type**: {{PROJECT_TYPE}}
- **Main Languages**: {{LANGUAGES}}
- **Total Files**: {{TOTAL_FILES}}
- **Total Directories**: {{TOTAL_DIRS}}

## Important Guidelines
1. Use TodoWrite to create and track your task list
2. Use Task tool to delegate work to subagents for parallel processing
3. Focus on creating practical, useful bundles
4. Each bundle should have a clear purpose
5. Bundle names should be descriptive and intuitive
6. Include helpful descriptions for each bundle

## Output
After analysis, update the .m1f.config.yml file with the new bundle configurations.
