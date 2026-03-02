#!/bin/bash
#
# IntelliCare - Update from Git Script
# =====================================
# This script updates the IntelliCare deployment from Git
# Uses HTTPS to avoid SSH key requirements
#

set -e

echo "============================================================================"
echo "IntelliCare - Update from Git"
echo "============================================================================"
echo ""

TARGET_DIR="/opt/intellicare"
GIT_REPO="https://github.com/egarabini/Intellicare.git"
BRANCH="staging"

# Check if directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "ERROR: Directory not found: $TARGET_DIR"
    echo "Please run clone_clean_from_git.sh first"
    exit 1
fi

echo "Target directory: $TARGET_DIR"
echo "Repository: $GIT_REPO"
echo "Branch: $BRANCH"
echo ""

cd "$TARGET_DIR"

# Step 1: Update remote URL to HTTPS (in case it was set to SSH)
echo "Updating remote URL to HTTPS..."
git remote set-url origin "$GIT_REPO" 2>/dev/null || git remote add origin "$GIT_REPO"
echo "✓ Remote URL updated"
echo ""

# Step 2: Fetch from origin
echo "Fetching from origin..."
git fetch origin
echo "✓ Fetch complete"
echo ""

# Step 3: Reset to origin/staging (clean, overwrite local changes)
echo "Resetting to origin/$BRANCH..."
git reset --hard origin/"$BRANCH"
echo "✓ Reset complete"
echo ""

# Step 4: Show current status
echo "============================================================================"
echo "Update Complete!"
echo "============================================================================"
echo ""
echo "Current status:"
echo "==============="
echo "Branch: $(git branch --show-current)"
echo "Commit: $(git log -1 --oneline)"
echo "Author: $(git log -1 --format='%an <%ae>')"
echo "Date: $(git log -1 --format='%ad')"
echo ""

# Step 5: Setup environment if needed
if [ ! -f ".env" ] || [ ! -f ".env.full" ]; then
    echo "Environment files not found. Running setup..."
    bash scripts/server/setup_env.sh
else
    echo "✓ Environment files exist"
fi

echo ""
echo "============================================================================"
echo "Next Steps:"
echo "============================================================================"
echo ""
echo "1. Review environment files (if updated):"
echo "   cat .env"
echo ""
echo "2. Stop existing containers:"
echo "   docker-compose -f docker-compose.full.yml down"
echo ""
echo "3. Rebuild and start:"
echo "   docker-compose -f docker-compose.full.yml build"
echo "   docker-compose -f docker-compose.full.yml up -d"
echo ""
echo "4. Or use the clean rebuild script:"
echo "   bash scripts/server/clean_and_rebuild.sh"
echo ""
echo "5. Check container status:"
echo "   docker ps"
echo ""

echo "============================================================================"
echo "Done! IntelliCare updated from Git"
echo "============================================================================"
