VENV_BIN = venv/bin

install:
	python3 -m venv venv
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt

run:
	$(VENV_BIN)/python3 fly_in.py

debug:
	python3 -m pdb fly_in.py

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

lint:
	$(VENV_BIN)/flake8 .
	$(VENV_BIN)/mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs\
--check-untyped-defs

lint-strict:
	$(VENV_BIN)/mypy --strict


.PHONY: install run