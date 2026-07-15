PYTHON ?= python
PIP ?= $(PYTHON) -m pip

ONLY ?=
CONTINUE ?=
BINDING ?=
FIXTURE ?=

.PHONY: validate test generate release help

help:
	@echo "Targets: validate test generate release"
	@echo "  make generate ONLY=am-portfolio CONTINUE=1"

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

release:
	@mkdir -p dist
	@echo "Packaging dist/ artifacts"
	@test -d dist/grafana && echo "grafana artifacts present" || echo "run make generate first"
