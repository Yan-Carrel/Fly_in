VENV_BIN = venv/bin

install:
	python3 -m venv venv
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt

run:
	PYGAME_HIDE_SUPPORT_PROMPT=1 $(VENV_BIN)/python3 fly_in.py $(MAP)

debug:
	$(VENV_BIN)/python3 -m pdb fly_in.py $(MAP)

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache graph_pac/.mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

lint:
	$(VENV_BIN)/flake8 .
	$(VENV_BIN)/mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs \
--check-untyped-defs .


.PHONY: install run