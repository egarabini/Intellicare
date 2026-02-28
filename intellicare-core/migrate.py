#!/usr/bin/env python3
"""Migration runner for IntelliCare database.

Usage:
    python migrate.py upgrade              # Apply all migrations
    python migrate.py upgrade 003          # Apply up to migration 003
    python migrate.py downgrade 001        # Revert to migration 001
    python migrate.py current              # Show current revision
    python migrate.py history              # Show migration history
    python migrate.py revision "message"   # Create new migration
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'


def print_status(message: str, status: str = "info"):
    """Print colored status message."""
    if status == "success":
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
    elif status == "error":
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}ℹ️  {message}{Colors.RESET}")


def run_alembic(args: list, db_url: str) -> int:
    """Run alembic command with database URL."""
    env = os.environ.copy()
    env['DATABASE_URL'] = db_url
    
    cmd = [sys.executable, '-m', 'alembic'] + args
    
    print(f"🔧 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="IntelliCare Database Migration Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate.py upgrade              # Apply all pending migrations
  python migrate.py upgrade 003          # Apply up to migration 003  
  python migrate.py downgrade 001        # Revert to migration 001
  python migrate.py current              # Show current database revision
  python migrate.py history              # Show migration history
  python migrate.py revision "message"   # Create new migration
        """
    )
    
    # Get database URL from environment
    db_url = os.getenv(
        'DATABASE_URL',
        'postgresql://intellicare_admin:CHANGE_ME@localhost:5432/intellicare_db'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Migration command')
    
    # Upgrade
    upgrade_parser = subparsers.add_parser('upgrade', help='Apply migrations')
    upgrade_parser.add_argument('revision', nargs='?', default='head', help='Target revision (default: head)')
    
    # Downgrade
    downgrade_parser = subparsers.add_parser('downgrade', help='Revert migrations')
    downgrade_parser.add_argument('revision', nargs='?', default='-1', help='Target revision (default: -1)')
    
    # Current
    subparsers.add_parser('current', help='Show current database revision')
    
    # History
    subparsers.add_parser('history', help='Show migration history')
    
    # Revision
    revision_parser = subparsers.add_parser('revision', help='Create new migration')
    revision_parser.add_argument('message', help='Migration description')
    
    # Heads
    subparsers.add_parser('heads', help='Show migration heads')
    
    # Branches
    subparsers.add_parser('branches', help='Show migration branches')
    
    args = parser.parse_args()
    
    # Print header
    print(f"\n{Colors.YELLOW}IntelliCare Migration Runner{Colors.RESET}")
    print("=" * 50)
    print(f"Database: {db_url}")
    if args.command:
        print(f"Command: {args.command}")
        if hasattr(args, 'revision') and args.revision:
            print(f"Revision: {args.revision}")
    print()
    
    # Execute command
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        exitcode = 0
        
        if args.command == 'upgrade':
            print_status(f"Applying migrations up to revision: {args.revision}")
            exitcode = run_alembic(['upgrade', args.revision], db_url)
        
        elif args.command == 'downgrade':
            print_status(f"Reverting migrations to revision: {args.revision}")
            exitcode = run_alembic(['downgrade', args.revision], db_url)
        
        elif args.command == 'current':
            print_status("Current database revision:")
            exitcode = run_alembic(['current'], db_url)
        
        elif args.command == 'history':
            print_status("Migration history:")
            exitcode = run_alembic(['history', '--verbose'], db_url)
        
        elif args.command == 'revision':
            print_status(f"Creating new migration: {args.message}")
            exitcode = run_alembic(['revision', '--autogenerate', '-m', args.message], db_url)
        
        elif args.command == 'heads':
            print_status("Current migration heads:")
            exitcode = run_alembic(['heads'], db_url)
        
        elif args.command == 'branches':
            print_status("Migration branches:")
            exitcode = run_alembic(['branches'], db_url)
        
        if exitcode == 0:
            print(f"\n{Colors.GREEN}Done! 🎉{Colors.RESET}\n")
        else:
            print(f"\n{Colors.RED}Migration failed with exit code {exitcode}{Colors.RESET}\n")
        
        return exitcode
        
    except KeyboardInterrupt:
        print_status("Interrupted by user", "warning")
        return 1
    except Exception as e:
        print_status(f"Error: {e}", "error")
        return 1


if __name__ == '__main__':
    sys.exit(main())

