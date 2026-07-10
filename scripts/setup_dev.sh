#!/usr/bin/env bash
# Autor: Emerson Antônio | Data: 2026-07-10
# Setup do ambiente de desenvolvimento GIFI Predict
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3.12}"
if ! command -v "$PYTHON" &>/dev/null; then
  echo "ERRO: $PYTHON não encontrado. Instale Python 3.12 ou defina PYTHON=..."
  exit 1
fi

echo "==> Python: $($PYTHON --version)"
echo "==> Criando venv em .venv"
"$PYTHON" -m venv .venv

# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Atualizando pip"
pip install -U pip wheel setuptools

echo "==> Instalando pacote editable com extras dev"
pip install -e ".[dev]"

if command -v uv &>/dev/null; then
  echo "==> Gerando uv.lock e requirements*.txt"
  uv lock
  uv export --no-dev -o requirements.txt
  uv export --extra dev -o requirements-dev.txt
else
  echo "AVISO: uv não encontrado — pule lock file ou instale: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

echo ""
echo "Setup concluído. Ative o ambiente:"
echo "  source .venv/bin/activate"
echo ""
echo "Validação rápida:"
echo "  pytest tests/ -q -m 'not slow'"
echo "  ruff check src/ tests/"
