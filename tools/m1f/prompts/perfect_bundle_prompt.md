# Perfect Bundle Creation Prompt for m1f-claude

## 🎯 CREATE PERFECT TOPIC-SPECIFIC BUNDLES FOR THIS PROJECT

============================================================

The basic bundles (complete.txt and docs.txt) have already been created. Now
create additional topic-specific bundles following BEST PRACTICES.

## 📚 REQUIRED READING (IN THIS ORDER):

1. READ: @m1f/m1f.txt for m1f documentation and bundle configuration syntax
2. READ: @m1f/project_analysis_dirlist.txt for directory structure
3. READ: @m1f/project_analysis_filelist.txt for complete file listing

⚠️ IMPORTANT: Read ALL three files above before proceeding!

## 🏆 BEST PRACTICES FOR PERFECT BUNDLES

### 1. MODULAR ARCHITECTURE PRINCIPLE

- Identify each logical module, tool, or subsystem in the project
- Create one bundle per module/tool (e.g., auth-module, payment-module,
  user-module)
- Each module bundle should be self-contained and meaningful

### 2. USE PRECISE INCLUDES, NOT BROAD EXCLUDES

Instead of excluding everything except what you want, use precise includes:

```yaml
# ❌ BAD - Too broad, relies on excludes
sources:
  - path: "."
    excludes: ["tests/", "docs/", "scripts/", "node_modules/"]

# ✅ GOOD - Precise includes
sources:
  - path: "tools/"
    include_extensions: [".py"]
    includes: ["auth/**", "auth.py", "utils.py", "__init__.py"]
```

### 3. BUNDLE GROUPING STRATEGY

Organize bundles into logical groups:

- `documentation` - All documentation bundles
- `source` - Source code bundles by module
- `tests` - Test code bundles
- `config` - Configuration bundles
- `complete` - Aggregated bundles

### 4. NUMBERED OUTPUT FILES

Use numbered prefixes for proper sorting:

```yaml
output: "m1f/project/87_module1_docs.txt"  # Documentation
output: "m1f/project/94_module1_code.txt"  # Source code
output: "m1f/project/95_module2_code.txt"  # Source code
output: "m1f/project/99_complete.txt"      # Complete bundle
```

### 5. HIERARCHICAL BUNDLES

Create aggregated bundles that combine related bundles:

- `all-docs` - Combines all documentation
- `all-tests` - Combines all tests
- `all-frontend` - Combines all frontend code
- `complete` - The ultimate bundle with everything

### 6. SHARED FILES STRATEGY

When files are used by multiple modules (like utils, constants, types):

- Include them in each relevant module bundle
- This ensures each bundle is self-contained

## 🔍 PROJECT ANALYSIS STEPS

### STEP 1: Identify Project Architecture

Analyze the directory structure to find:

- Monorepo with packages? → Create bundle per package
- Multiple apps/services? → Create bundle per app
- Modular architecture? → Create bundle per module
- Plugin/Extension system? → Create bundle per plugin
- Frontend/Backend split? → Create bundles for each

### STEP 2: Find Logical Boundaries

Look for natural boundaries in the code:

- Directory names that indicate modules (auth/, payment/, user/)
- File naming patterns (auth.service.ts, auth.controller.ts)
- Configuration files that define modules
- Import patterns that show dependencies

### STEP 3: Design Bundle Hierarchy

Plan your bundles in this order:

1. Module/tool-specific bundles (most granular)
2. Category bundles (tests, docs, config)
3. Aggregated bundles (all-docs, all-frontend)
4. Complete bundle (everything)

## 📝 BUNDLE CREATION RULES

### NAMING CONVENTIONS

- Use lowercase with hyphens: `user-service`, `auth-module`
- Be descriptive but concise
- Group prefix when applicable: `frontend-components`, `backend-api`

### OUTPUT FILE PATTERNS

```
m1f/{project_name}/
├── 80-89_*_docs.txt     # Documentation bundles
├── 90-93_*_config.txt   # Configuration bundles
├── 94-98_*_code.txt     # Source code bundles
└── 99_*_complete.txt    # Complete/aggregated bundles
```

### SOURCES CONFIGURATION

Always use the most specific configuration:

```yaml
sources:
  - path: "src/modules/auth"
    include_extensions: [".ts", ".js"]
    includes: ["**/*.service.ts", "**/*.controller.ts"]
  - path: "src/shared"
    includes: ["auth-utils.ts", "auth-types.ts"]
```

## 🚨 CRITICAL RULES - MUST FOLLOW

1. **NO DEFAULT EXCLUDES**: Don't exclude node_modules, .git, **pycache**, etc.
2. **NO BINARY/ASSET BUNDLES**: Skip images, fonts, compiled files
3. **MAX 20 BUNDLES**: Including existing complete and docs
4. **USE INCLUDES OVER EXCLUDES**: Be precise about what to include
5. **SELF-CONTAINED BUNDLES**: Each bundle should be useful standalone

## 🎯 IMPLEMENTATION CHECKLIST

□ Read all three required files completely □ Identify the project's modular
structure □ Plan bundle hierarchy (modules → categories → aggregated) □ Design
precise `includes` patterns for each bundle □ Use numbered output files for
sorting □ Group bundles logically □ Create aggregated bundles where valuable □
Keep total count under 20 bundles □ Use MultiEdit to add all bundles at once

## 💡 EXAMPLE PATTERNS TO RECOGNIZE

### For a Multi-Service Project:

```yaml
bundles:
  # Service-specific bundles
  auth-service:
    group: "services"
    output: "m1f/project/94_auth_service.txt"
    sources:
      - path: "services/auth"
        include_extensions: [".js", ".ts"]
      - path: "shared"
        includes: ["auth/**", "types/auth.ts"]

  user-service:
    group: "services"
    output: "m1f/project/95_user_service.txt"
    sources:
      - path: "services/user"
        include_extensions: [".js", ".ts"]
      - path: "shared"
        includes: ["user/**", "types/user.ts"]
```

### For a Plugin-Based System:

```yaml
bundles:
  plugin-core:
    group: "core"
    output: "m1f/project/94_plugin_core.txt"
    sources:
      - path: "core"
        include_extensions: [".py"]
      - path: "plugins"
        includes: ["__init__.py", "base.py"]

  plugin-auth:
    group: "plugins"
    output: "m1f/project/95_plugin_auth.txt"
    sources:
      - path: "plugins/auth"
      - path: "core"
        includes: ["plugin_utils.py"]
```

## ⚡ FINAL STEPS

1. Analyze the project structure deeply
2. Design bundles that reflect the project's architecture
3. Use precise includes to create focused bundles
4. Test your mental model: "Would each bundle be useful alone?"
5. Create the configuration with MultiEdit

Remember: The goal is bundles that are **modular**, **focused**, and
**self-contained**!
