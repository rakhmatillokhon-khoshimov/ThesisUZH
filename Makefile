.PHONY: thesis clean check-public

thesis:
	cd thesis && pdflatex main.tex && pdflatex main.tex

clean:
	find thesis -type f \( -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.toc' -o -name '*.lof' -o -name '*.lot' -o -name '*.nav' -o -name '*.snm' \) -delete
	find slides -maxdepth 1 -type f \( -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.toc' -o -name '*.nav' -o -name '*.snm' -o -name '*.vrb' -o -name '*.fls' -o -name '*.fdb_latexmk' \) -delete
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete

check-public:
	! find . -path './.git' -prune -o \( -path './data/private*' -o -path './restricted_archive*' -o -path '*screenshots_private*' -o -path '*/responses/*' -o -name '.env' -o -iname '*private*' \) -print | grep .
