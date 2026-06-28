# -*- coding: utf-8 -*-
"""Conector Supabase (somente leitura) escopado à entidade, via PostgREST.
Ativo só quando a entidade define `supabase_env_prefix` e há creds no cofre
(ex.: SUPABASE_URL_DETRAN + SUPABASE_SERVICE_DETRAN). DB de produção → sem escrita por padrão."""
import requests

from .config import supabase_creds

_C = supabase_creds()


def _h() -> dict:
    return {"apikey": _C["key"], "Authorization": f"Bearer {_C['key']}"}


def _na() -> dict:
    return {"configured": False, "msg": "Supabase não configurado para esta entidade (sem supabase_env_prefix/creds)."}


def tables() -> dict:
    """Lista as tabelas expostas pelo PostgREST do projeto Supabase da entidade."""
    if not _C:
        return _na()
    try:
        r = requests.get(f"{_C['url']}/rest/v1/", headers={**_h(), "Accept": "application/openapi+json"}, timeout=20)
    except requests.exceptions.RequestException as e:
        return {"configured": True, "ok": False, "error": f"conexão falhou (projeto pausado/offline?): {type(e).__name__}"}
    if r.status_code in (401, 403):
        return {"configured": True, "ok": False, "status": r.status_code,
                "hint": "introspecção de schema exige service key (secreta); a anon key só permite supabase_select de tabelas conhecidas."}
    if r.status_code >= 400:
        return {"configured": True, "ok": False, "status": r.status_code, "error": r.text[:200]}
    defs = list((r.json().get("definitions") or {}).keys())
    return {"configured": True, "ok": True, "url": _C["url"], "total": len(defs), "tables": defs}


def select(table: str, columns: str = "*", limit: int = 20, order: str | None = None) -> dict:
    """Lê linhas de uma tabela (PostgREST). `columns` ex.: 'id,nome'; `order` ex.: 'created_at.desc'."""
    if not _C:
        return _na()
    params = {"select": columns, "limit": limit}
    if order:
        params["order"] = order
    try:
        r = requests.get(f"{_C['url']}/rest/v1/{table}", headers=_h(), params=params, timeout=20)
    except requests.exceptions.RequestException as e:
        return {"configured": True, "ok": False, "error": f"conexão falhou (projeto pausado/offline?): {type(e).__name__}"}
    if r.status_code >= 400:
        return {"configured": True, "ok": False, "status": r.status_code, "error": r.text[:200]}
    rows = r.json()
    return {"configured": True, "ok": True, "table": table, "count": len(rows), "rows": rows}
