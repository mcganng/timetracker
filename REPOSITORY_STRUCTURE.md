# Repository Structure

## Directory Naming

This repository uses slightly different directory names than the deployed application:

| Git Repository | Deployed Location | Purpose |
|---------------|-------------------|---------|
| `templates_git/` | `/opt/timetracker/templates/` | HTML Jinja2 templates |
| `database_git/` | `/opt/timetracker/database/` | Database schema SQL |
| `static/` | `/opt/timetracker/static/` | Static CSS/JS files |

### Why the different names?

The production `templates/` and `database/` directories have restricted permissions (mode `drwx-wS---`) for security.
To allow the repository to be cloned and committed to without permission issues, we use `*_git/` naming in the repository.

### Installation

The `install.sh` script automatically handles this:

```bash
# When you run install.sh, it:
# 1. Creates the proper directories
mkdir -p /opt/timetracker/templates /opt/timetracker/database

# 2. Copies files from the repository
cp -r templates_git/* /opt/timetracker/templates/
cp -r database_git/* /opt/timetracker/database/

# 3. Sets correct permissions
chown -R timetracker:timetracker /opt/timetracker
```

### Development Workflow

When making changes to templates or database schema:

1. **Edit the files** in `/opt/timetracker/templates/` (production) using the Admin Code Editor UI
2. **Copy changes back** to the git repository:
   ```bash
   sudo cp /opt/timetracker/templates/file.html /path/to/repo/templates_git/
   sudo cp /opt/timetracker/database/schema.sql /path/to/repo/database_git/
   ```
3. **Commit and push** the changes from `templates_git/` and `database_git/`

### Alternative: Update install.sh

If you prefer to use standard `templates/` and `database/` names in git, you can:

1. Rename the directories:
   ```bash
   git mv templates_git templates
   git mv database_git database
   ```

2. Update `.gitignore` to allow these directories:
   ```bash
   # Remove from .gitignore if they were excluded
   ```

3. On your development machine, set permissive permissions:
   ```bash
   chmod -R 755 templates/ database/
   ```

This works fine for development, but production systems should maintain strict permissions for security.
