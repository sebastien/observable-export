SOURCES_PY=$(wildcard src/py/*.py)
VERSION=$(grep VERSION setup.py | cut -d'"' -f2)
MANIFEST    = $(SOURCES_PY) $(wildcard *.py AUTHORS* README* LICENSE*)
PRODUCT     = MANIFEST

.PHONY: all release clean

all: $(PRODUCT)

shell:
	@env PATH=$(realpath bin):$(PATH) PYTHONPATH=$(realpath src/py) bash

release: $(PRODUCT)
	git commit -a -m "Release $(VERSION)" ; true
	git tag $(VERSION) ; true
	git push --all ; true
	python setup.py clean sdist register upload

clean:
	@rm -rf build dist MANIFEST ; true

MANIFEST: $(MANIFEST)
	echo $(MANIFEST) | xargs -n1 | sort | uniq > $@

#EOF
