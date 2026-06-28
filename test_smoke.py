# -*- coding: utf-8 -*-
"""Smoke test (read-only) — valida config, conexão GitHub e HF da entidade.
Rodar: python test_smoke.py  (NÃO faz nenhuma escrita)."""
from connectors.config import secret_status
from connectors import github_source as gh
from connectors import hf_source as hf
from connectors import drive_source as drive
from connectors import vercel_source as vercel
from connectors import supabase_source as supa


def main():
    print("== status ==")
    print(secret_status())

    print("\n== github_repos (até 5) ==")
    r = gh.list_repos(5)
    print(f"owner={r['owner']} total={r['total']}")
    for x in r["repos"][:5]:
        print(f"  - {x['full_name']} ({x.get('language')}) {x['pushed_at']}")

    print("\n== hf_assets ==")
    a = hf.list_assets("all")
    print(f"authors={a['authors']} totals={a['totals']}")

    print("\n== drive_search (até 5) ==")
    d = drive.search(limit=5)
    print(f"scope={d['entity_scope']} achados={len(d['files'])}")
    for x in d["files"][:5]:
        print(f"  - [{x['type']}] {x['name']}")

    print("\n== vercel_projects ==")
    v = vercel.projects(10)
    print(f"filter={v['filter']} total={v['total']}")
    for p in v["projects"][:5]:
        print(f"  - {p['name']} ({p.get('state')})")

    print("\n== supabase_tables ==")
    s = supa.tables()
    print(f"tables={s['total']}: {s['tables'][:8]}" if s.get("ok") else s)

    print("\nOK — smoke read-only concluído.")


if __name__ == "__main__":
    main()
