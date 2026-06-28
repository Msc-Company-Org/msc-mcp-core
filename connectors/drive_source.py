# -*- coding: utf-8 -*-
"""Conector Google Drive (leitura + criação) escopado à entidade.
Usa OAuth refresh token do cofre. Escopos disponíveis: drive.readonly (lê tudo) +
drive.file (cria/edita arquivos do próprio app). Não edita arquivos arbitrários de terceiros."""
import json
import time
import requests

from .config import (
    GOOGLE_DRIVE_CLIENT_ID as _CID,
    GOOGLE_DRIVE_CLIENT_SECRET as _CSEC,
    GOOGLE_DRIVE_REFRESH_TOKEN as _RTOK,
    ENTITY,
)

_API = "https://www.googleapis.com/drive/v3"
_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
_SCOPE_HINT = ENTITY.get("drive_scope")  # palavra-chave da entidade (ex.: "Recanto")
_FILE_FIELDS = "files(id,name,mimeType,modifiedTime,size,webViewLink,parents)"

_tok = {"value": None, "exp": 0.0}


def _access_token() -> str:
    now = time.time()
    if _tok["value"] and now < _tok["exp"] - 60:
        return _tok["value"]
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": _CID, "client_secret": _CSEC,
        "refresh_token": _RTOK, "grant_type": "refresh_token"})
    r.raise_for_status()
    j = r.json()
    _tok["value"] = j["access_token"]
    _tok["exp"] = now + j.get("expires_in", 3600)
    return _tok["value"]


def _h() -> dict:
    return {"Authorization": f"Bearer {_access_token()}"}


def _files(f):
    return [{"id": x["id"], "name": x["name"], "type": x["mimeType"].split(".")[-1],
             "mime": x["mimeType"], "modified": (x.get("modifiedTime") or "")[:10],
             "size": x.get("size"), "url": x.get("webViewLink")} for x in f]


# ---------- LEITURA ----------

def search(query: str = "", limit: int = 20, scope: bool = True) -> dict:
    """Busca arquivos por nome (name contains). Se `scope` e a entidade tem drive_scope, restringe ao tema."""
    terms = ["trashed=false"]
    if query:
        terms.append(f"name contains '{query}'")
    if scope and _SCOPE_HINT and _SCOPE_HINT.lower() not in (query or "").lower():
        terms.append(f"fullText contains '{_SCOPE_HINT}'")
    q = " and ".join(terms)
    r = requests.get(f"{_API}/files", headers=_h(), timeout=30, params={
        "q": q, "pageSize": limit, "fields": _FILE_FIELDS, "orderBy": "modifiedTime desc"})
    r.raise_for_status()
    return {"entity_scope": _SCOPE_HINT, "query": q, "files": _files(r.json().get("files", []))}


def find(name: str, limit: int = 10) -> dict:
    """Localiza arquivos/pastas por nome (útil para achar a pasta da entidade e pegar o folder id)."""
    r = requests.get(f"{_API}/files", headers=_h(), timeout=30, params={
        "q": f"name contains '{name}' and trashed=false", "pageSize": limit, "fields": _FILE_FIELDS})
    r.raise_for_status()
    return {"files": _files(r.json().get("files", []))}


def list_folder(folder_id: str, limit: int = 50) -> dict:
    """Lista os filhos diretos de uma pasta (passe o id obtido via find/search)."""
    r = requests.get(f"{_API}/files", headers=_h(), timeout=30, params={
        "q": f"'{folder_id}' in parents and trashed=false", "pageSize": limit,
        "fields": _FILE_FIELDS, "orderBy": "folder,name"})
    r.raise_for_status()
    return {"folder_id": folder_id, "files": _files(r.json().get("files", []))}


def read_file(file_id: str, max_chars: int = 20000) -> dict:
    """Lê o conteúdo textual de um arquivo. Exporta Google Docs/Sheets/Slides para texto."""
    meta = requests.get(f"{_API}/files/{file_id}", headers=_h(), timeout=30,
                        params={"fields": "id,name,mimeType,size"})
    if meta.status_code == 404:
        return {"found": False, "file_id": file_id}
    meta.raise_for_status()
    m = meta.json()
    mime = m["mimeType"]
    if mime.startswith("application/vnd.google-apps"):
        emime = ("text/csv" if "spreadsheet" in mime else "text/plain")
        r = requests.get(f"{_API}/files/{file_id}/export", headers=_h(), params={"mimeType": emime}, timeout=60)
    else:
        r = requests.get(f"{_API}/files/{file_id}", headers=_h(), params={"alt": "media"}, timeout=60)
    r.raise_for_status()
    text = r.content.decode("utf-8", errors="replace")
    return {"found": True, "name": m["name"], "mime": mime, "truncated": len(text) > max_chars,
            "content": text[:max_chars]}


# ---------- ESCRITA (drive.file: cria/edita arquivos do app) ----------

def put_text(name: str, content: str, folder_id: str | None = None) -> dict:
    """[ESCRITA] Cria um arquivo de texto no Drive (no escopo drive.file). Opcionalmente dentro de folder_id."""
    metadata = {"name": name}
    if folder_id:
        metadata["parents"] = [folder_id]
    boundary = "----driveboundary7c3f"
    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n"
        f"{content}\r\n--{boundary}--"
    ).encode("utf-8")
    r = requests.post(f"{_UPLOAD}?uploadType=multipart&fields=id,name,webViewLink",
                      headers={**_h(), "Content-Type": f"multipart/related; boundary={boundary}"},
                      data=body, timeout=60)
    r.raise_for_status()
    x = r.json()
    return {"created": True, "id": x["id"], "name": x["name"], "url": x.get("webViewLink")}
