PYTHON ?= python
PIP ?= $(PYTHON) -m pip

ONLY ?=
CONTINUE ?=
BINDING ?=
FIXTURE ?=
VERSION ?=

.PHONY: validate test generate release package-release doctor help

help:
	@echo "Targets: validate test generate package-release release doctor"
	@echo "  make generate ONLY=am-portfolio CONTINUE=1"
	@echo "  make package-release VERSION=v1.0.0"
	@echo "  make doctor MANIFEST=../am-portfolio/observability.yaml"

validate:
	$(PYTHON) gen.py validate $(if $(BINDING),--binding $(BINDING),)

test:
	$(PYTHON) -m pytest -q

generate:
	$(PYTHON) gen.py generate \
		$(if $(ONLY),--only $(ONLY),) \
		$(if $(CONTINUE),--continue,) \
		$(if $(BINDING),--binding $(BINDING),) \
		$(if $(FIXTURE),--fixture $(FIXTURE),)

package-release:
	@test -n "$(VERSION)" || (echo "VERSION required, e.g. make package-release VERSION=v1.0.0" && exit 1)
	$(PYTHON) gen.py generate
	$(PYTHON) gen.py package-release --version $(VERSION)

release: package-release
	@echo "Artifacts in dist/release/ — upload via GitHub Release (see .github/workflows/release.yml)"

doctor:
	@test -n "$(MANIFEST)" || (echo "MANIFEST required" && exit 1)
	$(PYTHON) gen.py doctor $(MANIFEST)
