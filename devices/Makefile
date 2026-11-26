# the home's images: the five one-member images under <pkg>/build/ (served side by side, flat: metis-home's mode;
# images.golden pins their hashes, `make golden` writes it again) and the composition's under build/ (the director
# over the five, on the tick: `metisc build .`; image.golden pins its hash).
# METISC: metis-lang's metisc (default: the workspace sibling).
METISC ?= $(abspath ../../../metis-lang/src/metisc)
PACKAGES := lights air media scenes comfort timers agenda music habits glow persona

all: $(PACKAGES:%=%/build/image.txt)

# a package's image: its rules, its manifest and the shared units it includes
.SECONDEXPANSION:
%/build/image.txt: $$(wildcard $$*/*.llp) $$*/domain.yaml $(wildcard shared/*.llp)
	@mkdir -p $*/build
	$(METISC) --link $* > $@.tmp || { cat $@.tmp; rm -f $@.tmp; exit 1; }
	@mv $@.tmp $@
	@grep '^image ' $@

check:
	@for p in $(PACKAGES); do $(METISC) --link $$p --check | grep '^image '; done | diff images.golden - \
	  && echo "images.golden: the five images as pinned"

golden:
	@for p in $(PACKAGES); do $(METISC) --link $$p --check | grep '^image '; done > images.golden
	@cat images.golden

.PHONY: all check golden
