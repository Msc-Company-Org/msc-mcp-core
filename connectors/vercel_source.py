# -*- coding: utf-8 -*-
"""Conector Vercel (leitura + redeploy) escopado à entidade. Usa VERCEL_TOKEN do cofre.
Varre a conta pessoal + todos os teams acessíveis (o token do cofre pode estar numa conta
sem projetos; os deploys de produção ficam no team finish-him-1996s-projects)."""
import re
import requests

from .config import VERCEL_TOKEN, ENTITY

_API = "https://api.vercel.com"
_FILTER = ENTITY.get("vercel_filter") or ENTITY.get("slug")


def _h() -> dict:
    return {"Authorization": f"Bearer {VERCEL_TOKEN}"}


def _match(name: str) -> bool:
    return True if not _FILTER else re.search(_FILTER, name, re.I) is not None


def _teams() -> list:
    try:
        r = requests.get(f"{_API}/v2/teams", headers=_h(), timeout=30)
        r.raise_for_status()
        return [{"id": t["id"], "slug": t.get("slug")} for t in r.json().get("teams", [])]
    except Exception:  # noqa: BLE001
        return []


def _scopes() -> list:
    # None = conta pessoal; depois cada team
    return [None] + [t["id"] for t in _teams()]


# ---------- LEITURA ----------

def projects(limit: int = 100) -> dict:
    """Lista projetos Vercel da entidade (conta pessoal + teams), filtrados pelo escopo da entidade."""
    found = []
    for team in _scopes():
        params = {"limit": 100}
        if team:
            params["teamId"] = team
        try:
            r = requests.get(f"{_API}/v9/projects", headers=_h(), params=params, timeout=30)
            if r.status_code != 200:
                continue
            for p in r.json().get("projects", []):
                if _match(p["name"]):
                    latest = (p.get("latestDeployments") or [{}])[0]
                    found.append({"name": p["name"], "team": team, "framework": p.get("framework"),
                                  "url": (latest.get("url") if latest else None),
                                  "state": (latest.get("readyState") if latest else None)})
        except Exception:  # noqa: BLE001
            continue
    return {"filter": _FILTER, "total": len(found), "projects": found[:limit]}


def deployments(project: str, team: str | None = None, limit: int = 10) -> dict:
    """Últimos deployments de um projeto (por nome). Passe team se o projeto estiver num team."""
    params = {"app": project, "limit": limit}
    if team:
        params["teamId"] = team
    r = requests.get(f"{_API}/v6/deployments", headers=_h(), params=params, timeout=30)
    r.raise_for_status()
    return {"project": project, "deployments": [
        {"uid": d["uid"], "state": d.get("readyState") or d.get("state"), "url": d.get("url"),
         "target": d.get("target"), "created": d.get("createdAt")} for d in r.json().get("deployments", [])]}


def deployment(uid: str, team: str | None = None) -> dict:
    """Detalhe de um deployment pelo uid."""
    params = {"teamId": team} if team else {}
    r = requests.get(f"{_API}/v13/deployments/{uid}", headers=_h(), params=params, timeout=30)
    if r.status_code == 404:
        return {"found": False, "uid": uid}
    r.raise_for_status()
    d = r.json()
    return {"found": True, "uid": uid, "name": d.get("name"), "state": d.get("readyState"),
            "url": d.get("url"), "target": d.get("target"), "creator": (d.get("creator") or {}).get("username")}


def logs(uid: str, team: str | None = None, limit: int = 50) -> dict:
    """Eventos/logs de build de um deployment."""
    params = {"limit": limit}
    if team:
        params["teamId"] = team
    r = requests.get(f"{_API}/v3/deployments/{uid}/events", headers=_h(), params=params, timeout=30)
    if r.status_code != 200:
        return {"uid": uid, "error": r.status_code}
    out = []
    for e in (r.json() if isinstance(r.json(), list) else []):
        txt = e.get("text") or (e.get("payload") or {}).get("text")
        if txt:
            out.append(txt)
    return {"uid": uid, "lines": out[-limit:]}


# ---------- ESCRITA ----------

def redeploy(uid: str, name: str, team: str | None = None) -> dict:
    """[ESCRITA] Recria um deployment a partir de um existente (redeploy)."""
    params = {"teamId": team} if team else {}
    r = requests.post(f"{_API}/v13/deployments", headers=_h(), params=params,
                      json={"deploymentId": uid, "name": name, "target": "production"}, timeout=60)
    if r.status_code >= 400:
        return {"created": False, "status": r.status_code, "error": r.json().get("error")}
    d = r.json()
    return {"created": True, "uid": d.get("id"), "url": d.get("url"), "state": d.get("readyState")}
