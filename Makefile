# Build the lecture script (docu.pdf) and slides (slides.pdf).
# Requires a TeX Live installation with latexmk and pdflatex.

LATEXMK = latexmk -pdf -interaction=nonstopmode -halt-on-error

.PHONY: all script slides clean

all: script slides

script:
	$(LATEXMK) docu.tex

slides:
	$(LATEXMK) slides.tex

clean:
	latexmk -c docu.tex slides.tex
