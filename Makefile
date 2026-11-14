PYTHON := $(CURDIR)/venv/bin/python
PYTHONPATH := $(CURDIR)/app:$(CURDIR)
LOG_DIR := $(CURDIR)/logs

.PHONY: test evaluate ingest worker server

test:
	PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m pytest tests/

evaluate:
	@mkdir -p $(LOG_DIR)
	@TS=$$(date +%Y%m%d-%H%M%S) && LOG_FILE="$(LOG_DIR)/run-$$TS.log" && echo "Logging evaluate run to $$LOG_FILE" && PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m app.evaluation.evaluate 2>&1 | tee "$$LOG_FILE"

ingest:
	PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m app.rag.ingestion.index

worker:
	cd app && PYTHONPATH="$(PYTHONPATH)" rq worker

server:
	cd app && PYTHONPATH="$(PYTHONPATH)" $(PYTHON) -m rag.main
