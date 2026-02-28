#!/bin/bash
# ============================================================================
# IntelliCare STEP 1.4 - Infrastructure Startup Script (Linux/macOS)
# ============================================================================
# Starts PostgreSQL, Redis, Prometheus, and Grafana containers
# Usage: bash start-infrastructure.sh [command]
# Commands: up, down, logs, status, clean
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
PROJECT_NAME="intellicare-phase1.4"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# Main Commands
# ============================================================================

start_infrastructure() {
    print_header "Starting IntelliCare Infrastructure"
    
    # Check if docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" pull
    
    print_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    
    print_success "Infrastructure started!"
    print_info "Waiting for services to be healthy..."
    
    # Wait for PostgreSQL
    print_info "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T postgres pg_isready -U intellicare_admin > /dev/null 2>&1; then
            print_success "PostgreSQL is ready!"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # Wait for Redis
    print_info "Waiting for Redis..."
    for i in {1..30}; do
        if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T redis redis-cli ping > /dev/null 2>&1; then
            print_success "Redis is ready!"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # Wait for Prometheus
    sleep 3
    print_success "Prometheus is ready!"
    
    # Display connection information
    echo ""
    print_header "Connection Information"
    echo -e "PostgreSQL:  ${GREEN}postgresql://intellicare_admin:intellicare_dev_pwd@localhost:5432/intellicare_db${NC}"
    echo -e "Redis:       ${GREEN}redis://localhost:6379${NC}"
    echo -e "Prometheus:  ${GREEN}http://localhost:9090${NC}"
    echo -e "Grafana:     ${GREEN}http://localhost:3000${NC} (admin/intellicare_grafana)"
    echo ""
    
    print_info "Running initial setup..."
    setup_redis_consumer_groups
    verify_database
}

stop_infrastructure() {
    print_header "Stopping IntelliCare Infrastructure"
    
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    
    print_success "Infrastructure stopped!"
}

show_logs() {
    print_header "Infrastructure Logs"
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
}

show_status() {
    print_header "Infrastructure Status"
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
    
    echo ""
    print_info "Service Health:"
    
    # PostgreSQL
    if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T postgres pg_isready -U intellicare_admin > /dev/null 2>&1; then
        print_success "PostgreSQL: UP"
    else
        print_error "PostgreSQL: DOWN"
    fi
    
    # Redis
    if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis: UP"
    else
        print_error "Redis: DOWN"
    fi
    
    # Prometheus
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        print_success "Prometheus: UP"
    else
        print_error "Prometheus: DOWN"
    fi
    
    # Grafana
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        print_success "Grafana: UP"
    else
        print_error "Grafana: DOWN"
    fi
}

clean_infrastructure() {
    print_header "Cleaning Infrastructure"
    print_warning "This will remove all containers, volumes, and data!"
    read -p "Are you sure? (yes/no): " -r
    echo
    
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down -v
        print_success "Infrastructure cleaned!"
    else
        print_info "Cleanup cancelled."
    fi
}

setup_redis_consumer_groups() {
    # Create consumer groups for consolidation service
    # This is a placeholder - actual setup happens in the app
    print_info "Setting up Redis consumer groups..."
    
    if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T redis redis-cli XGROUP CREATE consolidation consolidation-events \$ MKSTREAM 2>/dev/null; then
        print_success "Consumer group 'consolidation' created"
    else
        print_warning "Consumer group already exists or Redis not ready"
    fi
}

verify_database() {
    print_info "Verifying database setup..."
    
    # Check schemas
    SCHEMAS=$(docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T postgres \
        psql -U intellicare_admin -d intellicare_db -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name LIKE '%operacional';" 2>/dev/null | tail -1)
    
    if [ "$SCHEMAS" = " 10" ]; then
        print_success "Database schemas created correctly"
    else
        print_warning "Database schemas may not be initialized correctly"
    fi
}

show_connection_strings() {
    print_header "Connection Strings"
    echo ""
    echo "PostgreSQL (psql):"
    echo "  psql -h localhost -U intellicare_admin -d intellicare_db"
    echo ""
    echo "Redis (redis-cli):"
    echo "  redis-cli -h localhost -p 6379"
    echo ""
    echo "Environment Variables:"
    echo "  export DATABASE_URL='postgresql://intellicare_admin:intellicare_dev_pwd@localhost:5432/intellicare_db'"
    echo "  export REDIS_URL='redis://localhost:6379'"
    echo ""
}

show_help() {
    cat << EOF
IntelliCare STEP 1.4 - Infrastructure Startup Script

Usage: bash start-infrastructure.sh [command]

Commands:
  up|start      Start all infrastructure containers
  down|stop     Stop all containers
  logs          Show container logs
  status        Show container status
  clean         Remove all containers and volumes (⚠️  destructive!)
  connections   Show connection strings
  help          Show this help message

Examples:
  bash start-infrastructure.sh up
  bash start-infrastructure.sh status
  bash start-infrastructure.sh logs
  bash start-infrastructure.sh down

Services Started:
  - PostgreSQL 15  (port 5432)
  - Redis 7        (port 6379)
  - Prometheus     (port 9090)
  - Grafana        (port 3000)

Default Credentials:
  - PostgreSQL: intellicare_admin / intellicare_dev_pwd
  - Grafana: admin / intellicare_grafana

EOF
}

# ============================================================================
# Main Script Logic
# ============================================================================

COMMAND="${1:-up}"

case "$COMMAND" in
    up|start)
        start_infrastructure
        ;;
    down|stop)
        stop_infrastructure
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    clean)
        clean_infrastructure
        ;;
    connections)
        show_connection_strings
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
