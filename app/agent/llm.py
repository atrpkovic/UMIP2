"""Multi-provider LLM client supporting Claude and DeepSeek."""

from openai import OpenAI
from anthropic import Anthropic
from config import settings


class LLMClient:
    """Wrapper for multiple LLM providers with unified interface."""

    MAX_TOKENS = 4096

    def __init__(self):
        # Initialize all providers
        self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
        self.hyperbolic_client = OpenAI(
            api_key=settings.hyperbolic_api_key,
            base_url="https://api.hyperbolic.xyz/v1"
        )

        # Default to current .env model
        self.current_provider = "hyperbolic"
        self.model = settings.llm_model

    def set_model(self, model_key: str, model_identifier: str):
        """
        Switch the active LLM model and provider.

        Args:
            model_key: Frontend key ('claude-sonnet', 'deepseek-v3')
            model_identifier: Actual model identifier for API
        """
        self.model = model_identifier

        # Determine provider based on model_key
        if model_key == "claude-sonnet":
            self.current_provider = "anthropic"
        elif model_key == "deepseek-v3":
            self.current_provider = "hyperbolic"

    def generate(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None
    ) -> str:
        """
        Generate a response using the currently selected LLM provider.

        Args:
            user_message: The user's current message
            system_prompt: System instructions for the model
            conversation_history: Optional list of previous messages

        Returns:
            The assistant's response text
        """
        if self.current_provider == "anthropic":
            return self._generate_anthropic(user_message, system_prompt, conversation_history)
        else:  # hyperbolic (uses OpenAI-compatible API)
            return self._generate_hyperbolic(user_message, system_prompt, conversation_history)

    def _generate_hyperbolic(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None
    ) -> str:
        """Generate using Hyperbolic API (OpenAI-compatible)."""
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        response = self.hyperbolic_client.chat.completions.create(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            messages=messages
        )

        return response.choices[0].message.content

    def _generate_anthropic(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None
    ) -> str:
        """Generate using Anthropic Claude API."""
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text

    def generate_stream(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None
    ):
        """
        Stream a response using the currently selected LLM provider.

        Args:
            user_message: The user's current message
            system_prompt: System instructions for the model
            conversation_history: Optional list of previous messages

        Yields:
            Text tokens as they arrive
        """
        if self.current_provider == "anthropic":
            yield from self._generate_stream_anthropic(user_message, system_prompt, conversation_history)
        else:  # hyperbolic
            yield from self._generate_stream_hyperbolic(user_message, system_prompt, conversation_history)

    def _generate_stream_hyperbolic(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None
    ):
        """Stream using Hyperbolic API (OpenAI-compatible)."""
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        stream = self.hyperbolic_client.chat.completions.create(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            messages=messages,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _generate_stream_anthropic(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None
    ):
        """Stream using Anthropic Claude API."""
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        with self.anthropic_client.messages.stream(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            system=system_prompt,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield text

    def generate_with_retry(
        self,
        user_message: str,
        system_prompt: str,
        max_retries: int = 2
    ) -> str:
        """Generate with automatic retry on transient failures."""
        from openai import APIConnectionError, RateLimitError, APIStatusError
        import time

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return self.generate(user_message, system_prompt)
            except APIConnectionError as e:
                last_error = e
                if attempt < max_retries:
                    continue
            except RateLimitError as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            except APIStatusError as e:
                # Don't retry on 4xx errors
                raise

        raise last_error
