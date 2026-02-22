#!/bin/bash
############################################################################
# NISE TRAINING MODULE - FLOWISE + OLLAMA SETUP SCRIPT
############################################################################
# Projeto: NISE - Treinamento Assistido
# Módulo: Script de setup para Flowise + Ollama
# Versão: 1.0
# Data: 11/03/2026
# Responsável: DEV2
############################################################################

set -e

echo "============================================================================"
echo "NISE TRAINING MODULE - FLOWISE + OLLAMA SETUP"
echo "============================================================================"
echo ""

# ============================================================================
# STEP 1: Check Docker
# ============================================================================
echo "📦 Step 1: Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found! Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found! Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# ============================================================================
# STEP 2: Create directories
# ============================================================================
echo "📁 Step 2: Creating directories..."
mkdir -p flowise/storage
mkdir -p flowise/logs
mkdir -p ollama/models
echo "✅ Directories created"
echo ""

# ============================================================================
# STEP 3: Copy environment file
# ============================================================================
echo "⚙️  Step 3: Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.flowise.example .env
    echo "✅ .env file created from template"
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi
echo ""

# ============================================================================
# STEP 4: Start services
# ============================================================================
echo "🚀 Step 4: Starting Flowise + Ollama services..."
docker-compose -f docker-compose.flowise.yml up -d
echo "✅ Services started"
echo ""

# ============================================================================
# STEP 5: Wait for services
# ============================================================================
echo "⏳ Step 5: Waiting for services to be ready..."
echo "   Waiting for Ollama..."
sleep 10

# Check Ollama
until docker exec nise-ollama ollama list &> /dev/null; do
    echo "   Ollama not ready yet, waiting..."
    sleep 5
done
echo "✅ Ollama is ready"

echo "   Waiting for Flowise..."
sleep 10

# Check Flowise
until curl -s http://localhost:3000/api/v1/health &> /dev/null; do
    echo "   Flowise not ready yet, waiting..."
    sleep 5
done
echo "✅ Flowise is ready"
echo ""

# ============================================================================
# STEP 6: Download Ollama models
# ============================================================================
echo "📥 Step 6: Downloading Ollama models..."
echo "   This may take several minutes depending on your internet connection..."
echo ""

# Download llama2:7b (general purpose)
echo "   Downloading llama2:7b (general purpose)..."
docker exec nise-ollama ollama pull llama2:7b
echo "✅ llama2:7b downloaded"
echo ""

# Optional: Download medical models (commented out - uncomment if needed)
# echo "   Downloading meditron:7b (medical specialist)..."
# docker exec nise-ollama ollama pull meditron:7b
# echo "✅ meditron:7b downloaded"
# echo ""

echo "✅ Models downloaded"
echo ""

# ============================================================================
# STEP 7: Test Ollama
# ============================================================================
echo "🧪 Step 7: Testing Ollama..."
docker exec nise-ollama ollama run llama2:7b "Hello, this is a test. Respond with 'OK' if you can read this." --verbose=false
echo "✅ Ollama test completed"
echo ""

# ============================================================================
# STEP 8: Display access information
# ============================================================================
echo "============================================================================"
echo "🎉 FLOWISE + OLLAMA SETUP COMPLETED!"
echo "============================================================================"
echo ""
echo "📊 Access Information:"
echo "   - Flowise UI: http://localhost:3000"
echo "   - Flowise API: http://localhost:3000/api/v1"
echo "   - Ollama API: http://localhost:11434"
echo ""
echo "🔐 Flowise Credentials:"
echo "   - Username: admin"
echo "   - Password: admin123"
echo "   (Change in .env file)"
echo ""
echo "🤖 Ollama Models:"
echo "   - llama2:7b (general purpose) ✅"
echo ""
echo "📝 Next Steps:"
echo "   1. Access Flowise UI at http://localhost:3000"
echo "   2. Login with credentials above"
echo "   3. Create your first chatflow"
echo "   4. Configure Ollama integration"
echo "   5. Test RAG with NISE knowledge base"
echo ""
echo "🛠️  Useful Commands:"
echo "   - View logs: docker-compose -f docker-compose.flowise.yml logs -f"
echo "   - Stop services: docker-compose -f docker-compose.flowise.yml down"
echo "   - Restart services: docker-compose -f docker-compose.flowise.yml restart"
echo "   - List Ollama models: docker exec nise-ollama ollama list"
echo ""
echo "============================================================================"

