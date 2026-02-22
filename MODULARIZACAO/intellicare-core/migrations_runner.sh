#!/bin/bash
# Migration Runner Script for IntelliCare
#
# This script helps manage database migrations using Alembic.
# Supports upgrade, downgrade, and migration info commands.
#
# Usage:
#   ./migrations_runner.sh upgrade      # Apply all pending migrations
#   ./migrations_runner.sh downgrade 1  # Revert last migration
#   ./migrations_runner.sh current       # Show current revision
#   ./migrations_runner.sh heads         # Show available revisions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/intellicare_db}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
show_help() {
    cat << EOF
${BLUE}IntelliCare Migration Runner${NC}

Usage: ./migrations_runner.sh [COMMAND] [OPTIONS]

Commands:
  upgrade [TARGET]        Apply all pending migrations (or to specific revision)
  downgrade [STEPS]       Revert N migrations (default: 1 step)
  current                 Show current database revision
  heads                   Show available migration heads
  history                 Show migration history
  branches                Show migration branches
  info    [REV]           Show info about a revision
  init                    Initialize Alembic environment (first time only)
  revision [MSG]          Create a new migration revision
  autogenerate [MSG]      Auto-generate migration from model changes

Examples:
  # Apply all pending migrations to production database
  DATABASE_URL="postgresql://user:pass@prod-host/intellicare_db" ./migrations_runner.sh upgrade

  # Revert last 2 migrations
  ./migrations_runner.sh downgrade 2

  # Create new migration with message
  ./migrations_runner.sh revision "add user roles table"

  # Show current revision
  ./migrations_runner.sh current

Environment Variables:
  DATABASE_URL     PostgreSQL connection string
                   Default: postgresql://postgres:postgres@localhost:5432/intellicare_db
  ALEMBIC_CONFIG   Path to alembic.ini
                   Default: ./alembic.ini

${YELLOW}⚠️  Always backup database before migrations!${NC}

EOF
}

# Ensure we're in the right directory
cd "$SCRIPT_DIR"

if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    upgrade)
        TARGET=${1:-head}
        echo -e "${BLUE}📦 Upgrading database to $TARGET${NC}"
        export DATABASE_URL
        alembic upgrade $TARGET
        echo -e "${GREEN}✅ Upgrade complete!${NC}"
        alembic current
        ;;
    
    downgrade)
        STEPS=${1:-1}
        echo -e "${YELLOW}⚠️  Downgrading database by $STEPS step(s)${NC}"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            export DATABASE_URL
            for ((i=0; i<STEPS; i++)); do
                alembic downgrade -1
            done
            echo -e "${GREEN}✅ Downgrade complete!${NC}"
            alembic current
        else
            echo -e "${RED}❌ Cancelled${NC}"
            exit 1
        fi
        ;;
    
    current)
        echo -e "${BLUE}📍 Current database revision:${NC}"
        export DATABASE_URL
        alembic current
        ;;
    
    heads)
        echo -e "${BLUE}📚 Available migration heads:${NC}"
        export DATABASE_URL
        alembic heads
        ;;
    
    history)
        echo -e "${BLUE}📜 Migration history:${NC}"
        export DATABASE_URL
        alembic history
        ;;
    
    branches)
        echo -e "${BLUE}🌳 Migration branches:${NC}"
        export DATABASE_URL
        alembic branches
        ;;
    
    info)
        REV=${1:-current}
        echo -e "${BLUE}ℹ️  Info about revision $REV:${NC}"
        export DATABASE_URL
        alembic show $REV
        ;;
    
    init)
        echo -e "${BLUE}🔧 Initializing Alembic environment...${NC}"
        alembic init migrations
        echo -e "${GREEN}✅ Alembic environment initialized!${NC}"
        echo "Next steps:"
        echo "  1. Configure DATABASE_URL in alembic.ini"
        echo "  2. Set target_metadata in migrations/env.py"
        echo "  3. Create first migration: ./migrations_runner.sh revision 'initial schema'"
        ;;
    
    revision)
        MESSAGE=${1:-"auto revision"}
        echo -e "${BLUE}✏️  Creating new migration: $MESSAGE${NC}"
        export DATABASE_URL
        alembic revision -m "$MESSAGE"
        echo -e "${GREEN}✅ Revision created! Edit migrations/versions/ to add migration logic.${NC}"
        ;;
    
    autogenerate)
        MESSAGE=${1:-"auto generated migration"}
        echo -e "${BLUE}🔍 Auto-generating migration: $MESSAGE${NC}"
        echo -e "${YELLOW}⚠️  Make sure target_metadata is set in migrations/env.py!${NC}"
        export DATABASE_URL
        alembic revision --autogenerate -m "$MESSAGE"
        echo -e "${GREEN}✅ Review the generated migration before running upgrade!${NC}"
        ;;
    
    -h | --help | help)
        show_help
        ;;
    
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac

exit 0
