#!/bin/bash
# sync-mcps.sh - Sincroniza código do msc-mcp-core para todos os MCPs específicos
# Uso: ./sync-mcps.sh

set -e

CORE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_ROOT="$(dirname "$CORE_DIR")"

echo "🔄 Sincronizando código do msc-mcp-core..."
echo "Core: $CORE_DIR"
echo "MCP Root: $MCP_ROOT"
echo ""

FILES=("mcp_server.py" "test_smoke.py" "pyproject.toml" "requirements.txt")

sync_mcp() {
    local mcp_path="$1"
    local mcp_name=$(basename "$mcp_path")
    
    if [ ! -d "$mcp_path" ]; then
        echo "⚠️  $mcp_name não encontrado, pulando..."
        return
    fi
    
    echo "📦 Sincronizando $mcp_name..."
    
    # Copiar arquivos comuns
    for file in "${FILES[@]}"; do
        if [ -f "$CORE_DIR/$file" ]; then
            cp "$CORE_DIR/$file" "$mcp_path/$file"
        fi
    done
    
    # Sincronizar connectors
    if [ -d "$CORE_DIR/connectors" ]; then
        cp -r "$CORE_DIR/connectors/"* "$mcp_path/connectors/" 2>/dev/null || {
            mkdir -p "$mcp_path/connectors"
            cp -r "$CORE_DIR/connectors/"* "$mcp_path/connectors/"
        }
    fi
    
    echo "✅ $mcp_name sincronizado"
}

# Sincronizar todos os MCPs
sync_mcp "$MCP_ROOT/msc-company-mcp"
sync_mcp "$MCP_ROOT/msc-labs-mcp"
sync_mcp "$MCP_ROOT/recanto-acai-mcp"
sync_mcp "$MCP_ROOT/../Detran-RJ/detran-rj-mcp"

echo ""
echo "🎉 Sincronização completa!"
echo ""
echo "Para commitar as mudanças:"
echo "  cd $MCP_ROOT/msc-company-mcp && git add . && git commit -m 'chore: sync with msc-mcp-core'"
echo "  cd $MCP_ROOT/msc-labs-mcp && git add . && git commit -m 'chore: sync with msc-mcp-core'"
echo "  cd $MCP_ROOT/recanto-acai-mcp && git add . && git commit -m 'chore: sync with msc-mcp-core'"
echo "  cd $MCP_ROOT/../Detran-RJ/detran-rj-mcp && git add . && git commit -m 'chore: sync with msc-mcp-core'"
