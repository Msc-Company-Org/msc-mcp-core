# -*- coding: utf-8 -*-
"""Conector Hugging Face (leitura + escrita) escopado à entidade. Usa HF_TOKEN do cofre."""
import re
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

from .config import HF_TOKEN, ENTITY

_AUTHORS = ENTITY["hf_authors"]
_FILTER = ENTITY.get("hf_repo_filter")
_api = HfApi(token=HF_TOKEN)


def _match(repo_id: str) -> bool:
    return True if not _FILTER else re.search(_FILTER, repo_id, re.I) is not None


def _norm(items, kind):
    out = []
    for it in items:
        rid = getattr(it, "id", None) or getattr(it, "modelId", None)
        if not rid or not _match(rid):
            continue
        out.append({
            "id": rid, "kind": kind, "private": getattr(it, "private", None),
            "downloads": getattr(it, "downloads", None), "likes": getattr(it, "likes", None),
            "updated": str(getattr(it, "last_modified", "") or "")[:10],
        })
    return out


# ---------- LEITURA ----------

def list_assets(kind: str = "all") -> dict:
    """Lista models/datasets/spaces da(s) conta(s) HF da entidade. kind ∈ {all, models, datasets, spaces}."""
    res = {"authors": _AUTHORS, "models": [], "datasets": [], "spaces": []}
    for author in _AUTHORS:
        if kind in ("all", "models"):
            res["models"] += _norm(_api.list_models(author=author), "model")
        if kind in ("all", "datasets"):
            res["datasets"] += _norm(_api.list_datasets(author=author), "dataset")
        if kind in ("all", "spaces"):
            res["spaces"] += _norm(_api.list_spaces(author=author), "space")
    res["totals"] = {k: len(res[k]) for k in ("models", "datasets", "spaces")}
    return res


def asset_info(repo_id: str, repo_type: str = "model") -> dict:
    """Detalhes de um repo HF. repo_type ∈ {model, dataset, space}."""
    try:
        info = _api.repo_info(repo_id=repo_id, repo_type=repo_type)
    except Exception as e:  # noqa: BLE001
        return {"found": False, "repo_id": repo_id, "error": str(e)}
    return {"found": True, "id": repo_id, "type": repo_type,
            "private": getattr(info, "private", None), "sha": getattr(info, "sha", None),
            "siblings": [s.rfilename for s in (getattr(info, "siblings", None) or [])][:50]}


def space_runtime(repo_id: str) -> dict:
    """Estado de runtime de um Space (RUNNING/SLEEPING/PAUSED/NO_APP_FILE...)."""
    try:
        rt = _api.get_space_runtime(repo_id=repo_id)
    except Exception as e:  # noqa: BLE001
        return {"repo_id": repo_id, "error": str(e)}
    return {"repo_id": repo_id, "stage": getattr(rt, "stage", None),
            "hardware": getattr(rt, "hardware", None)}


# ---------- ESCRITA ----------

def create_repo(repo_id: str, repo_type: str = "model", private: bool = True) -> dict:
    """Cria um repo HF (model/dataset/space). AÇÃO DE ESCRITA."""
    url = _api.create_repo(repo_id=repo_id, repo_type=repo_type, private=private, exist_ok=True)
    return {"created": True, "repo_id": repo_id, "type": repo_type, "private": private, "url": str(url)}


def upload_text(repo_id: str, path_in_repo: str, content: str,
                repo_type: str = "model", message: str | None = None) -> dict:
    """Sobe/atualiza um arquivo de texto num repo HF. AÇÃO DE ESCRITA."""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / Path(path_in_repo).name
        f.write_text(content, encoding="utf-8")
        _api.upload_file(path_or_fileobj=str(f), path_in_repo=path_in_repo,
                         repo_id=repo_id, repo_type=repo_type,
                         commit_message=message or f"upload {path_in_repo}")
    return {"uploaded": True, "repo_id": repo_id, "path": path_in_repo, "type": repo_type}
