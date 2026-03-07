"""
Research Backend Abstraction
============================

Provides a unified interface for prospect research across multiple backends:
- PerplexityBackend: Production web research via Perplexity Sonar API
- OllamaBackend: Local open-source LLM inference via Ollama
- DemoBackend: Pre-generated research data for zero-cost demo runs

Usage:
    from research_backends import get_backend

    backend = get_backend("perplexity")  # or "ollama" or "demo"
    result = backend.research(system_prompt, user_prompt)
"""

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path

import requests

from nyriom_config import (
    PERPLEXITY_API_KEY, PERPLEXITY_API_URL,
    RESEARCHER_MODEL, ENHANCER_MODEL,
    RESEARCH_RATE_LIMIT, ENHANCE_RATE_LIMIT,
    BASE_DIR,
)


class ResearchBackend(ABC):
    """Abstract base class for research backends."""

    @abstractmethod
    def research(self, system_prompt: str, user_prompt: str,
                 model_tier: str = "standard") -> dict:
        """
        Execute a research query.

        Args:
            system_prompt: System context for the model
            user_prompt: The research query
            model_tier: "standard" (sonar/small model) or "pro" (sonar-pro/large model)

        Returns:
            dict with keys:
                - "content": str (the model's response text)
                - "citations": list (source URLs, if available)
                - "error": str (if the call failed)
        """
        pass

    @abstractmethod
    def rate_limit_delay(self, model_tier: str = "standard") -> float:
        """Return the delay in seconds between API calls."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name."""
        pass

    @property
    @abstractmethod
    def supports_web_search(self) -> bool:
        """Whether this backend can search the live web."""
        pass


class PerplexityBackend(ResearchBackend):
    """Production backend using Perplexity Sonar API for web-grounded research."""

    def __init__(self):
        if not PERPLEXITY_API_KEY:
            raise ValueError(
                "PERPLEXITY_API_KEY not set. "
                "Create a .env file or use --backend demo for zero-cost runs."
            )
        self.api_key = PERPLEXITY_API_KEY
        self.call_count = 0

    @property
    def name(self) -> str:
        return "Perplexity Sonar"

    @property
    def supports_web_search(self) -> bool:
        return True

    def rate_limit_delay(self, model_tier: str = "standard") -> float:
        return ENHANCE_RATE_LIMIT if model_tier == "pro" else RESEARCH_RATE_LIMIT

    def research(self, system_prompt: str, user_prompt: str,
                 model_tier: str = "standard") -> dict:
        model = ENHANCER_MODEL if model_tier == "pro" else RESEARCHER_MODEL
        timeout = 90 if model_tier == "pro" else 60

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "return_citations": True,
        }

        try:
            response = requests.post(
                PERPLEXITY_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            self.call_count += 1
            data = response.json()

            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "{}")
            )
            citations = data.get("citations", [])

            return {"content": content, "citations": citations}

        except Exception as e:
            return {"error": str(e)}


class OllamaBackend(ResearchBackend):
    """Local LLM backend using Ollama for open-source model inference.

    Supports any model available in Ollama (e.g., mistral, llama3, qwen2.5).
    Note: Local models cannot perform web search, so research quality
    depends on the model's training data.
    """

    DEFAULT_MODEL = "mistral"
    DEFAULT_PRO_MODEL = "llama3"
    OLLAMA_URL = "http://localhost:11434/api/chat"

    def __init__(self, model: str = None, pro_model: str = None):
        self.model = model or self.DEFAULT_MODEL
        self.pro_model = pro_model or self.DEFAULT_PRO_MODEL
        self.call_count = 0
        self._verify_ollama()

    def _verify_ollama(self):
        """Check that Ollama is running and the model is available."""
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=5)
            resp.raise_for_status()
            available = [m["name"].split(":")[0] for m in resp.json().get("models", [])]
            if self.model not in available:
                print(f"  Warning: Model '{self.model}' not found in Ollama.")
                print(f"  Available: {', '.join(available) or 'none'}")
                print(f"  Run: ollama pull {self.model}")
        except requests.ConnectionError:
            raise ConnectionError(
                "Ollama is not running. Start it with: ollama serve\n"
                "Or use --backend demo for zero-cost runs."
            )

    @property
    def name(self) -> str:
        return f"Ollama ({self.model})"

    @property
    def supports_web_search(self) -> bool:
        return False

    def rate_limit_delay(self, model_tier: str = "standard") -> float:
        return 0.5  # Local inference, minimal delay

    def research(self, system_prompt: str, user_prompt: str,
                 model_tier: str = "standard") -> dict:
        model = self.pro_model if model_tier == "pro" else self.model

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        }

        try:
            response = requests.post(
                self.OLLAMA_URL,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            self.call_count += 1
            data = response.json()
            content = data.get("message", {}).get("content", "{}")
            return {"content": content, "citations": []}

        except Exception as e:
            return {"error": str(e)}


class DemoBackend(ResearchBackend):
    """Zero-cost demo backend using pre-generated research data.

    Loads bundled JSON research results so the full pipeline can run
    without any API key or external service. Useful for:
    - Portfolio demonstrations
    - Testing pipeline logic
    - CI/CD validation
    """

    DEMO_DATA_FILE = BASE_DIR / "input" / "demo_research_data.json"

    def __init__(self):
        self.call_count = 0
        self._data = {}
        if self.DEMO_DATA_FILE.exists():
            with open(self.DEMO_DATA_FILE, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            print(f"  Loaded {len(self._data)} pre-generated research entries")
        else:
            print(f"  Warning: Demo data file not found: {self.DEMO_DATA_FILE}")
            print("  Run: python generate_demo_data.py")

    @property
    def name(self) -> str:
        return "Demo (pre-generated)"

    @property
    def supports_web_search(self) -> bool:
        return False

    def rate_limit_delay(self, model_tier: str = "standard") -> float:
        return 0.05  # Near-instant, small delay for output readability

    def research(self, system_prompt: str, user_prompt: str,
                 model_tier: str = "standard") -> dict:
        self.call_count += 1

        # Extract the person/company key from the prompt
        key = self._extract_key(user_prompt)
        if key and key in self._data:
            result = self._data[key]
            return {
                "content": json.dumps(result),
                "citations": result.get("sources", []),
            }

        # Return a plausible empty result if no match
        return {
            "content": json.dumps({
                "company_type": "NOT_FOUND",
                "program_count": "NOT_FOUND",
                "region_focus": "NOT_FOUND",
                "lightweighting_programs": "NOT_FOUND",
                "sustainability_initiatives": "NOT_FOUND",
                "production_scale": "NOT_FOUND",
                "linkedin_url": "NOT_FOUND",
                "materials_adoption_role": "NOT_FOUND",
                "current_material_suppliers": "NOT_FOUND",
                "rd_budget": "NOT_FOUND",
                "material_spec_influence": "NOT_FOUND",
                "recent_acquisitions": "NOT_FOUND",
                "bio_materials_interest": "NOT_FOUND",
            }),
            "citations": [],
        }

    def _extract_key(self, prompt: str) -> str:
        """Extract a lookup key from the research prompt.

        Matches patterns like: "First Last" at "Company Name"
        """
        import re
        # Try to find quoted name and company
        name_match = re.search(r'"([^"]+?)\s+([^"]+?)".*?"([^"]+?)"', prompt)
        if name_match:
            # Could be "Company" and "First Last" or vice versa
            # The research prompt format is: company then person
            pass

        # Simpler: look for person pattern
        person_match = re.search(
            r'(?:person\s+)?"(\w+)\s+(\w+)".*?(?:at|company)\s+"([^"]+)"',
            prompt, re.IGNORECASE
        )
        if person_match:
            first, last, company = person_match.groups()
            return f"{first}|{last}|{company}"

        # Try company + person pattern (used in step2)
        cp_match = re.search(
            r'company\s+"([^"]+)".*?person\s+"(\w+)\s+(\w+)"',
            prompt, re.IGNORECASE
        )
        if cp_match:
            company, first, last = cp_match.groups()
            return f"{first}|{last}|{company}"

        # Fallback: look for any two quoted strings
        quotes = re.findall(r'"([^"]+)"', prompt)
        if len(quotes) >= 2:
            # Usually company is first, then full name
            parts = quotes[1].split()
            if len(parts) >= 2:
                return f"{parts[0]}|{parts[-1]}|{quotes[0]}"

        return None


def get_backend(backend_name: str, **kwargs) -> ResearchBackend:
    """Factory function to create the appropriate research backend.

    Args:
        backend_name: One of "perplexity", "ollama", or "demo"
        **kwargs: Additional arguments passed to the backend constructor

    Returns:
        A ResearchBackend instance
    """
    backends = {
        "perplexity": PerplexityBackend,
        "ollama": OllamaBackend,
        "demo": DemoBackend,
    }

    if backend_name not in backends:
        raise ValueError(
            f"Unknown backend '{backend_name}'. "
            f"Available: {', '.join(backends.keys())}"
        )

    return backends[backend_name](**kwargs)
