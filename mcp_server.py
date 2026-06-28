# -*- coding: utf-8 -*-
"""Servidor MCP da entidade — expõe GitHub + Hugging Face (leitura + escrita) para agentes.
A entidade é definida em entity.py. Conectores em connectors/. Rodar: python mcp_server.py (stdio).
"""
from typing import Optional

from mcp.server.fastmcp import FastMCP

from connectors import github_source as gh
from connectors import hf_source as hf
from connectors import drive_source as drive
from connectors import vercel_source as vercel
from connectors import supabase_source as supa
from connectors.config import secret_status, ENTITY

mcp = FastMCP(f"{ENTITY['slug']}-mcp")


# ===================== DIAGNÓSTICO =====================

@mcp.tool()
def status() -> dict:
    """Status do MCP: entidade ativa + presença (mascarada) dos tokens GitHub/HF. Não expõe valores."""
    return secret_status()


# ===================== GITHUB (leitura) =====================

@mcp.tool()
def github_repos(limite: int = 100) -> dict:
    """Lista os repositórios GitHub da entidade (escopados ao owner e ao filtro da entidade)."""
    return gh.list_repos(limite)


@mcp.tool()
def github_repo_info(repo: str) -> dict:
    """Detalhes de um repositório (privacidade, linguagem, branch padrão, issues, último push)."""
    return gh.repo_info(repo)


@mcp.tool()
def github_read_file(repo: str, path: str, ref: Optional[str] = None) -> dict:
    """Lê um arquivo (ou lista um diretório) de um repo. `ref` opcional = branch/tag/commit."""
    return gh.read_file(repo, path, ref)


@mcp.tool()
def github_search_code(query: str, limite: int = 15) -> dict:
    """Busca código nos repositórios da entidade (GitHub code search, escopado ao owner)."""
    return gh.search_code(query, limite)


@mcp.tool()
def github_list_issues(repo: str, state: str = "open", limite: int = 30) -> dict:
    """Lista issues/PRs de um repo. state ∈ {open, closed, all}."""
    return gh.list_issues(repo, state, limite)


# ===================== GITHUB (escrita) =====================

@mcp.tool()
def github_create_issue(repo: str, title: str, body: str = "") -> dict:
    """[ESCRITA] Cria uma issue no repositório."""
    return gh.create_issue(repo, title, body)


@mcp.tool()
def github_comment_issue(repo: str, number: int, body: str) -> dict:
    """[ESCRITA] Comenta numa issue/PR existente."""
    return gh.comment_issue(repo, number, body)


@mcp.tool()
def github_put_file(repo: str, path: str, content: str, message: str, branch: Optional[str] = None) -> dict:
    """[ESCRITA] Cria ou atualiza um arquivo (faz commit). Detecta o sha automaticamente se o arquivo já existir."""
    return gh.put_file(repo, path, content, message, branch)


@mcp.tool()
def github_list_branches(repo: str, limite: int = 50) -> dict:
    """Lista as branches de um repositório."""
    return gh.list_branches(repo, limite)


@mcp.tool()
def github_list_commits(repo: str, branch: Optional[str] = None, limite: int = 20) -> dict:
    """Lista os commits recentes de um repo (opcionalmente de uma branch)."""
    return gh.list_commits(repo, branch, limite)


@mcp.tool()
def github_list_pull_requests(repo: str, state: str = "open", limite: int = 30) -> dict:
    """Lista Pull Requests. state ∈ {open, closed, all}."""
    return gh.list_pull_requests(repo, state, limite)


@mcp.tool()
def github_create_branch(repo: str, new_branch: str, from_branch: Optional[str] = None) -> dict:
    """[ESCRITA] Cria uma branch a partir de outra (default = branch padrão)."""
    return gh.create_branch(repo, new_branch, from_branch)


@mcp.tool()
def github_create_pull_request(repo: str, title: str, head: str, base: Optional[str] = None, body: str = "") -> dict:
    """[ESCRITA] Abre um Pull Request (head → base). base default = branch padrão do repo."""
    return gh.create_pull_request(repo, title, head, base, body)


# ===================== HUGGING FACE (leitura) =====================

@mcp.tool()
def hf_assets(kind: str = "all") -> dict:
    """Lista os ativos HF da entidade. kind ∈ {all, models, datasets, spaces}."""
    return hf.list_assets(kind)


@mcp.tool()
def hf_asset_info(repo_id: str, repo_type: str = "model") -> dict:
    """Detalhes de um repo HF (arquivos, sha, privacidade). repo_type ∈ {model, dataset, space}."""
    return hf.asset_info(repo_id, repo_type)


@mcp.tool()
def hf_space_runtime(repo_id: str) -> dict:
    """Estado de runtime de um Space (RUNNING/SLEEPING/PAUSED/NO_APP_FILE)."""
    return hf.space_runtime(repo_id)


# ===================== HUGGING FACE (escrita) =====================

@mcp.tool()
def hf_create_repo(repo_id: str, repo_type: str = "model", private: bool = True) -> dict:
    """[ESCRITA] Cria um repo HF (model/dataset/space). Idempotente (exist_ok)."""
    return hf.create_repo(repo_id, repo_type, private)


@mcp.tool()
def hf_upload_text(repo_id: str, path_in_repo: str, content: str,
                   repo_type: str = "model", message: Optional[str] = None) -> dict:
    """[ESCRITA] Sobe/atualiza um arquivo de texto num repo HF."""
    return hf.upload_text(repo_id, path_in_repo, content, repo_type, message)


# ===================== GOOGLE DRIVE (leitura) =====================

@mcp.tool()
def drive_search(query: str = "", limite: int = 20) -> dict:
    """Busca arquivos no Drive por nome (restrito ao tema da entidade quando aplicável)."""
    return drive.search(query, limite)


@mcp.tool()
def drive_find(name: str, limite: int = 10) -> dict:
    """Localiza arquivos/pastas por nome (útil para descobrir o id da pasta da entidade)."""
    return drive.find(name, limite)


@mcp.tool()
def drive_list_folder(folder_id: str, limite: int = 50) -> dict:
    """Lista os filhos diretos de uma pasta do Drive (passe o id obtido via drive_find)."""
    return drive.list_folder(folder_id, limite)


@mcp.tool()
def drive_read(file_id: str, max_chars: int = 20000) -> dict:
    """Lê o conteúdo textual de um arquivo do Drive (exporta Google Docs/Sheets para texto)."""
    return drive.read_file(file_id, max_chars)


# ===================== GOOGLE DRIVE (escrita) =====================

@mcp.tool()
def drive_put_text(name: str, content: str, folder_id: Optional[str] = None) -> dict:
    """[ESCRITA] Cria um arquivo de texto no Drive (escopo drive.file). Opcionalmente dentro de uma pasta."""
    return drive.put_text(name, content, folder_id)


# ===================== VERCEL =====================

@mcp.tool()
def vercel_projects(limite: int = 100) -> dict:
    """Lista os projetos Vercel da entidade (conta pessoal + teams), filtrados pelo escopo."""
    return vercel.projects(limite)


@mcp.tool()
def vercel_deployments(project: str, team: Optional[str] = None, limite: int = 10) -> dict:
    """Últimos deployments de um projeto Vercel (por nome)."""
    return vercel.deployments(project, team, limite)


@mcp.tool()
def vercel_deployment(uid: str, team: Optional[str] = None) -> dict:
    """Detalhe de um deployment Vercel pelo uid (estado, url, target)."""
    return vercel.deployment(uid, team)


@mcp.tool()
def vercel_logs(uid: str, team: Optional[str] = None, limite: int = 50) -> dict:
    """Logs/eventos de build de um deployment Vercel."""
    return vercel.logs(uid, team, limite)


@mcp.tool()
def vercel_redeploy(uid: str, name: str, team: Optional[str] = None) -> dict:
    """[ESCRITA] Recria (redeploy) um deployment de produção a partir de um existente."""
    return vercel.redeploy(uid, name, team)


# ===================== SUPABASE (read-only, se a entidade tiver creds) =====================

@mcp.tool()
def supabase_tables() -> dict:
    """Lista as tabelas do projeto Supabase da entidade (só Detran-RJ tem creds por enquanto)."""
    return supa.tables()


@mcp.tool()
def supabase_select(table: str, columns: str = "*", limite: int = 20, order: Optional[str] = None) -> dict:
    """Lê linhas de uma tabela Supabase (PostgREST). Ex.: columns='id,nome', order='created_at.desc'."""
    return supa.select(table, columns, limite, order)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
