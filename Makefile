.PHONY: thesis clean check-public

MAKEGLOSSARIES := $(shell command -v makeglossaries 2>/dev/null || { test -x /usr/local/texlive/2025/bin/universal-darwin/makeglossaries && echo /usr/local/texlive/2025/bin/universal-darwin/makeglossaries; })

thesis:
	cd thesis && pdflatex -interaction=nonstopmode -halt-on-error main.tex && biber main && $(MAKEGLOSSARIES) main && pdflatex -interaction=nonstopmode -halt-on-error main.tex && pdflatex -interaction=nonstopmode -halt-on-error main.tex

clean:
	find thesis -type f \( \
		-name 'main.pdf' -o \
		-name '*.aux' -o -name '*.acn' -o -name '*.acr' -o -name '*.alg' -o \
		-name '*.bbl' -o -name '*.bcf' -o -name '*.blg' -o \
		-name '*.fdb_latexmk' -o -name '*.fls' -o \
		-name '*.glg' -o -name '*.glo' -o -name '*.gls' -o -name '*.ist' -o \
		-name '*.lof' -o -name '*.log' -o -name '*.lot' -o \
		-name '*.nav' -o -name '*.out' -o -name '*.run.xml' -o \
		-name '*.snm' -o -name '*.synctex.gz' -o -name '*.toc' \
	\) -delete
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete

check-public:
	! find . -path './.git' -prune -o \( -path './data/private*' -o -path './restricted_archive*' -o -path '*screenshots_private*' -o -path '*/responses/*' -o -name '.env' -o -iname '*private*' \) -print | grep .
