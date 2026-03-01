#!/bin/bash
#
# IntelliCare - Environment Setup Script
# ======================================
# This script generates .env from .env.example template
# Run this after cloning from Git to create the local environment file
#

set -e

echo "============================================================================"
echo "IntelliCare - Environment Configuration Setup"
echo "============================================================================"
echo ""

TARGET_DIR="/opt/intellicare"
TEMPLATE_FILE="$TARGET_DIR/.env.example"
ENV_FILE="$TARGET_DIR/.env"
ENV_FULL_FILE="$TARGET_DIR/.env.full"

# Check if template exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "ERROR: Template file not found: $TEMPLATE_FILE"
    echo "Please ensure .env.example exists in the repository."
    exit 1
fi

echo "Template file found: $TEMPLATE_FILE"
echo ""

# Function to prompt for value with default
prompt_value() {
    local var_name="$1"
    local default_value="$2"
    local prompt_text="$3"

    if [ -n "$default_value" ] && [ "$default_value" != "CHANGE_ME" ]; then
        echo "$prompt_text [$default_value]:"
        read -r response
        echo "${response:-$default_value}"
    else
        echo "$prompt_text:"
        read -r response
        echo "${response:-$default_value}"
    fi
}

# Create .env file from template with development defaults
echo "Creating .env file with development defaults..."
echo ""

# Copy template to .env
cp "$TEMPLATE_FILE" "$ENV_FILE"

# Replace development-specific values for quick setup
sed -i 's/CHANGE_ME_SECURE_PASSWORD/intellicare_dev/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_GRAFANA_PASSWORD/admin/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_ROCKETCHAT_PASSWORD/admin/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_JITSI_SECRET/dev-secret/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_VAPID_PRIVATE_KEY/dev-vapid-private/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_VAPID_PUBLIC_KEY/dev-vapid-public/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_WHATSAPP_TOKEN/dev-whatsapp-token/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_TWILIO_SID/dev-twilio-sid/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_TWILIO_TOKEN/dev-twilio-token/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_SMTP_PASS/dev-smtp-pass/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_TAVILY_KEY/dev-tavily-key/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_KEYCLOAK_ADMIN_PASSWORD/admin/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_KEYCLOAK_CLIENT_SECRET/dev-client-secret/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_TRAEFIK_PASSWORD/admin/g' "$ENV_FILE"
sed -i 's/CHANGE_ME_CLOUDFLARE_TOKEN/''/g' "$ENV_FILE"

echo "✓ Development .env file created: $ENV_FILE"
echo ""

# Also create .env.full (same content for docker-compose)
cp "$ENV_FILE" "$ENV_FULL_FILE"
echo "✓ .env.full file created: $ENV_FULL_FILE"
echo ""

echo "============================================================================"
echo "Environment setup complete!"
echo "============================================================================"
echo ""
echo "Files created:"
echo "  - $ENV_FILE"
echo "  - $ENV_FULL_FILE"
echo ""
echo "IMPORTANT: For production deployment, update the following values:"
echo "  - All passwords (POSTGRES_PASSWORD, KEYCLOAK_*, etc.)"
echo "  - API keys (TAVILY_API_KEY, TWILIO_*, etc.)"
echo "  - Cloudflare token (CF_DNS_API_TOKEN)"
echo ""
echo "Next steps:"
echo "  1. Review the generated .env file"
echo "  2. Update sensitive values if needed"
echo "  3. Run: docker-compose -f docker-compose.full.yml up -d"
echo ""
