#!/bin/bash
set -e

echo "============================================================================"
echo "Clean Clone from Git - Branch: staging"
echo "============================================================================"
echo ""

# Config
GIT_REPO=""  # Deixe vazio para detectar automaticamente ou coloque a URL aqui
BRANCH="staging"
TARGET_DIR="/opt/intellicare/intellicare"
BACKUP_DIR="/opt/intellicare/backup-before-clone-$(date +%Y%m%d-%H%M%S)"

echo "Target directory: $TARGET_DIR"
echo "Branch: $BRANCH"
echo ""

# Install git if not present
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    apt-get update -qq
    apt-get install -y -qq git
    echo "Git installed"
    echo ""
fi

# Step 1: Backup if directory exists
if [ -d "$TARGET_DIR" ]; then
    echo "Directory exists. Creating backup..."
    mkdir -p "$BACKUP_DIR"
    mv "$TARGET_DIR" "$BACKUP_DIR/"
    echo "Backup created: $BACKUP_DIR"
    echo ""
fi

# Step 2: Remove directory completely to ensure clean state
echo "Ensuring clean state..."
rm -rf "$TARGET_DIR"
echo "Clean state ensured"
echo ""

# Step 3: Clone from Git
echo "Cloning from Git (branch: $BRANCH)..."
echo ""

# Detect Git URL if not provided
if [ -z "$GIT_REPO" ]; then
    # Try to get from remote if backup exists
    if [ -d "$BACKUP_DIR/intellicare/.git" ]; then
        GIT_REPO=$(cd "$BACKUP_DIR/intellicare" && git remote get-url origin 2>/dev/null || echo "")
        if [ -n "$GIT_REPO" ]; then
            echo "Detected Git URL from backup: $GIT_REPO"
        fi
    fi
fi

# If still empty, ask user
if [ -z "$GIT_REPO" ]; then
    echo "Could not detect Git URL automatically."
    echo "Please enter your Git repository URL:"
    echo "Example: https://github.com/usuario/intellicare.git"
    echo "         git@github.com:usuario/intellicare.git"
    read -p "Git URL: " GIT_REPO
fi

if [ -z "$GIT_REPO" ]; then
    echo "ERROR: Git URL is required"
    exit 1
fi

echo ""
echo "Cloning from: $GIT_REPO"
echo "Branch: $BRANCH"
echo ""

# Clone with --depth 1 for faster clone (shallow clone)
git clone --branch "$BRANCH" --single-branch --depth 1 "$GIT_REPO" "$TARGET_DIR"

if [ $? -ne 0 ]; then
    echo "ERROR: Git clone failed"
    echo "Please check:"
    echo "  1. Git URL is correct"
    echo "  2. Branch '$BRANCH' exists"
    echo "  3. You have access to the repository"
    exit 1
fi

echo ""
echo "============================================================================"
echo "Clone successful!"
echo "============================================================================"
echo ""

cd "$TARGET_DIR"

echo "Repository info:"
echo "================="
git remote -v
echo "Branch: $(git branch --show-current)"
echo "Commit: $(git log -1 --oneline)"
echo ""

echo "Contents:"
echo "========="
ls -la
echo ""

echo "Docker files:"
echo "============="
ls -la docker-compose*.yml 2>/dev/null || echo "No docker-compose files found"
echo ""

echo "============================================================================"
echo "Done! Repository cloned cleanly from Git"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "1. Review docker-compose files:"
echo "   ls -la docker-compose*.yml"
echo ""
echo "2. Build and start containers:"
echo "   docker-compose -f docker-compose.full.yml build"
echo "   docker-compose -f docker-compose.full.yml up -d"
echo ""
echo "3. Or use the clean rebuild script:"
echo "   bash scripts/server/clean_and_rebuild.sh"
echo ""
