.PHONY: thesis clean check-public

thesis:
	cd thesis_draft && pdflatex main.tex && pdflatex main.tex

clean:
	find thesis_draft -type f \( -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.toc' -o -name '*.lof' -o -name '*.lot' -o -name '*.nav' -o -name '*.snm' \) -delete

check-public:
	! find . -path '*screenshots_private*' -o -path '*/responses/*' -o -name '.env' -o -iname '*private*' | grep .
