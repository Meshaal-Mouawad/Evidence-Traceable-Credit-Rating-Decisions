#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v pdflatex >/dev/null 2>&1; then
  printf '%s\n' 'pdflatex is required. Install a TeX Live or MacTeX distribution.' >&2
  exit 1
fi

# The included .bbl files retain the approved bibliography exactly.
# Rebuild these with BibTeX8 only if references.bib is intentionally edited.
for name in main reading_copy; do
  test -s "${name}.bbl"
  : > "${name}.compile.log"
  for pass in 1 2 3; do
    if ! pdflatex -interaction=nonstopmode -halt-on-error -file-line-error \
      "${name}.tex" >> "${name}.compile.log" 2>&1; then
      tail -n 45 "${name}.compile.log" >&2
      exit 1
    fi
  done
done

cp main.pdf JFRC_Anonymous_Manuscript.pdf
cp reading_copy.pdf JFRC_Complete_Reading_Copy.pdf

for name in Table_I Table_II; do
  : > "tables/${name}.compile.log"
  for pass in 1 2; do
    if ! pdflatex -interaction=nonstopmode -halt-on-error -file-line-error \
      -output-directory=tables "tables/${name}_document.tex" \
      >> "tables/${name}.compile.log" 2>&1; then
      tail -n 45 "tables/${name}.compile.log" >&2
      exit 1
    fi
  done
  cp "tables/${name}_document.pdf" "tables/${name}.pdf"
done

printf '%s\n' 'Built the complete reading copy, anonymous journal-layout manuscript, and separate tables.'
