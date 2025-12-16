"""Claude API client wrapper."""

import anthropic
from config import settings


class LLMClient:
    """Wrapper for Anthropic Claude API."""

    MODEL = "claude-sonnet-4-5-20250929"
    MAX_TOKENS = 2048

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def generate(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: list[dict] | None = None
    ) -> str:
        """
        Generate a response from Claude.

        Args:
            user_message: The user's current message
            system_prompt: System instructions for the model
            conversation_history: Optional list of previous messages
                                  [{"role": "user"|"assistant", "content": "..."}]

        Returns:
            The assistant's response text
        """
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model=self.MODEL,
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
        Stream a response from Claude in real-time.

        Args:
            user_message: The user's current message
            system_prompt: System instructions for the model
            conversation_history: Optional list of previous messages

        Yields:
            Text tokens as they arrive from Claude
        """
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        # Stream response from Claude
        with self.client.messages.stream(
            model=self.MODEL,
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
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.generate(user_message, system_prompt)
            except anthropic.APIConnectionError as e:
                last_error = e
                if attempt < max_retries:
                    continue
            except anthropic.RateLimitError as e:
                last_error = e
                if attempt < max_retries:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            except anthropic.APIStatusError as e:
                # Don't retry on 4xx errors
                raise
        
        raise last_error
