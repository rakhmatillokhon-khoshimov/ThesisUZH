# Thesis Source

Build from this directory:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
biber main
makeglossaries main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

The thesis source uses the UZH DDIS thesis class (`ddis-thesis.cls`), BibLaTeX with
`biber`, and `glossaries`. It expects these sibling folders under the repository
root:

- `assets/`
- `figures/`
- `results/analysis/`

These folders contain the exported thesis figures and generated result tables
used by `../figures/...` and `../results/analysis/...` paths in the LaTeX
source. If the thesis source is moved without those folders, it will not compile.

The repository excludes restricted prompt text, raw outputs, screenshots, and
second-coder packets. It is intended to compile the final thesis and expose the
summary-level analysis artifacts.
