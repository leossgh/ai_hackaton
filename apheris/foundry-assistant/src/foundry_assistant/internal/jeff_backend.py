"""Local Jeff backend: a jeff-serve `/v1/systemone` server, over the stdlib.

Jeff (github.com/firelex/jeff) is a small System One decision model served by
`jeff-serve`, with swappable LoRA adapters. It speaks the same typed
choice/score/noul wire format this app's walk already uses — `{state, questions}`
in, a probability per option out — so this adapter only translates the SDK's
Choice/Score/Noul into Jeff's request and reads its answers back. No torch and no
jeff package in this environment: it is one HTTP POST with urllib, like Jeff's own
stdlib client.
"""

from __future__ import annotations

import asyncio
import json
import os
import urllib.request
from typing import Any

from typesafe_sdk import Choice, Noul, Score

# jeff-serve rejects a Choice with more than 255 options (HTTP 422); a wide node
# (MONDO has some with ~500 children) is shortlisted first, knockout-style: each group of
# KNOCKOUT_GROUP options is asked on its own and only its winner goes on to the real question.
MAX_OPTIONS = 255
KNOCKOUT_GROUP = 50


def _wire(question: Any) -> dict[str, Any]:
    """An SDK Choice/Score/Noul as Jeff's wire question dict."""
    if isinstance(question, Choice):
        return {"type": "choice", "instructions": question.instructions,
                "criteria": question.criteria}
    if isinstance(question, Score):
        return {"type": "score", "instructions": question.instructions,
                "criteria": question.criteria}
    if isinstance(question, Noul):
        return {"type": "noul", "instructions": question.instructions}
    raise TypeError(f"unsupported question type: {type(question).__name__}")


class _Answer:
    """A Jeff answer dict as an attribute object (`.choice`, `.score`, `.noul`, …)."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.__dict__.update(data)

    def __getattr__(self, name: str) -> Any:  # keys set via __dict__; satisfies the type checker
        raise AttributeError(name)


class _Response:
    """Groups Jeff's answers by type, as walk.py reads them off the SDK response."""

    def __init__(self, answers: dict[str, dict[str, Any]]) -> None:
        wrapped = {name: _Answer(a) for name, a in answers.items()}
        self.choices = {n: a for n, a in wrapped.items() if a.type == "choice"}
        self.scores = {n: a for n, a in wrapped.items() if a.type == "score"}
        self.nouls = {n: a for n, a in wrapped.items() if a.type == "noul"}


class JeffClient:
    """Mirrors the subset of AsyncTypeSafeClient that walk.py uses, over jeff-serve."""

    def __init__(self, base_url: str, model: str, api_key: str | None = None,
                 timeout: float | None = None) -> None:
        self._url = base_url.rstrip("/") + "/v1/systemone"
        self._model = model
        self._api_key = api_key or os.environ.get("APHERIS_LOCAL_API_KEY")  # optional server auth
        # a CPU-served model can take a minute on a long passage prompt
        self._timeout = timeout or float(os.environ.get("APHERIS_LOCAL_TIMEOUT", "300"))
        # decision tokens summed over every call (incl. shortlist knockouts), when reported
        self.decision_usage: dict[str, int] = {}

    def _post(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        payload = {"model": self._model, "state": state,
                   "questions": {name: _wire(q) for name, q in questions.items()}}
        headers = {"content-type": "application/json", "accept": "application/json"}
        if self._api_key:
            headers["authorization"] = f"Bearer {self._api_key}"
        request = urllib.request.Request(
            self._url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            body: dict[str, Any] = json.loads(response.read())
        for k, v in (body.get("usage") or {}).items():
            self.decision_usage[k] = self.decision_usage.get(k, 0) + int(v)
        return body

    async def _shortlist(self, state: Any, question: Choice) -> Choice:
        """Knock a too-wide Choice down to one winner per group of KNOCKOUT_GROUP options."""
        criteria = dict(question.criteria)
        while len(criteria) > MAX_OPTIONS:
            items = list(criteria.items())
            winners: dict[str, Any] = {}
            for i in range(0, len(items), KNOCKOUT_GROUP):
                group = Choice(instructions=question.instructions,
                               criteria=dict(items[i:i + KNOCKOUT_GROUP]))
                body = await asyncio.to_thread(self._post, state, {"q": group})
                pick = body["answers"]["q"]["choice"]
                winners[pick] = criteria[pick]
            criteria = winners
        return Choice(instructions=question.instructions, criteria=criteria)

    async def system_one(self, state: Any, questions: dict[str, Any]) -> _Response:
        questions = {
            name: await self._shortlist(state, q)
            if isinstance(q, Choice) and len(q.criteria) > MAX_OPTIONS else q
            for name, q in questions.items()
        }
        body = await asyncio.to_thread(self._post, state, questions)
        return _Response(body["answers"])

    async def __aenter__(self) -> JeffClient:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False
