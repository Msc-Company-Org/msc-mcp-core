# -*- coding: utf-8 -*-
"""Conector GitHub (leitura + escrita) escopado à entidade. Usa GITHUB_TOKEN do cofre."""
import base64
import re
import requests

from .config import GITHUB_TOKEN, ENTITY

API = "https://api.github.com"
_OWNER = ENTITY["github_owner"]
_FILTER = ENTITY.get("github_repo_filter")


def _h() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"{ENTITY['slug']}-mcp",
    }


def _match(name: str) -> bool:
    return True if not _FILTER else re.search(_FILTER, name, re.I) is not None


def _full(repo: str) -> str:
    return repo if "/" in repo else f"{_OWNER}/{repo}"


# ---------- LEITURA ----------

def list_repos(limit: int = 100) -> dict:
    """Lista os repositórios da entidade (escopados ao owner + filtro)."""
    rows, page = [], 1
    while True:
        r = requests.get(f"{API}/orgs/{_OWNER}/repos", headers=_h(),
                         params={"per_page": 100, "page": page, "sort": "pushed"}, timeout=30)
        if r.status_code == 404:
            r = requests.get(f"{API}/users/{_OWNER}/repos", headers=_h(),
                             params={"per_page": 100, "page": page, "sort": "pushed"}, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    repos = [x for x in rows if _match(x["name"])]
    return {"owner": _OWNER, "total": len(repos), "repos": [
        {"name": x["name"], "full_name": x["full_name"], "private": x["private"],
         "description": x.get("description"), "language": x.get("language"),
         "pushed_at": (x.get("pushed_at") or "")[:10], "url": x["html_url"],
         "default_branch": x.get("default_branch")} for x in repos[:limit]]}


def repo_info(repo: str) -> dict:
    r = requests.get(f"{API}/repos/{_full(repo)}", headers=_h(), timeout=30)
    if r.status_code == 404:
        return {"found": False, "repo": _full(repo)}
    r.raise_for_status()
    x = r.json()
    return {"found": True, "full_name": x["full_name"], "private": x["private"],
            "description": x.get("description"), "language": x.get("language"),
            "default_branch": x.get("default_branch"), "open_issues": x.get("open_issues_count"),
            "pushed_at": (x.get("pushed_at") or "")[:10], "url": x["html_url"]}


def read_file(repo: str, path: str, ref: str | None = None) -> dict:
    params = {"ref": ref} if ref else {}
    r = requests.get(f"{API}/repos/{_full(repo)}/contents/{path}", headers=_h(), params=params, timeout=30)
    if r.status_code == 404:
        return {"found": False, "repo": _full(repo), "path": path}
    r.raise_for_status()
    x = r.json()
    if isinstance(x, list):
        return {"found": True, "is_dir": True, "entries": [e["name"] for e in x]}
    content = base64.b64decode(x.get("content", "")).decode("utf-8", errors="replace") if x.get("encoding") == "base64" else ""
    return {"found": True, "is_dir": False, "path": path, "size": x.get("size"), "sha": x.get("sha"), "content": content}


def search_code(query: str, limit: int = 15) -> dict:
    q = f"{query} org:{_OWNER}"
    r = requests.get(f"{API}/search/code", headers=_h(), params={"q": q, "per_page": limit}, timeout=30)
    r.raise_for_status()
    x = r.json()
    items = [{"repo": i["repository"]["full_name"], "path": i["path"], "url": i["html_url"]} for i in x.get("items", [])]
    return {"query": q, "total": x.get("total_count", 0), "items": [i for i in items if _match(i["repo"].split("/")[-1])]}


def list_issues(repo: str, state: str = "open", limit: int = 30) -> dict:
    r = requests.get(f"{API}/repos/{_full(repo)}/issues", headers=_h(),
                     params={"state": state, "per_page": limit}, timeout=30)
    r.raise_for_status()
    items = [{"number": i["number"], "title": i["title"], "state": i["state"],
              "is_pr": "pull_request" in i, "url": i["html_url"]} for i in r.json()]
    return {"repo": _full(repo), "state": state, "issues": items}


# ---------- ESCRITA ----------

def create_issue(repo: str, title: str, body: str = "") -> dict:
    """Cria uma issue. AÇÃO DE ESCRITA."""
    r = requests.post(f"{API}/repos/{_full(repo)}/issues", headers=_h(),
                      json={"title": title, "body": body}, timeout=30)
    r.raise_for_status()
    x = r.json()
    return {"created": True, "number": x["number"], "url": x["html_url"]}


def comment_issue(repo: str, number: int, body: str) -> dict:
    """Comenta numa issue/PR. AÇÃO DE ESCRITA."""
    r = requests.post(f"{API}/repos/{_full(repo)}/issues/{number}/comments", headers=_h(),
                      json={"body": body}, timeout=30)
    r.raise_for_status()
    return {"created": True, "url": r.json()["html_url"]}


def put_file(repo: str, path: str, content: str, message: str, branch: str | None = None) -> dict:
    """Cria ou atualiza um arquivo (commit). AÇÃO DE ESCRITA. Detecta o sha se já existir."""
    full = _full(repo)
    params = {"ref": branch} if branch else {}
    cur = requests.get(f"{API}/repos/{full}/contents/{path}", headers=_h(), params=params, timeout=30)
    sha = cur.json().get("sha") if cur.status_code == 200 else None
    payload = {"message": message, "content": base64.b64encode(content.encode("utf-8")).decode("ascii")}
    if branch:
        payload["branch"] = branch
    if sha:
        payload["sha"] = sha
    r = requests.put(f"{API}/repos/{full}/contents/{path}", headers=_h(), json=payload, timeout=30)
    r.raise_for_status()
    x = r.json()
    return {"committed": True, "path": path, "sha": x["content"]["sha"], "commit_url": x["commit"]["html_url"]}


def list_branches(repo: str, limit: int = 50) -> dict:
    r = requests.get(f"{API}/repos/{_full(repo)}/branches", headers=_h(),
                     params={"per_page": limit}, timeout=30)
    r.raise_for_status()
    return {"repo": _full(repo), "branches": [{"name": b["name"], "sha": b["commit"]["sha"][:8],
            "protected": b.get("protected")} for b in r.json()]}


def list_commits(repo: str, branch: str | None = None, limit: int = 20) -> dict:
    params = {"per_page": limit}
    if branch:
        params["sha"] = branch
    r = requests.get(f"{API}/repos/{_full(repo)}/commits", headers=_h(), params=params, timeout=30)
    r.raise_for_status()
    return {"repo": _full(repo), "commits": [{"sha": c["sha"][:8], "message": (c["commit"]["message"] or "").splitlines()[0],
            "author": c["commit"]["author"]["name"], "date": c["commit"]["author"]["date"][:10]} for c in r.json()]}


def list_pull_requests(repo: str, state: str = "open", limit: int = 30) -> dict:
    r = requests.get(f"{API}/repos/{_full(repo)}/pulls", headers=_h(),
                     params={"state": state, "per_page": limit}, timeout=30)
    r.raise_for_status()
    return {"repo": _full(repo), "state": state, "pulls": [{"number": p["number"], "title": p["title"],
            "state": p["state"], "head": p["head"]["ref"], "base": p["base"]["ref"], "url": p["html_url"]} for p in r.json()]}


def create_branch(repo: str, new_branch: str, from_branch: str | None = None) -> dict:
    """[ESCRITA] Cria uma branch a partir de outra (default = branch padrão do repo)."""
    full = _full(repo)
    if not from_branch:
        from_branch = repo_info(repo).get("default_branch", "main")
    ref = requests.get(f"{API}/repos/{full}/git/ref/heads/{from_branch}", headers=_h(), timeout=30)
    ref.raise_for_status()
    sha = ref.json()["object"]["sha"]
    r = requests.post(f"{API}/repos/{full}/git/refs", headers=_h(),
                      json={"ref": f"refs/heads/{new_branch}", "sha": sha}, timeout=30)
    r.raise_for_status()
    return {"created": True, "branch": new_branch, "from": from_branch, "sha": sha[:8]}


def create_pull_request(repo: str, title: str, head: str, base: str | None = None, body: str = "") -> dict:
    """[ESCRITA] Abre um Pull Request (head → base). base default = branch padrão."""
    full = _full(repo)
    if not base:
        base = repo_info(repo).get("default_branch", "main")
    r = requests.post(f"{API}/repos/{full}/pulls", headers=_h(),
                      json={"title": title, "head": head, "base": base, "body": body}, timeout=30)
    if r.status_code >= 400:
        return {"created": False, "status": r.status_code, "error": r.json().get("message"),
                "errors": r.json().get("errors")}
    x = r.json()
    return {"created": True, "number": x["number"], "url": x["html_url"]}
