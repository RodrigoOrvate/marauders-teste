PYTHON = python3
GUI = marauders_gui.py
BIN = /usr/local/bin/marauders

run:
	@$(PYTHON) $(GUI)

install:
	@echo "#!/bin/bash" > marauders_cmd
	@echo "cd $(PWD) && $(PYTHON) $(GUI)" >> marauders_cmd
	@chmod +x marauders_cmd
	@sudo mv marauders_cmd $(BIN)
	@echo "✅ Agora você pode abrir o programa digitando apenas: marauders"

uninstall:
	@sudo rm -f $(BIN)
