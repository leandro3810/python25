#!/usr/bin/env python3
"""Agente de manutenção para o projeto python25.

Uso:
  python3 automation/ai_maintenance_agent.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class MaintenanceReport:
    """Resumo da saúde de manutenção do projeto.

    generated_at: timestamp UTC da geração.
    branch: branch local atual.
    pending_changes: indica alterações locais não commitadas.
    default_branch_sha: SHA do último commit da branch padrão remota (quando disponível).
    open_security_alerts: quantidade de alertas de segurança abertos no GitHub (quando disponível).
    risks: lista de riscos detectados.
    recommended_actions: lista de ações recomendadas.
    action_required: indica se é necessário atuar agora.
    """

    generated_at: str
    branch: str
    pending_changes: bool
    default_branch_sha: str | None
    open_security_alerts: int | None
    risks: list[str]
    recommended_actions: list[str]
    action_required: bool


def run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def safe_run(command: list[str]) -> str | None:
    try:
        return run(command)
    except Exception:
        return None


def get_git_branch() -> str:
    branch = safe_run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return branch or "unknown"


def has_pending_changes() -> bool:
    status = safe_run(["git", "status", "--porcelain"])
    return bool(status and status.strip())


def github_request(path: str, token: str | None) -> dict[str, Any] | list[Any] | None:
    owner = os.getenv("GH_OWNER")
    repo = os.getenv("GH_REPO")
    if not owner or not repo:
        return None
    url = f"https://api.github.com/repos/{owner}/{repo}{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "python25-ai-agent"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        print(
            f"[ai-maintenance-agent] Falha ao consultar GitHub API em {path}: {type(exc).__name__} - {exc}",
            file=sys.stderr,
        )
        return None


def collect_remote_signals() -> tuple[str | None, int | None]:
    token = os.getenv("GH_TOKEN")
    repo_info = github_request("", token)
    default_branch = None
    default_branch_sha = None
    open_security_alerts = None

    if isinstance(repo_info, dict):
        default_branch = repo_info.get("default_branch")

    if default_branch:
        branch_info = github_request(f"/branches/{default_branch}", token)
        if isinstance(branch_info, dict):
            commit = branch_info.get("commit", {})
            default_branch_sha = commit.get("sha")

    alerts = github_request("/code-scanning/alerts?state=open", token)
    if isinstance(alerts, list):
        open_security_alerts = len(alerts)

    return default_branch_sha, open_security_alerts


def create_report() -> MaintenanceReport:
    risks: list[str] = []
    actions: list[str] = []

    branch = get_git_branch()
    pending_changes = has_pending_changes()
    default_branch_sha, open_security_alerts = collect_remote_signals()

    if pending_changes:
        risks.append("Existem alterações locais pendentes.")
        actions.append("Revisar, commitar e enviar alterações validadas.")

    if open_security_alerts is not None and open_security_alerts > 0:
        risks.append(f"Existem {open_security_alerts} alertas de segurança abertos no GitHub.")
        actions.append("Priorizar correção dos alertas de segurança abertos.")

    if default_branch_sha is None:
        risks.append("Não foi possível coletar estado remoto do repositório.")
        actions.append("Configurar GH_OWNER, GH_REPO e GH_TOKEN no ambiente do n8n.")

    if not actions:
        actions.append("Nenhuma ação crítica detectada no momento.")

    return MaintenanceReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        branch=branch,
        pending_changes=pending_changes,
        default_branch_sha=default_branch_sha,
        open_security_alerts=open_security_alerts,
        risks=risks,
        recommended_actions=actions,
        action_required=len(risks) > 0,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Saída em JSON")
    args = parser.parse_args()

    report = create_report()
    data = asdict(report)

    if args.json:
        print(json.dumps(data, ensure_ascii=False))
    else:
        print("Relatório de manutenção do python25")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
