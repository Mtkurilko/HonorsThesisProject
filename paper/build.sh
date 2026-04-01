#!/bin/sh

rm -f paper.aux paper.bbl paper.blg paper.log paper.out paper.tex

# Insert appendix at the correct location
awk '
  /^# Appendix/ {
    print;
    system("cat appendix.md");
    next;
  }
  { print }
' paper-source.md > paper-source-with-appendix.md

# Generate LaTeX with crossref and bibliography
pandoc paper-source-with-appendix.md \
    --template=template.tex \
    --filter pandoc-crossref \
    --citeproc \
    --output=paper.tex \
    --natbib

pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex

rm -f paper.aux paper.bbl paper.blg paper.log paper.out paper.tex paper-source-with-appendix.md
