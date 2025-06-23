# m1f Configuration Examples

This guide provides comprehensive examples of `.m1f.config.yml` files for
different project types. Each example includes detailed comments explaining the
configuration choices.

> **⚠️ IMPORTANT**: m1f automatically excludes many common directories
> (node_modules, .git, **pycache**, etc.). See the
> [Default Excludes Guide](./26_default_excludes_guide.md) for the complete
> list. **Only add project-specific excludes to keep your configs minimal!**

## 🚨 IMPORTANT: Use Standard Separator for AI Bundles!

**The primary purpose of m1f bundles is to provide context to AI assistants like
Claude, NOT for human reading in Markdown!**

- ✅ **ALWAYS use**: `separator_style: Standard` (or omit it - Standard is the
  default)
- ❌ **AVOID**: `separator_style: Markdown` (this adds unnecessary ```language
  blocks)
- 🎯 **Why**: Standard format is clean and optimal for AI consumption

```yaml
# CORRECT - For AI consumption:
bundles:
  - name: my-bundle
    separator_style: Standard  # ← This is optimal (or just omit it)

# AVOID - Adds unnecessary markdown formatting:
bundles:
  - name: my-bundle
    separator_style: Markdown  # ← Don't use for AI bundles!
```

**Note**: `MachineReadable` is only needed when you plan to use `s1f` to split
the bundle back into individual files.

## Minimal vs Verbose Configurations

### ❌ BAD Example - Overly Verbose (Don't Do This!)

```yaml
global:
  global_excludes:
    # ❌ ALL of these are already excluded by default!
    - "**/node_modules/**" # Auto-excluded
    - "**/vendor/**" # Auto-excluded
    - "**/__pycache__/**" # Auto-excluded
    - "**/build/**" # Auto-excluded
    - "**/dist/**" # Auto-excluded
    - "**/.git/**" # Auto-excluded
    - "**/cache/**" # Auto-excluded
    - "**/.vscode/**" # Auto-excluded
    - "**/.idea/**" # Auto-excluded

    # ✅ Only these are needed (project-specific)
    - "**/logs/**"
    - "**/tmp/**"
    - "/m1f/**"
```

### ✅ GOOD Example - Minimal Configuration

```yaml
global:
  global_excludes:
    # Only project-specific excludes
    - "**/logs/**" # Your log files
    - "**/tmp/**" # Your temp files
    - "/m1f/**" # Output directory

  global_settings:
    # Let .gitignore handle most excludes
    exclude_paths_file: ".gitignore"
```

## Table of Contents

1. [m1f Tool Project (Current)](#m1f-tool-project-current)
2. [Node.js/React Project](#nodejsreact-project)
3. [Python/Django Project](#pythondjango-project)
4. [WordPress Theme](#wordpress-theme)
5. [Documentation Site](#documentation-site)
6. [Mixed Language Project](#mixed-language-project)
7. [Microservices Architecture](#microservices-architecture)
8. [Mobile App Project](#mobile-app-project)

## m1f Tool Project (Current)

This is the actual configuration used by the m1f project itself - a Python-based
tool with comprehensive documentation.

```yaml
# m1f Auto-Bundle Configuration

# Global settings
global:
  # Exclusions that apply to all bundles
  global_excludes:
    - "/m1f/**" # Exclude output directory
    - "**/*.pyc" # Python bytecode
    - "**/*.log" # Log files
    - "**/tmp/**" # Temporary directories
    - "**/dev/**" # Development files
    - "**/tests/**/source/**" # Test input data
    - "**/tests/**/output/**" # Test output data
    - "**/tests/**/expected/**" # Expected test results
    - "**/tests/**/scraped_examples/**" # Scraped test examples

  global_settings:
    # Default security setting for all files
    security_check: "warn" # Strict by default
    # Use .gitignore as exclude file (can be single file or list)
    exclude_paths_file:
      - ".gitignore"
      - ".m1fignore"

    # Per-extension overrides
    extensions:
      .py:
        security_check: "abort" # Strict for Python files

  # Default settings for all bundles
  defaults:
    force_overwrite: true
    max_file_size: "1MB"
    minimal_output: false

  # File watcher settings for auto-update
  watcher:
    enabled: true
    debounce_seconds: 2
    ignored_paths:
      - "/m1f"
      - ".git/"
      - ".venv/"
      - "tmp/"
      - ".scrapes/"

# Bundle definitions
bundles:
  # Documentation bundles - separate by tool
  m1f-docs:
    description: "m1f docs"
    group: "documentation"
    output: "m1f/m1f/87_m1f_only_docs.txt"
    sources:
      - path: "docs/01_m1f"

  html2md-docs:
    description: "html2md docs"
    group: "documentation"
    output: "m1f/m1f/88_html2md_docs.txt"
    sources:
      - path: "docs/03_html2md"

  # Source code bundles - modular approach
  m1f-code:
    description: "m1f complete code"
    group: "source"
    output: "m1f/m1f/94_code.txt"
    sources:
      - path: "."
        includes:
          [
            "README.md",
            "SETUP.md",
            "requirements.txt",
            "tools/**",
            "scripts/**",
          ]
      - path: "tests/"
        excludes:
          [
            "**/tests/**/source/**",
            "**/tests/**/extracted/**",
            "**/tests/**/output/**",
          ]

  # Complete project bundle
  all:
    description: "All 1 One"
    group: "complete"
    output: "m1f/m1f/99_m1f_complete.txt"
    sources:
      - path: "."
```

## Node.js/React Project

Configuration for a modern React application with TypeScript and testing.

```yaml
# React Application m1f Configuration

global:
  global_excludes:
    # ⚠️ MINIMAL CONFIG - Only project-specific excludes!
    # DON'T add node_modules, dist, build - they're auto-excluded!

    # Next.js specific (not in defaults)
    - "**/.next/**" # Next.js build cache
    - "**/coverage/**" # Test coverage reports

    # Log and temp files
    - "**/*.log"
    - "**/*.map" # Source maps
    - "**/.DS_Store"
    - "**/Thumbs.db"

  global_settings:
    security_check: "warn"
    exclude_paths_file: [".gitignore", ".eslintignore"]

    # JavaScript/TypeScript specific processing
    extensions:
      .js:
        minify: true # Minify for AI context
        remove_comments: true # Clean comments
      .jsx:
        minify: true
        remove_comments: true
      .ts:
        minify: true
        remove_comments: true
      .tsx:
        minify: true
        remove_comments: true
      .json:
        minify: true # Compact JSON
      .env:
        security_check: "abort" # Never include env files

  defaults:
    force_overwrite: true
    max_file_size: "500KB" # Smaller for JS files
    minimal_output: true # Compact output

bundles:
  # Application source code
  app-components:
    description: "React components"
    group: "frontend"
    output: "m1f/01_components.txt"
    sources:
      - path: "src/components"
        include_extensions: [".tsx", ".ts", ".css", ".scss"]
      - path: "src/hooks"
        include_extensions: [".ts", ".tsx"]

  app-pages:
    description: "Application pages/routes"
    group: "frontend"
    output: "m1f/02_pages.txt"
    sources:
      - path: "src/pages"
      - path: "src/routes"
      - path: "src/layouts"

  app-state:
    description: "State management (Redux/Context)"
    group: "frontend"
    output: "m1f/03_state.txt"
    sources:
      - path: "src/store"
      - path: "src/redux"
      - path: "src/context"
      - path: "src/reducers"
      - path: "src/actions"

  # API and services
  app-api:
    description: "API integration layer"
    group: "integration"
    output: "m1f/10_api.txt"
    sources:
      - path: "src/api"
      - path: "src/services"
      - path: "src/graphql"
        include_extensions: [".ts", ".graphql", ".gql"]

  # Configuration and setup
  app-config:
    description: "Build configuration"
    group: "config"
    output: "m1f/20_config.txt"
    sources:
      - path: "."
        includes:
          [
            "package.json",
            "tsconfig.json",
            "webpack.config.js",
            "vite.config.js",
            ".eslintrc.*",
            ".prettierrc.*",
            "babel.config.*",
          ]

  # Tests
  app-tests:
    description: "Test suites"
    group: "testing"
    output: "m1f/30_tests.txt"
    sources:
      - path: "src"
        includes:
          ["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts", "**/*.spec.tsx"]
      - path: "__tests__"
      - path: "cypress/integration"
        include_extensions: [".js", ".ts"]

  # Documentation
  app-docs:
    description: "Project documentation"
    group: "docs"
    output: "m1f/40_docs.txt"
    sources:
      - path: "."
        includes: ["README.md", "CONTRIBUTING.md", "docs/**/*.md"]
      - path: "src"
        includes: ["**/*.md"]

  # Quick reference bundle for AI assistance
  app-quick-reference:
    description: "Key files for quick AI context"
    group: "reference"
    output: "m1f/00_quick_reference.txt"
    max_file_size: "100KB" # Keep small for quick loading
    sources:
      - path: "."
        includes: ["package.json", "README.md", "src/App.tsx", "src/index.tsx"]
      - path: "src/types" # TypeScript types
```

## Python/Django Project

Configuration for a Django web application with REST API.

```yaml
# Django Project m1f Configuration

global:
  global_excludes:
    # ⚠️ MINIMAL CONFIG - __pycache__, .pytest_cache, etc. are auto-excluded!

    # Python bytecode (not in defaults)
    - "**/*.pyc"
    - "**/*.pyo"
    - "**/*.pyd"

    # Virtual environments (common names)
    - "**/venv/**"
    - "**/.venv/**"
    - "**/env/**"

    # Django specific
    - "**/migrations/**" # Database migrations
    - "**/media/**" # User uploads
    - "**/static/**" # Collected static files
    - "**/staticfiles/**"
    - "**/*.sqlite3" # SQLite database
    - "**/celerybeat-schedule"

  global_settings:
    security_check: "abort" # Strict for web apps
    exclude_paths_file: ".gitignore"

    extensions:
      .py:
        remove_docstrings: false # Keep docstrings for API
        remove_comments: true # Remove inline comments
      .html:
        minify: true # Minify templates
      .env:
        security_check: "abort" # Never include
      .yml:
        security_check: "warn" # Check for secrets

  defaults:
    force_overwrite: true
    max_file_size: "1MB"

bundles:
  # Django apps - one bundle per app
  app-accounts:
    description: "User accounts and authentication"
    group: "apps"
    output: "m1f/apps/01_accounts.txt"
    sources:
      - path: "accounts/"
        excludes: ["migrations/", "__pycache__/", "*.pyc"]

  app-api:
    description: "REST API implementation"
    group: "apps"
    output: "m1f/apps/02_api.txt"
    sources:
      - path: "api/"
        excludes: ["migrations/", "__pycache__/"]
      - path: "."
        includes: ["**/serializers.py", "**/viewsets.py"]

  app-core:
    description: "Core business logic"
    group: "apps"
    output: "m1f/apps/03_core.txt"
    sources:
      - path: "core/"
        excludes: ["migrations/", "__pycache__/"]

  # Project configuration
  django-settings:
    description: "Django settings and configuration"
    group: "config"
    output: "m1f/10_settings.txt"
    sources:
      - path: "config/" # Settings module
      - path: "."
        includes:
          ["manage.py", "requirements*.txt", "Dockerfile", "docker-compose.yml"]

  # Models across all apps
  django-models:
    description: "All database models"
    group: "database"
    output: "m1f/20_models.txt"
    sources:
      - path: "."
        includes: ["**/models.py", "**/models/*.py"]

  # Views and URLs
  django-views:
    description: "Views and URL patterns"
    group: "views"
    output: "m1f/21_views.txt"
    sources:
      - path: "."
        includes: ["**/views.py", "**/views/*.py", "**/urls.py"]

  # Templates
  django-templates:
    description: "HTML templates"
    group: "frontend"
    output: "m1f/30_templates.txt"
    sources:
      - path: "templates/"
      - path: "."
        includes: ["**/templates/**/*.html"]

  # Tests
  django-tests:
    description: "Test suites"
    group: "testing"
    output: "m1f/40_tests.txt"
    sources:
      - path: "."
        includes: ["**/tests.py", "**/tests/*.py", "**/test_*.py"]

  # Management commands
  django-commands:
    description: "Custom management commands"
    group: "utilities"
    output: "m1f/50_commands.txt"
    sources:
      - path: "."
        includes: ["**/management/commands/*.py"]

  # Quick AI reference
  django-quick-ref:
    description: "Essential files for AI context"
    group: "reference"
    output: "m1f/00_quick_reference.txt"
    max_file_size: "100KB"
    sources:
      - path: "."
        includes:
          [
            "README.md",
            "requirements.txt",
            "config/settings/base.py",
            "config/urls.py",
          ]
```

## WordPress Theme

Configuration for a custom WordPress theme with modern build tools.

```yaml
# WordPress Theme m1f Configuration

global:
  global_excludes:
    # ⚠️ MINIMAL CONFIG - node_modules, vendor, build, dist are auto-excluded!

    # WordPress specific (not in defaults)
    - "wp-admin/**" # Core files
    - "wp-includes/**" # Core files
    - "wp-content/uploads/**" # User uploads
    - "wp-content/cache/**" # Cache plugins
    - "wp-content/backup/**" # Backup files
    - "wp-content/upgrade/**" # Updates

    # Sass cache (not in defaults)
    - "**/.sass-cache/**"
    - "**/*.map" # Source maps
    - "**/*.log" # Log files

  global_settings:
    security_check: "warn"
    exclude_paths_file: [".gitignore", ".wpignore"]

    # Use WordPress preset for optimal processing
    preset: "wordpress"

    extensions:
      .php:
        remove_comments: true # Clean PHP comments
      .js:
        minify: true
      .css:
        minify: true
      .scss:
        minify: true

  defaults:
    force_overwrite: true
    max_file_size: "500KB"

bundles:
  # Theme core files
  theme-core:
    description: "Theme core functionality"
    group: "theme"
    output: "m1f/01_theme_core.txt"
    sources:
      - path: "."
        includes: [
            "style.css", # Theme header
            "functions.php",
            "index.php",
            "header.php",
            "footer.php",
            "sidebar.php",
            "searchform.php",
            "404.php",
          ]

  # Template files
  theme-templates:
    description: "Page and post templates"
    group: "theme"
    output: "m1f/02_templates.txt"
    sources:
      - path: "."
        includes:
          [
            "single*.php",
            "page*.php",
            "archive*.php",
            "category*.php",
            "tag*.php",
            "taxonomy*.php",
            "front-page.php",
            "home.php",
          ]
      - path: "template-parts/"
      - path: "templates/"

  # Theme includes/components
  theme-includes:
    description: "Theme includes and components"
    group: "theme"
    output: "m1f/03_includes.txt"
    sources:
      - path: "inc/"
      - path: "includes/"
      - path: "lib/"
      - path: "components/"

  # Custom post types and taxonomies
  theme-cpt:
    description: "Custom post types and taxonomies"
    group: "functionality"
    output: "m1f/10_custom_types.txt"
    sources:
      - path: "."
        includes: ["**/post-types/*.php", "**/taxonomies/*.php"]
      - path: "inc/"
        includes: ["*cpt*.php", "*custom-post*.php", "*taxonom*.php"]

  # ACF field groups
  theme-acf:
    description: "Advanced Custom Fields configuration"
    group: "functionality"
    output: "m1f/11_acf_fields.txt"
    sources:
      - path: "acf-json/" # ACF JSON exports
      - path: "."
        includes: ["**/acf-fields/*.php", "**/acf/*.php"]

  # JavaScript and build files
  theme-assets:
    description: "Theme assets and build configuration"
    group: "assets"
    output: "m1f/20_assets.txt"
    sources:
      - path: "src/"
        include_extensions: [".js", ".jsx", ".scss", ".css"]
      - path: "assets/src/"
      - path: "."
        includes:
          [
            "webpack.config.js",
            "gulpfile.js",
            "package.json",
            ".babelrc",
            "postcss.config.js",
          ]

  # WooCommerce integration
  theme-woocommerce:
    description: "WooCommerce customizations"
    group: "integrations"
    output: "m1f/30_woocommerce.txt"
    sources:
      - path: "woocommerce/"
      - path: "inc/"
        includes: ["*woocommerce*.php", "*wc-*.php"]

  # Documentation and setup
  theme-docs:
    description: "Theme documentation"
    group: "docs"
    output: "m1f/40_documentation.txt"
    sources:
      - path: "."
        includes: ["README.md", "CHANGELOG.md", "style.css"]
      - path: "docs/"

  # Quick reference for AI
  theme-quick-ref:
    description: "Essential theme files for AI context"
    group: "reference"
    output: "m1f/00_quick_reference.txt"
    max_file_size: "100KB"
    sources:
      - path: "."
        includes: ["style.css", "functions.php", "README.md", "package.json"]
```

## Documentation Site

Configuration for a documentation website using Markdown and static site
generators.

```yaml
# Documentation Site m1f Configuration

global:
  global_excludes:
    # Build outputs
    - "_site/**"
    - "public/**"
    - "dist/**"
    - ".cache/**"

    # Development
    - "**/node_modules/**"
    - "**/.sass-cache/**"
    - "**/tmp/**"

  global_settings:
    security_check: "skip" # Docs are public
    exclude_paths_file: ".gitignore"

    # Optimize for documentation
    extensions:
      .md:
        preserve_formatting: true # Keep Markdown formatting
        max_file_size: "2MB" # Allow larger docs
      .mdx:
        preserve_formatting: true
      .yml:
        minify: false # Keep YAML readable
      .json:
        minify: true

  defaults:
    force_overwrite: true
    max_file_size: "1MB"
    include_empty_dirs: false

bundles:
  # Documentation by section
  docs-getting-started:
    description: "Getting started guides"
    group: "content"
    output: "m1f/01_getting_started.txt"
    sources:
      - path: "docs/getting-started/"
      - path: "content/getting-started/"
      - path: "src/pages/docs/getting-started/"

  docs-tutorials:
    description: "Tutorial content"
    group: "content"
    output: "m1f/02_tutorials.txt"
    sources:
      - path: "docs/tutorials/"
      - path: "content/tutorials/"
      - path: "examples/"
        include_extensions: [".md", ".mdx"]

  docs-api-reference:
    description: "API documentation"
    group: "content"
    output: "m1f/03_api_reference.txt"
    sources:
      - path: "docs/api/"
      - path: "content/api/"
      - path: "reference/"

  docs-guides:
    description: "How-to guides"
    group: "content"
    output: "m1f/04_guides.txt"
    sources:
      - path: "docs/guides/"
      - path: "content/guides/"
      - path: "content/how-to/"

  # Site configuration and theming
  site-config:
    description: "Site configuration and theme"
    group: "config"
    output: "m1f/10_site_config.txt"
    sources:
      - path: "."
        includes: [
            "config*.yml",
            "config*.yaml",
            "config*.toml",
            "config*.json",
            "_config.yml", # Jekyll
            "docusaurus.config.js", # Docusaurus
            "gatsby-config.js", # Gatsby
            "mkdocs.yml", # MkDocs
            ".vuepress/config.js", # VuePress
          ]
      - path: "data/" # Data files
        include_extensions: [".yml", ".yaml", ".json"]

  # Theme and layouts
  site-theme:
    description: "Theme and layout files"
    group: "theme"
    output: "m1f/11_theme.txt"
    sources:
      - path: "_layouts/" # Jekyll
      - path: "_includes/"
      - path: "layouts/" # Hugo
      - path: "themes/"
      - path: "src/theme/"
      - path: "src/components/"
        include_extensions: [".jsx", ".tsx", ".vue", ".css", ".scss"]

  # Code examples
  docs-examples:
    description: "Code examples and snippets"
    group: "examples"
    output: "m1f/20_examples.txt"
    sources:
      - path: "examples/"
      - path: "snippets/"
      - path: "code-examples/"
      - path: "."
        includes: ["**/*.example.*", "**/examples/**"]

  # Search index and data
  site-search:
    description: "Search configuration and index"
    group: "search"
    output: "m1f/30_search.txt"
    sources:
      - path: "."
        includes: ["**/search-index.json", "**/algolia*.js", "**/lunr*.js"]
      - path: "search/"

  # Complete documentation bundle
  docs-complete:
    description: "All documentation content"
    group: "complete"
    output: "m1f/99_all_docs.txt"
    sources:
      - path: "."
        include_extensions: [".md", ".mdx"]
        excludes: ["node_modules/", "_site/", "public/"]

  # Quick reference
  docs-quick-ref:
    description: "Key documentation for AI context"
    group: "reference"
    output: "m1f/00_quick_reference.txt"
    max_file_size: "100KB"
    sources:
      - path: "."
        includes: ["README.md", "index.md", "docs/index.md"]
      - path: "docs/"
        includes: ["quick-start.md", "overview.md", "introduction.md"]
```

## Mixed Language Project

Configuration for a project with multiple programming languages (e.g., Python
backend, React frontend, Go microservices).

```yaml
# Mixed Language Project m1f Configuration

global:
  global_excludes:
    # Language-specific build artifacts
    - "**/node_modules/**" # JavaScript
    - "**/__pycache__/**" # Python
    - "**/venv/**"
    - "**/vendor/**" # Go/PHP
    - "**/target/**" # Rust/Java
    - "**/bin/**" # Binaries
    - "**/obj/**" # .NET

    # Common excludes
    - "**/dist/**"
    - "**/build/**"
    - "**/*.log"
    - "**/.cache/**"
    - "**/tmp/**"

  global_settings:
    security_check: "warn"
    exclude_paths_file: [".gitignore", ".dockerignore"]

    # Language-specific processing
    extensions:
      # Frontend
      .js:
        minify: true
        remove_comments: true
      .ts:
        minify: true
        remove_comments: true
      .jsx:
        minify: true
      .tsx:
        minify: true

      # Backend
      .py:
        remove_comments: true
        remove_docstrings: false
      .go:
        remove_comments: true
      .java:
        remove_comments: true
      .rs:
        remove_comments: true

      # Config files
      .env:
        security_check: "abort"
      .yml:
        security_check: "warn"

  defaults:
    force_overwrite: true
    max_file_size: "1MB"

bundles:
  # Frontend - React/TypeScript
  frontend-components:
    description: "Frontend React components"
    group: "frontend"
    output: "m1f/frontend/01_components.txt"
    sources:
      - path: "frontend/src/components/"
      - path: "frontend/src/hooks/"
      - path: "frontend/src/utils/"

  frontend-config:
    description: "Frontend configuration"
    group: "frontend"
    output: "m1f/frontend/02_config.txt"
    sources:
      - path: "frontend/"
        includes:
          ["package.json", "tsconfig.json", "webpack.config.js", ".eslintrc.*"]

  # Backend - Python/FastAPI
  backend-api:
    description: "Python API endpoints"
    group: "backend"
    output: "m1f/backend/01_api.txt"
    sources:
      - path: "backend/app/api/"
      - path: "backend/app/routers/"

  backend-models:
    description: "Database models and schemas"
    group: "backend"
    output: "m1f/backend/02_models.txt"
    sources:
      - path: "backend/app/models/"
      - path: "backend/app/schemas/"
      - path: "backend/app/database/"

  backend-services:
    description: "Business logic services"
    group: "backend"
    output: "m1f/backend/03_services.txt"
    sources:
      - path: "backend/app/services/"
      - path: "backend/app/core/"

  # Microservices - Go
  service-auth:
    description: "Authentication service (Go)"
    group: "microservices"
    output: "m1f/services/01_auth.txt"
    sources:
      - path: "services/auth/"
        include_extensions: [".go"]
        excludes: ["vendor/", "*_test.go"]

  service-notifications:
    description: "Notification service (Go)"
    group: "microservices"
    output: "m1f/services/02_notifications.txt"
    sources:
      - path: "services/notifications/"
        include_extensions: [".go"]
        excludes: ["vendor/", "*_test.go"]

  # Shared libraries
  shared-proto:
    description: "Protocol Buffers definitions"
    group: "shared"
    output: "m1f/shared/01_protobuf.txt"
    sources:
      - path: "proto/"
        include_extensions: [".proto"]

  shared-utils:
    description: "Shared utilities across languages"
    group: "shared"
    output: "m1f/shared/02_utils.txt"
    sources:
      - path: "shared/"
      - path: "common/"

  # Infrastructure as Code
  infrastructure:
    description: "Infrastructure configuration"
    group: "infrastructure"
    output: "m1f/infra/01_infrastructure.txt"
    sources:
      - path: "infrastructure/"
        include_extensions: [".tf", ".yml", ".yaml"]
      - path: "."
        includes: ["docker-compose*.yml", "Dockerfile*", ".dockerignore"]

  # Testing
  tests-frontend:
    description: "Frontend tests"
    group: "testing"
    output: "m1f/tests/01_frontend.txt"
    sources:
      - path: "frontend/"
        includes: ["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts"]

  tests-backend:
    description: "Backend tests"
    group: "testing"
    output: "m1f/tests/02_backend.txt"
    sources:
      - path: "backend/"
        includes: ["**/test_*.py", "**/*_test.py"]

  tests-integration:
    description: "Integration tests"
    group: "testing"
    output: "m1f/tests/03_integration.txt"
    sources:
      - path: "tests/integration/"
      - path: "e2e/"

  # Documentation
  project-docs:
    description: "Project documentation"
    group: "docs"
    output: "m1f/docs/01_documentation.txt"
    sources:
      - path: "."
        includes: ["README.md", "CONTRIBUTING.md", "ARCHITECTURE.md"]
      - path: "docs/"
      - path: "frontend/README.md"
      - path: "backend/README.md"
      - path: "services/*/README.md"

  # Quick reference bundle
  project-overview:
    description: "Project overview for AI context"
    group: "reference"
    output: "m1f/00_overview.txt"
    max_file_size: "100KB"
    sources:
      - path: "."
        includes:
          [
            "README.md",
            "docker-compose.yml",
            "frontend/package.json",
            "backend/requirements.txt",
            "services/auth/go.mod",
          ]
```

## Microservices Architecture

Configuration for a microservices-based application with multiple services.

```yaml
# Microservices Architecture m1f Configuration

global:
  global_excludes:
    # Common excludes across all services
    - "**/node_modules/**"
    - "**/vendor/**"
    - "**/target/**"
    - "**/build/**"
    - "**/dist/**"
    - "**/.cache/**"
    - "**/logs/**"
    - "**/*.log"

  global_settings:
    security_check: "abort" # Strict for microservices
    exclude_paths_file: [".gitignore", ".dockerignore"]

    # Process by file type
    extensions:
      .env:
        security_check: "abort"
      .yml:
        security_check: "warn"
      .json:
        minify: true
      .proto:
        preserve_formatting: true # Keep protobuf readable

  defaults:
    force_overwrite: true
    max_file_size: "500KB" # Smaller for services

  # Watch for changes in all services
  watcher:
    enabled: true
    debounce_seconds: 3
    ignored_paths:
      - "**/node_modules"
      - "**/vendor"
      - "**/logs"

bundles:
  # API Gateway
  gateway-main:
    description: "API Gateway service"
    group: "gateway"
    output: "m1f/gateway/01_main.txt"
    sources:
      - path: "services/gateway/"
        excludes: ["node_modules/", "dist/", "coverage/"]

  # Individual microservices
  service-users:
    description: "User management service"
    group: "services"
    output: "m1f/services/01_users.txt"
    sources:
      - path: "services/users/"
        excludes: ["vendor/", "bin/", "logs/"]

  service-orders:
    description: "Order processing service"
    group: "services"
    output: "m1f/services/02_orders.txt"
    sources:
      - path: "services/orders/"
        excludes: ["vendor/", "bin/", "logs/"]

  service-inventory:
    description: "Inventory management service"
    group: "services"
    output: "m1f/services/03_inventory.txt"
    sources:
      - path: "services/inventory/"
        excludes: ["vendor/", "bin/", "logs/"]

  service-payments:
    description: "Payment processing service"
    group: "services"
    output: "m1f/services/04_payments.txt"
    sources:
      - path: "services/payments/"
        excludes: ["vendor/", "bin/", "logs/"]

  # Shared configurations and contracts
  shared-contracts:
    description: "Service contracts and interfaces"
    group: "shared"
    output: "m1f/shared/01_contracts.txt"
    sources:
      - path: "contracts/"
        include_extensions: [".proto", ".graphql", ".openapi.yml"]
      - path: "schemas/"

  shared-libs:
    description: "Shared libraries and utilities"
    group: "shared"
    output: "m1f/shared/02_libraries.txt"
    sources:
      - path: "libs/"
      - path: "packages/"
      - path: "common/"

  # Infrastructure and deployment
  k8s-configs:
    description: "Kubernetes configurations"
    group: "infrastructure"
    output: "m1f/k8s/01_configs.txt"
    sources:
      - path: "k8s/"
        include_extensions: [".yml", ".yaml"]
      - path: "helm/"

  docker-configs:
    description: "Docker configurations"
    group: "infrastructure"
    output: "m1f/docker/01_configs.txt"
    sources:
      - path: "."
        includes: ["**/Dockerfile*", "**/.dockerignore", "docker-compose*.yml"]

  # Monitoring and observability
  monitoring:
    description: "Monitoring and alerting configs"
    group: "observability"
    output: "m1f/monitoring/01_configs.txt"
    sources:
      - path: "monitoring/"
      - path: "grafana/"
      - path: "prometheus/"

  # CI/CD pipelines
  cicd:
    description: "CI/CD pipeline definitions"
    group: "devops"
    output: "m1f/cicd/01_pipelines.txt"
    sources:
      - path: ".github/workflows/"
      - path: ".gitlab-ci.yml"
      - path: "jenkins/"
      - path: ".circleci/"

  # Service mesh configuration
  service-mesh:
    description: "Service mesh configurations"
    group: "infrastructure"
    output: "m1f/mesh/01_configs.txt"
    sources:
      - path: "istio/"
      - path: "linkerd/"
      - path: "consul/"

  # Quick overview for new developers
  architecture-overview:
    description: "Architecture overview"
    group: "reference"
    output: "m1f/00_architecture.txt"
    max_file_size: "150KB"
    sources:
      - path: "."
        includes:
          [
            "README.md",
            "ARCHITECTURE.md",
            "docker-compose.yml",
            "services/*/README.md",
          ]
```

## Mobile App Project

Configuration for a React Native or Flutter mobile application.

```yaml
# Mobile App m1f Configuration

global:
  global_excludes:
    # Platform-specific builds
    - "**/ios/build/**"
    - "**/ios/Pods/**"
    - "**/android/build/**"
    - "**/android/.gradle/**"
    - "**/android/app/build/**"

    # React Native / Flutter
    - "**/node_modules/**"
    - "**/.dart_tool/**"
    - "**/pubspec.lock"
    - "**/package-lock.json"
    - "**/yarn.lock"

    # IDE and temp files
    - "**/.idea/**"
    - "**/.vscode/**"
    - "**/tmp/**"
    - "**/*.log"

  global_settings:
    security_check: "warn"
    exclude_paths_file: [".gitignore", ".npmignore"]

    extensions:
      # Mobile-specific
      .swift:
        remove_comments: true
      .kt:
        remove_comments: true
      .dart:
        remove_comments: true
      .java:
        remove_comments: true
      # JavaScript/TypeScript
      .js:
        minify: true
      .jsx:
        minify: true
      .ts:
        minify: true
      .tsx:
        minify: true

  defaults:
    force_overwrite: true
    max_file_size: "500KB"

bundles:
  # Core application code
  app-screens:
    description: "App screens and navigation"
    group: "app"
    output: "m1f/app/01_screens.txt"
    sources:
      - path: "src/screens/" # React Native
      - path: "lib/screens/" # Flutter
      - path: "src/pages/"
      - path: "src/navigation/"

  app-components:
    description: "Reusable UI components"
    group: "app"
    output: "m1f/app/02_components.txt"
    sources:
      - path: "src/components/"
      - path: "lib/widgets/" # Flutter
      - path: "src/ui/"

  app-state:
    description: "State management"
    group: "app"
    output: "m1f/app/03_state.txt"
    sources:
      - path: "src/store/" # Redux/MobX
      - path: "src/context/" # React Context
      - path: "lib/providers/" # Flutter Provider
      - path: "lib/blocs/" # Flutter BLoC

  app-services:
    description: "API and service layer"
    group: "app"
    output: "m1f/app/04_services.txt"
    sources:
      - path: "src/services/"
      - path: "src/api/"
      - path: "lib/services/"
      - path: "src/utils/"

  # Platform-specific code
  platform-ios:
    description: "iOS specific code"
    group: "platform"
    output: "m1f/platform/01_ios.txt"
    sources:
      - path: "ios/"
        include_extensions: [".swift", ".m", ".h", ".plist"]
        excludes: ["Pods/", "build/"]

  platform-android:
    description: "Android specific code"
    group: "platform"
    output: "m1f/platform/02_android.txt"
    sources:
      - path: "android/"
        include_extensions: [".java", ".kt", ".xml", ".gradle"]
        excludes: ["build/", ".gradle/"]

  # Assets and resources
  app-assets:
    description: "App assets and resources"
    group: "assets"
    output: "m1f/assets/01_resources.txt"
    sources:
      - path: "assets/"
        includes: ["**/*.json", "**/*.xml", "**/strings.xml"]
      - path: "src/assets/"
      - path: "resources/"

  # Configuration
  app-config:
    description: "App configuration"
    group: "config"
    output: "m1f/config/01_configuration.txt"
    sources:
      - path: "."
        includes: [
            "package.json",
            "app.json", # React Native
            "metro.config.js", # React Native
            "babel.config.js",
            "tsconfig.json",
            "pubspec.yaml", # Flutter
            ".env.example",
          ]

  # Tests
  app-tests:
    description: "Test suites"
    group: "testing"
    output: "m1f/tests/01_tests.txt"
    sources:
      - path: "__tests__/"
      - path: "test/"
      - path: "src/"
        includes: ["**/*.test.js", "**/*.test.ts", "**/*.spec.js"]

  # Native modules
  native-modules:
    description: "Native modules and bridges"
    group: "native"
    output: "m1f/native/01_modules.txt"
    sources:
      - path: "src/native/"
      - path: "native-modules/"
      - path: "."
        includes: ["**/RN*.swift", "**/RN*.java", "**/RN*.kt"]

  # Quick reference
  app-quick-ref:
    description: "Key files for AI context"
    group: "reference"
    output: "m1f/00_quick_reference.txt"
    max_file_size: "100KB"
    sources:
      - path: "."
        includes:
          ["README.md", "package.json", "app.json", "src/App.js", "index.js"]
```

## Best Practices

When creating your `.m1f.config.yml`:

1. **Group Related Files**: Create focused bundles that group related
   functionality
2. **Use Meaningful Names**: Choose descriptive bundle names that indicate
   content
3. **Set Size Limits**: Keep bundles under 100KB for optimal AI performance
4. **Security First**: Always configure proper security checks for sensitive
   files
5. **Leverage Presets**: Use built-in presets for common project types
6. **Exclude Wisely**: Don't bundle generated files, dependencies, or build
   artifacts
7. **Document Purpose**: Add descriptions to help others understand each bundle
8. **Test Configuration**: Run `m1f-update` and check bundle sizes with
   `m1f-token-counter`

## Common Patterns

### Pattern 1: Separate by Layer

```yaml
bundles:
  frontend: # UI components
  backend: # Server logic
  database: # Models and migrations
  api: # API endpoints
  tests: # Test suites
```

### Pattern 2: Separate by Feature

```yaml
bundles:
  feature-auth: # Authentication
  feature-payment: # Payment processing
  feature-search: # Search functionality
  feature-admin: # Admin panel
```

### Pattern 3: Separate by Purpose

```yaml
bundles:
  quick-reference: # Essential files for context
  documentation: # All docs
  source-code: # Implementation
  configuration: # Config files
  deployment: # Deploy scripts
```

### Pattern 4: Progressive Detail

```yaml
bundles:
  overview: # High-level summary (10KB)
  core-logic: # Main functionality (50KB)
  full-source: # Complete code (100KB)
  everything: # All files (500KB)
```

Remember: The best configuration depends on your specific project needs and how
you plan to use the bundles with AI assistants.
