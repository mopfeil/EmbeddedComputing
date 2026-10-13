# Build the lecture script (docu.pdf) and slides (slides.pdf).
# Requires a TeX Live installation with latexmk and lualatex.
# The RWU font Barlow Semi Condensed is shipped in fonts/ and needs lualatex;
# "make PDFTEX=1" builds with pdflatex and Latin Modern instead.

ifdef PDFTEX
LATEXMK = latexmk -pdf -interaction=nonstopmode -halt-on-error
else
LATEXMK = latexmk -lualatex -interaction=nonstopmode -halt-on-error
endif

.PHONY: all script slides worksheet publish clean

all: script slides

script:
	$(LATEXMK) docu.tex

slides:
	$(LATEXMK) slides.tex

# Worksheet "GPIO output stages" (Falstad circuits in examples/interfaces/falstad):
# student version and a version with solutions
worksheet:
	$(LATEXMK) Worksheet_IO_Ports.tex
	$(LATEXMK) -jobname=Worksheet_IO_Ports_Solutions -usepretex='\def\solutions{}' Worksheet_IO_Ports.tex

# Copy the built PDFs into pdf/, the versioned copies linked from README.md
publish: all
	cp docu.pdf pdf/EmbeddedComputing_Script.pdf
	cp slides.pdf pdf/EmbeddedComputing_Slides.pdf

clean:
	latexmk -c docu.tex slides.tex Worksheet_IO_Ports.tex
	latexmk -c -jobname=Worksheet_IO_Ports_Solutions Worksheet_IO_Ports.tex
