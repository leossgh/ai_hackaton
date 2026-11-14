# Foundry Assistant (terminal)

An on-prem helper that answers Foundry questions from the docs: which workflow to use, its
inputs, the `foundry-toolkit` commands. It runs fully locally — two small models (0.5B each)
under llama.cpp, no network, no tokens. It needs no `foundry-toolkit` or Hub, so it can be
installed first and guide the rest.

## Needs

- Linux x86_64, Python 3.12+, [uv](https://docs.astral.sh/uv/)
- llama.cpp's `llama-server` (a Vulkan/CUDA build for GPU, or a CPU build)
- the two model files in `models/` (about 1 GB, not in git):
  - `qwen2.5-0.5b-goldtail-q8_0.gguf` (decision)
  - `qwen2.5-0.5b-phrase2-q8_0.gguf` (phrasing)
- about 2 GB RAM, ~2 GB disk; on GPU about 2 GB VRAM

## Run

```bash
make install
make models  LLAMA_BIN=/path/to/llama.cpp     # checks files are in place
make up      LLAMA_BIN=/path/to/llama.cpp     # model server on :8771 (GPU; add NGL=0 for CPU)
make ask Q="how do I install the foundry toolkit and log in?"
make tui                                       # interactive: /read <id>, /quit
make down
```

Answers take ~1–4 s on a GPU, ~10–35 s on CPU.

## Use your own docs

Convert any folder of Markdown into a knowledge base, then point the assistant at it:

```bash
make kb DOCS=~/my-docs NAME=mydocs EXCLUDE="CHANGELOG.md internal/*"
make ask KB=kb/mydocs/kb Q="how do I …?"
```

Subfolders become areas, `.md` files become pages, and a folder's `README.md` stands for the
folder. Each page's one-line summary (its frontmatter `description`, else its first paragraph)
is what the assistant routes on — sharpen those in `kb/mydocs/kb/*.md` if it picks the wrong page.
No retraining is needed.

## Layout

```
src/foundry_assistant/      the assistant: routing over the docs, grounding, verification,
                            the terminal client (cli.py) and the docs converter (docs_to_kb.py)
server/                     the model server: fronts the two GGUFs on one port
kb/foundry-v1/              the knowledge base (Foundry docs in OKF format)
models/                     put the two GGUFs here
```
