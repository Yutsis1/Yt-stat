from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any


@dataclass
class OpenAICall:
    model: str
    input: Any
    prompt: Any


class OpenAIMock:
    """Register input -> output mappings for OpenAI response stubs."""

    def __init__(self, mapping: dict[str, str] | None = None, *, default_output: str = ""):
        self.mapping = dict(mapping or {})
        self.default_output = default_output
        self.calls: list[OpenAICall] = []

    def register(self, input_text: str, output_text: str) -> None:
        self.mapping[input_text] = output_text

    async def create(self, *, model: str, input: Any, prompt: Any):
        self.calls.append(OpenAICall(model=model, input=input, prompt=prompt))
        output_text = self.mapping.get(str(input), self.default_output)
        return SimpleNamespace(output_text=output_text)
