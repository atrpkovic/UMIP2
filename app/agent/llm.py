"""Hyperbolic API client wrapper for Llama models."""

from openai import OpenAI
from config import settings


class LLMClient:
    """Wrapper for Hyperbolic API (OpenAI-compatible) with Llama models."""

    MAX_TOKENS = 2048

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.hyperbolic_api_key,
            base_url="https://api.hyperbolic.xyz/v1"
        )
        self.model = settings.llm_model

    def generate(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None
    ) -> str:
        """
        Generate a response from Llama via Hyperbolic.

        Args:
            user_message: The user's current message
            system_prompt: System instructions for the model
            conversation_history: Optional list of previous messages
                                  [{"role": "user"|"assistant", "content": "..."}]

        Returns:
            The assistant's response text
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            messages=messages
        )

        return response.choices[0].message.content

    def generate_stream(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None
    ):
        """
        Stream a response from Llama via Hyperbolic in real-time.

        Args:
            user_message: The user's current message
            system_prompt: System instructions for the model
            conversation_history: Optional list of previous messages

        Yields:
            Text tokens as they arrive from Llama
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        # Stream response from Hyperbolic
        stream = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            messages=messages,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
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
