# msc-mcp-core

**Código compartilhado** da família de servidores MCP da MSC.

> Este repo contém o código comum dos 4 MCPs específicos por entidade.
> Cada MCP específico (`msc-company-mcp`, `msc-labs-mcp`, etc.) aponta para este core via submodule.

## Estrutura

```
msc-mcp-core/
├── mcp_server.py       ← servidor MCP (compartilhado)
├── test_smoke.py       ← testes smoke (compartilhado)
├── connectors/
│   ├── __init__.py
│   ├── config.py       ← config de secrets (compartilhado)
│   ├── github_source.py
│   ├── hf_source.py
│   ├── drive_source.py
│   ├── vercel_source.py
│   └── supabase_source.py
├── pyproject.toml
└── requirements.txt
```

## MCPs que usam este core

| MCP | Repo | Entidade |
|-----|------|----------|
| `msc-company-mcp` | `Msc-Company-Org/msc-company-mcp` | MSC Company |
| `msc-labs-mcp` | `Msc-Company-Org/msc-labs-mcp` | MSC Labs |
| `recanto-acai-mcp` | `Msc-Company-Org/recanto-acai-mcp` | Recanto do Açaí |
| `detran-rj-mcp` | `Detran-RJ/detran-rj-mcp` | Detran-RJ |

## Para rodar localmente (desenvolvimento)

```bash
# Clone o repo da entidade
git clone https://github.com/Msc-Company-Org/msc-company-mcp.git
cd msc-company-mcp

# Adicione o core como submodule
git submodule add https://github.com/Msc-Company-Org/msc-mcp-core.git core

# Ou use symlink para desenvolvimento
ln -s ../msc-mcp-core/* .  # não faça isso em produção!
```

## Para development do core

```bash
cd msc-mcp-core
uv sync
uv run pytest
uv run python test_smoke.py
```

## Para release de nova versão do core

```bash
cd msc-mcp-core
# ... faça changes ...
git tag v0.2.0
git push origin v0.2.0
```

Depois, em cada MCP específico:
```bash
cd ../msc-company-mcp
git submodule update --remote core
git add core
git commit -m "chore: update msc-mcp-core to v0.2.0"
git push
```

## Histórico de md5 dos arquivos compartilhados

| Arquivo | md5 |
|---------|-----|
| `mcp_server.py` | `b886c91fbe444f45a9f68ce9a457948a` |
| `test_smoke.py` | `1fafb6b3854313ad3943db897e1827c4` |
