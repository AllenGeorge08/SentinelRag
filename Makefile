PYTHON := venv/bin/python
PYTHONPATH := $(CURDIR)/app:$(CURDIR)

.PHONY: test evaluate ingest

test:
	PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m pytest tests/

evaluate:
	PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m app.evaluation.evaluate

ingest:
	PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m app.rag.ingestion.index
