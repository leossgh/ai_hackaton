# Foundry Assistant — terminal client + local model server.
#
#   make install                 # Python deps into .venv (uv)
#   make models                  # check the two GGUFs + llama.cpp are in place
#   make up                      # start the model server in the background (:8771)
#   make ask Q="how do I install the foundry toolkit?"
#   make tui                     # interactive session (/read <id>, /quit)
#   make health | make down
#   make kb DOCS=~/docs NAME=mydocs   # convert Markdown docs into kb/mydocs (then KB=kb/mydocs/kb)
#
# CPU-only VM:  make up LLAMA_BIN=/opt/llama.cpp/cpu NGL=0

SHELL := /bin/bash

MODELS_DIR ?= $(CURDIR)/models
# the knowledge base to answer from (make kb writes new ones under kb/)
KB         ?= $(CURDIR)/kb/foundry-v1/kb
MODEL_PORT ?= 8771
# 99 = all layers on GPU; 0 = CPU
NGL        ?= 99
# folder containing llama.cpp's `llama-server` (Vulkan/CUDA build for GPU, CPU build otherwise)
LLAMA_BIN  ?= /opt/llama.cpp

DECIDE_GGUF := qwen2.5-0.5b-goldtail-q8_0.gguf
PHRASE_GGUF := qwen2.5-0.5b-phrase2-q8_0.gguf
RUN := $(CURDIR)/run
ENV := APHERIS_LOCAL_BASE_URL=http://127.0.0.1:$(MODEL_PORT) \
       APHERIS_LOCAL_PHRASE_URL=http://127.0.0.1:$(MODEL_PORT)/v1/chat/completions

.PHONY: install models up health down ask tui kb

install:
	uv sync

models:
	@for f in $(DECIDE_GGUF) $(PHRASE_GGUF); do \
	  test -f "$(MODELS_DIR)/$$f" && echo "ok  $$f" || { echo "MISSING  $(MODELS_DIR)/$$f"; exit 1; }; done
	@test -x "$(LLAMA_BIN)/llama-server" && echo "ok  llama-server ($(LLAMA_BIN))" \
	  || { echo "MISSING  llama-server in $(LLAMA_BIN)"; exit 1; }

up: models
	@mkdir -p "$(RUN)"
	nohup python3 server/serve_llamacpp.py --bin "$(LLAMA_BIN)" --ngl $(NGL) \
	  --port $(MODEL_PORT) --gguf "$(MODELS_DIR)" > "$(RUN)/model.log" 2>&1 & echo $$! > "$(RUN)/model.pid"
	@curl -s --retry 120 --retry-connrefused --retry-delay 1 localhost:$(MODEL_PORT)/health >/dev/null \
	  && echo "model server up on :$(MODEL_PORT)"

health:
	@curl -s localhost:$(MODEL_PORT)/health; echo

down:
	@-kill $$(cat "$(RUN)/model.pid" 2>/dev/null) 2>/dev/null && echo "model server stopped" || true
	@rm -f "$(RUN)/model.pid"

ask:
	@$(ENV) uv run foundry-ask --kb "$(KB)" "$(Q)"

tui:
	@$(ENV) uv run foundry-ask --kb "$(KB)"

kb:
	@test -n "$(DOCS)" -a -n "$(NAME)" || { echo 'usage: make kb DOCS=<docs-dir> NAME=<kb-name> [EXCLUDE="glob ..."]'; exit 1; }
	uv run foundry-assistant-kb "$(DOCS)" "$(CURDIR)/kb/$(NAME)" $(foreach g,$(EXCLUDE),--exclude '$(g)')
