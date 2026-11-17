#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
for command in pdflatex bibtex8; do
  command -v "$command" >/dev/null || { echo "Missing TeX command: $command" >&2; exit 1; }
done
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex8 main
for pass in 1 2 3; do pdflatex -interaction=nonstopmode -halt-on-error main.tex; done
for name in Table_I Table_II; do
  for pass in 1 2; do
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=tables "tables/${name}_document.tex"
  done
done
