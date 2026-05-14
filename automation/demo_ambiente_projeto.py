#!/usr/bin/env python3
"""Ambiente de demonstração do projeto python25.

Mostra:
- estrutura principal do repositório
- esquema de controle de dados
- esquema de sistemas
"""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

IGNORE_NAMES = {
    ".git",
    "__pycache__",
    "site-packages",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
}


def build_tree_structure(base: Path, max_depth: int = 2, max_items_per_dir: int = 30) -> dict[str, Any]:
    def walk(path: Path, depth: int) -> dict[str, Any]:
        node: dict[str, Any] = {"name": path.name, "type": "dir", "children": []}
        if depth >= max_depth:
            return node

        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return node

        all_visible_entries = [e for e in entries if e.name not in IGNORE_NAMES]
        visible_entries = all_visible_entries[:max_items_per_dir]
        if len(all_visible_entries) > max_items_per_dir:
            node["truncated"] = True
        for entry in visible_entries:
            if entry.is_dir():
                node["children"].append(walk(entry, depth + 1))
            else:
                node["children"].append({"name": entry.name, "type": "file"})

        return node

    return walk(base, 0)


def build_demo() -> dict[str, Any]:
    return {
        "projeto": "python25",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "ambiente": {
            "python": platform.python_version(),
            "sistema": platform.platform(),
            "raiz_projeto": str(PROJECT_ROOT),
        },
        "estrutura": build_tree_structure(PROJECT_ROOT),
        "esquema_controle_dados": {
            "descricao": "Módulos responsáveis por metadados, cache, rede e modelos.",
            "componentes": [
                {"nome": "Metadados", "caminho": "Metadados/", "papel": "Base e recursos de metadados."},
                {"nome": "Cache (Esconderijos)", "caminho": "Esconderijos/", "papel": "Controle de cache, wrappers e adaptação de armazenamento."},
                {"nome": "Network", "caminho": "Network/", "papel": "Sessão, download, autenticação e utilitários de rede."},
                {"nome": "Modelo", "caminho": "modelo/", "papel": "Representações de dados e regras de seleção/escopo."},
            ],
        },
        "esquema_sistemas": {
            "descricao": "Camadas de execução, automação, interface e segurança do projeto.",
            "componentes": [
                {"nome": "Cli", "caminho": "Cli/", "papel": "Entrada e comandos para execução em terminal."},
                {"nome": "Automação", "caminho": "automation/", "papel": "Agentes e rotinas automatizadas de manutenção."},
                {"nome": "Integração", "caminho": "n8n/workflows/", "papel": "Fluxos de integração para execução externa."},
                {"nome": "Segurança", "caminho": "segurança/ e .github/workflows/", "papel": "Consultas e pipeline de análise de segurança."},
            ],
        },
    }


def print_text(data: dict[str, Any]) -> None:
    print("Ambiente de Demonstração - python25")
    print(f"Gerado em: {data['gerado_em']}")
    print(f"Python: {data['ambiente']['python']}")
    print(f"Sistema: {data['ambiente']['sistema']}")
    print()

    print("Estrutura principal:")

    def render_tree(node: dict[str, Any], prefix: str = "") -> None:
        print(f"{prefix}- {node['name']}")
        for child in node.get("children", []):
            render_tree(child, prefix + "  ")

    render_tree(data["estrutura"])
    print()

    print("Esquema de controle de dados:")
    for item in data["esquema_controle_dados"]["componentes"]:
        print(f"- {item['nome']} ({item['caminho']}): {item['papel']}")
    print()

    print("Esquema de sistemas:")
    for item in data["esquema_sistemas"]["componentes"]:
        print(f"- {item['nome']} ({item['caminho']}): {item['papel']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera ambiente de demonstração do python25")
    parser.add_argument("--json", action="store_true", help="Mostra saída em JSON")
    args = parser.parse_args()

    data = build_demo()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_text(data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
