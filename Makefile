ENTRY_POINT = parser/parser.py
VENV_BIN = venv/bin

install:
	python3 -m venv venv
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt

run:
	$(VENV_BIN)/python3 $(ENTRY_POINT)

debug:
	python3 -m pdb $(ENTRY_POINT)

clean:
	rm -rf __pycache__

lint:
	$(VENV_BIN)/flake8 .
	$(VENV_BIN)/mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs\
--check-untyped-defs

lint-strict:
	$(VENV_BIN)/mypy --strict


.PHONY: install run