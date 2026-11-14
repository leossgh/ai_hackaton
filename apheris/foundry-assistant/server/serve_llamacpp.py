"""Serve apheris-local with llama.cpp: the same endpoints as serve_fused.py, no PyTorch.

Starts two `llama-server` processes, one per merged GGUF from export_gguf.py, and fronts
them with the app's wire formats:

* POST /v1/systemone        — decisions from the decision GGUF. Each option code's mean
                              log-probability is read the way serve_fused.py reads it: the
                              prompt is evaluated once (llama-server keeps it cached), then
                              each code's later tokens are scored after their prefix.
* POST /v1/chat/completions — phrasing, passed through to the phrase GGUF's server.
* GET  /props               — the phrase server's (the console reads its context size).

Needs only the standard library and llama.cpp's binaries (CPU or Vulkan build). The GGUFs
are read from `../models/` by default. Run (or use `make up`):

    python3 server/serve_llamacpp.py --bin ~/opt/llama.cpp/b11827/cpu/llama-b11827

Copied from the training repo's `training/serve_llamacpp.py`; the decision prompt format it
renders lives in `decision_format.py` and must stay identical to training.
"""

from __future__ import annotations

import argparse
import json
import math
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from decision_format import answer as _answer
from decision_format import render_decision

HERE = Path(__file__).resolve().parent
MAX_LEN = 8192  # the decision adapter's training window, as serve_fused keeps
N_PROBS = 100  # top tokens returned per position; option codes outside it get a floor


def _post(url: str, body: dict, timeout: float = 600) -> Any:
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


class _Decider:
    """Option-code probabilities from a llama-server running the merged decision GGUF."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.lock = threading.Lock()  # one slot: requests share (and reuse) its prompt cache
        self.codes: dict[int, list[int]] = {}

    def _tokens(self, text: str, special: bool) -> list[int]:
        out = _post(f"{self.url}/tokenize", {"content": text, "parse_special": special})
        return [t if isinstance(t, int) else t["id"] for t in out["tokens"]]

    def _next(self, ids: list[int]) -> dict[int, float]:
        """Log-probabilities of the top next tokens after `ids` (plain softmax of logits)."""
        out = _post(f"{self.url}/completion", {
            "prompt": ids, "n_predict": 1, "n_probs": N_PROBS, "temperature": -1,
            "cache_prompt": True})
        probs = out.get("completion_probabilities") or out["probs"]
        return {t["id"]: t["logprob"] for t in probs[0]["top_logprobs"]}

    def probs(self, content: str, n_opts: int) -> tuple[list[float], int]:
        """Option probabilities, and the prompt's token count (after truncation to MAX_LEN)."""
        text = _post(f"{self.url}/apply-template",
                     {"messages": [{"role": "user", "content": content}]})["prompt"]
        with self.lock:
            ids = self._tokens(text, special=True)[-MAX_LEN:]
            for i in range(n_opts):
                if i not in self.codes:
                    self.codes[i] = self._tokens(f"{i:02d}", special=False)
            cache = {(): self._next(ids)}  # code prefix -> next-token log-probs
            scores = []
            for i in range(n_opts):
                code, s = self.codes[i], 0.0
                for k, tok in enumerate(code):
                    prefix = tuple(code[:k])
                    if prefix not in cache:
                        cache[prefix] = self._next(ids + list(prefix))
                    top = cache[prefix]
                    s += top.get(tok, min(top.values()) - math.log(10))  # below the top-N
                scores.append(s / len(code))
        hi = max(scores)
        ex = [math.exp(x - hi) for x in scores]
        return [e / sum(ex) for e in ex], len(ids)


def _handler(decider: _Decider, phrase_url: str, layout: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, out: Any) -> None:
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(out).encode())

        def do_GET(self) -> None:  # noqa: N802  (BaseHTTPRequestHandler API)
            with urllib.request.urlopen(f"{phrase_url}{self.path}", timeout=10) as resp:
                self._send(resp.status, json.loads(resp.read()))

        def do_POST(self) -> None:  # noqa: N802
            body = json.loads(self.rfile.read(int(self.headers["content-length"])))
            try:
                if self.path.rstrip("/").endswith("systemone"):
                    answers, prompt_tokens = {}, 0
                    for name, q in body["questions"].items():
                        p = render_decision(body["state"], name, q, layout)
                        probs, n_tok = decider.probs(p.content, len(p.option_ids))
                        answers[name] = _answer(p, probs)
                        prompt_tokens += n_tok
                    out = {"answers": answers, "usage": {
                        "prompt_tokens": prompt_tokens, "completion_tokens": 0,
                        "total_tokens": prompt_tokens}}
                else:  # greedy, as serve_fused generates
                    out = _post(f"{phrase_url}/v1/chat/completions",
                                {**body, "temperature": 0.0})
                status = 200
            except Exception as err:  # noqa: BLE001  (return the error, keep serving)
                out, status = {"error": str(err)}, 500
            self._send(status, out)

        def log_message(self, *a: Any) -> None:
            pass

    return Handler


def _llama_server(bin_dir: Path, gguf: Path, port: int, ctx: int, threads: int | None,
                  ngl: int) -> subprocess.Popen:
    cmd = [str(bin_dir / "llama-server"), "-m", str(gguf), "--host", "127.0.0.1",
           "--port", str(port), "-c", str(ctx), "-np", "1", "-ngl", str(ngl)]
    if threads:
        cmd += ["-t", str(threads)]
    # The health wait below would happily accept a server some other stack already runs on this
    # port, and the decider would then score with the wrong model. Refuse instead.
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1):
            raise SystemExit(f"port {port} is already serving; pick another --port "
                             f"(this server uses --port+10 and --port+11)")
    except OSError:
        pass
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(240):  # wait for the model to load
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2):
                return proc
        except OSError:
            time.sleep(0.5)
    raise SystemExit(f"llama-server for {gguf.name} did not come up on port {port}")


def main() -> None:
    """Start the decision and phrase llama-servers and front them on --port."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bin", type=Path, required=True, help="folder with llama-server")
    ap.add_argument("--gguf", type=Path, default=HERE.parent / "models")
    ap.add_argument("--base", default="qwen2.5-0.5b", help="the decision GGUF's base")
    ap.add_argument("--decide", default="goldtail", help="decision GGUF: <base>-<this>-<quant>")
    ap.add_argument("--phrase-base", default="qwen2.5-0.5b", help="the phrase GGUF's base")
    ap.add_argument("--phrase", default="phrase2",
                    help="phrase GGUF: <phrase-base>-<this>-<quant>")
    ap.add_argument("--layout", default="tail", choices=["head", "tail"],
                    help="decision prompt layout the decide adapter was trained on")
    ap.add_argument("--quant", default="q8_0")
    ap.add_argument("--port", type=int, default=8771)
    ap.add_argument("--threads", type=int, help="llama.cpp threads (default: its own choice)")
    ap.add_argument("--ngl", type=int, default=0, help="layers on the GPU (Vulkan/CUDA builds)")
    args = ap.parse_args()
    procs = [
        _llama_server(args.bin, args.gguf / f"{args.base}-{args.decide}-{args.quant}.gguf",
                      args.port + 10, MAX_LEN + 512, args.threads, args.ngl),
        _llama_server(args.bin, args.gguf / f"{args.phrase_base}-{args.phrase}-{args.quant}.gguf",
                      args.port + 11, MAX_LEN, args.threads, args.ngl),
    ]
    print(f"serving /v1/systemone + /v1/chat/completions on 127.0.0.1:{args.port} "
          f"(llama-server on {args.port + 10}, {args.port + 11})", flush=True)
    # `kill`/systemd send SIGTERM, which by default exits without running `finally` and would
    # orphan both llama-servers; turn it into SystemExit so they are terminated below.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        ThreadingHTTPServer(("127.0.0.1", args.port), _handler(
            _Decider(f"http://127.0.0.1:{args.port + 10}"),
            f"http://127.0.0.1:{args.port + 11}", args.layout)).serve_forever()
    finally:
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    main()
