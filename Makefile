# Build the lecture script (docu.pdf) and slides (slides.pdf).
# Requires a TeX Live installation with latexmk and pdflatex.

LATEXMK = latexmk -pdf -interaction=nonstopmode -halt-on-error

.PHONY: all script slides publish clean

all: script slides

script:
	$(LATEXMK) docu.tex

slides:
	$(LATEXMK) slides.tex

# Copy the built PDFs into pdf/, the versioned copies linked from README.md
publish: all
	cp docu.pdf pdf/EmbeddedComputing_Script.pdf
	cp slides.pdf pdf/EmbeddedComputing_Slides.pdf

clean:
	latexmk -c docu.tex slides.tex
