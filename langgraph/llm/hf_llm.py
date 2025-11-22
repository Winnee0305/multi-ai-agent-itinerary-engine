import os


class _FallbackLLM:
    """A minimal LLM-like fallback used for local testing when the real
    Hugging Face endpoint or configuration is not available.
    The `invoke` method attempts to return sensible types expected by the
    graph nodes (strings or small dicts).
    """

    def invoke(self, prompt: str):
        text = prompt.lower()
        if "rate how suitable" in text or "give a score" in text or "rate how suitable" in prompt:
            return {"score": "7", "reason": "Fallback scored by simple heuristic."}
        if "create a half-day itinerary" in text or "return json with a list of steps" in text or "itinerary" in text:
            return {"steps": [{"poi": "Sample POI", "time": "09:00-10:00", "activity": "Visit sample POI"}]}
        if "optimize this itinerary" in text or "optimized json" in text or "optimize" in text:
            return {"steps": [{"poi": "Sample POI", "time": "09:00-10:00", "activity": "Visit sample POI"}]}

        # Default: return a concise description string
        return "This is a fallback description generated locally."


def get_llm():
    """Return a configured LLM. Attempt to create a Hugging Face endpoint
    when available; fall back to a safe local stub otherwise.
    """
    try:
        # Lazy import to avoid failing the package import when not installed
        from langchain_huggingface import HuggingFaceEndpoint

        # Allow opting out of remote calls via env var
        if os.environ.get("LANGGRAPH_OFFLINE", "0") == "1":
            return _FallbackLLM()

        try:
            endpoint = HuggingFaceEndpoint(
                repo_id="mistralai/Mistral-7B-Instruct-v0.1",
                task="conversational",
                max_new_tokens=300,
                temperature=0.6,
            )

            class _SafeWrapper:
                """Wraps a real LLM endpoint and falls back to the local stub
                if any runtime error occurs during invocation.
                """

                def __init__(self, client):
                    self._client = client
                    self._fallback = _FallbackLLM()

                def invoke(self, prompt: str):
                    try:
                        # Prefer the `invoke` API used by nodes
                        if hasattr(self._client, "invoke"):
                            return self._client.invoke(prompt)
                        # Some clients implement __call__ or generate
                        if hasattr(self._client, "generate"):
                            return self._client.generate(prompt)
                        if callable(self._client):
                            return self._client(prompt)
                        return self._fallback.invoke(prompt)
                    except Exception:
                        return self._fallback.invoke(prompt)

            return _SafeWrapper(endpoint)
        except Exception:
            return _FallbackLLM()
    except Exception:
        return _FallbackLLM()
