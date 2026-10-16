"""Leitura do arquivo de configuracao (config.yaml) do pipeline."""

from __future__ import annotations

from pathlib import Path

import yaml


def load_config(path: str | Path) -> dict:
    """Le o config.yaml e devolve um dicionario com as configuracoes."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de configuracao nao encontrado: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
