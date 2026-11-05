"""Provider boundary for MediSync's privacy-gated assistant.

Only the local provider is registered. Adding a network provider requires an
explicit privacy review and a new adapter; no external data egress exists here.
"""
import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Literal, Protocol, Sequence

from app.config import Settings, get_settings
from app.services.ai_assistant import Source, answer, build_context


class ProviderTransientError(RuntimeError):
    """A provider failure that may succeed on a bounded retry."""


class ProviderUnavailable(RuntimeError):
    """No provider is configured for the requested mode."""


@dataclass(frozen=True)
class LLMResult:
    content: str
    citations: list[Source]
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class LLMStreamChunk:
    text: str
    citations: list[Source]
    delivery_mode: Literal["buffered", "provider_stream"]
    output_tokens: int | None = None


class LLMProvider(Protocol):
    name: str

    async def generate(
        self,
        message: str,
        context: Sequence[dict[str, str]],
        *,
        max_output_tokens: int,
    ) -> LLMResult: ...

    def stream(
        self,
        message: str,
        context: Sequence[dict[str, str]],
        *,
        max_output_tokens: int,
    ) -> AsyncIterator[LLMStreamChunk]: ...


class LocalRulesProvider:
    name = "local_rules"

    async def generate(
        self,
        message: str,
        context: Sequence[dict[str, str]],
        *,
        max_output_tokens: int,
    ) -> LLMResult:
        del max_output_tokens  # This provider has no tokenizer or generative model.
        content, _emergency, citations = answer(message, context)
        return LLMResult(content=content, citations=citations)

    async def stream(
        self,
        message: str,
        context: Sequence[dict[str, str]],
        *,
        max_output_tokens: int,
    ) -> AsyncIterator[LLMStreamChunk]:
        del max_output_tokens
        result = await self.generate(message, context, max_output_tokens=0)
        # The deterministic local responder has no incremental generation. It
        # yields one explicitly buffered event instead of faking token deltas.
        yield LLMStreamChunk(result.content, result.citations, "buffered")


class LLMService:
    def __init__(self, settings: Settings, providers: dict[str, LLMProvider]):
        self.settings = settings
        self.providers = providers

    async def generate(
        self,
        message: str,
        context: Sequence[dict[str, str]],
    ) -> LLMResult:
        if self.settings.ai_external_calls_enabled:
            raise ProviderUnavailable("External AI is disabled pending privacy approval")
        if len(message) > 4000:
            raise ValueError("Assistant input exceeds the configured limit")
        provider = self.providers.get(self.settings.ai_provider)
        if provider is None:
            raise ProviderUnavailable("Configured AI provider is not installed")

        bounded_context = build_context(
            context,
            max_messages=self.settings.ai_context_max_messages,
            max_chars=self.settings.ai_context_max_chars,
        )
        attempts = self.settings.ai_max_retries + 1
        for attempt in range(attempts):
            try:
                result = await asyncio.wait_for(
                    provider.generate(
                        message,
                        bounded_context,
                        max_output_tokens=self.settings.ai_max_output_tokens,
                    ),
                    timeout=self.settings.ai_timeout_seconds,
                )
                if result.output_tokens is not None and result.output_tokens > self.settings.ai_max_output_tokens:
                    raise ProviderUnavailable("AI provider exceeded the configured output token limit")
                return result
            except (TimeoutError, ProviderTransientError):
                if attempt + 1 >= attempts:
                    raise
        raise ProviderUnavailable("AI provider did not return a response")

    async def stream(
        self,
        message: str,
        context: Sequence[dict[str, str]],
    ) -> AsyncIterator[LLMStreamChunk]:
        """Relay provider-native async chunks with bounded time and retries.

        Retries are allowed only before the first chunk is emitted. A failure
        after output starts is surfaced to the SSE route as a generic error.
        """
        if self.settings.ai_external_calls_enabled:
            raise ProviderUnavailable("External AI is disabled pending privacy approval")
        if len(message) > 4000:
            raise ValueError("Assistant input exceeds the configured limit")
        provider = self.providers.get(self.settings.ai_provider)
        if provider is None:
            raise ProviderUnavailable("Configured AI provider is not installed")
        bounded_context = build_context(
            context,
            max_messages=self.settings.ai_context_max_messages,
            max_chars=self.settings.ai_context_max_chars,
        )
        for attempt in range(self.settings.ai_max_retries + 1):
            emitted = False
            try:
                stream = provider.stream(
                    message,
                    bounded_context,
                    max_output_tokens=self.settings.ai_max_output_tokens,
                )
                total_chars = 0
                has_content = False
                while True:
                    try:
                        chunk = await asyncio.wait_for(
                            anext(stream), timeout=self.settings.ai_timeout_seconds
                        )
                    except StopAsyncIteration:
                        break
                    total_chars += len(chunk.text)
                    if total_chars > self.settings.ai_max_output_tokens * 32:
                        raise ProviderUnavailable("AI provider exceeded the bounded response size")
                    if chunk.output_tokens is not None and chunk.output_tokens > self.settings.ai_max_output_tokens:
                        raise ProviderUnavailable("AI provider exceeded the configured output token limit")
                    if chunk.text:
                        has_content = True
                        emitted = True
                    yield chunk
                if not has_content:
                    raise ProviderTransientError("AI provider returned an empty stream")
                return
            except (TimeoutError, ProviderTransientError):
                if emitted or attempt >= self.settings.ai_max_retries:
                    raise
        raise ProviderUnavailable("AI provider did not return a response")


def get_llm_service() -> LLMService:
    return LLMService(get_settings(), {"local_rules": LocalRulesProvider()})
