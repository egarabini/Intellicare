#!/bin/bash
# Clone IntelliCare from Git

echo "Cloning IntelliCare from Git..."
echo ""

# Install git if not present
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    apt-get install -y git
fi

# Go to parent directory
cd /opt/intellicare

# Clone repository
echo "Cloning repository..."
git clone https://github.com/seu-usuario/intellicare.git intellicare

# Or if you have a specific Git repository URL, replace above with:
# git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git intellicare

cd intellicare

echo ""
echo "Repository cloned!"
echo ""
echo "Next steps:"
echo "1. Copy docker-compose files to correct location"
echo "2. Build and start containers"
