import time
import httpx
from llm.providers.base import BaseProvider

class OpenAICompatibleProvider(BaseProvider):
    """
    Unified client for all OpenAI-compatible endpoints (Groq, Cerebras, OpenRouter, Together, Ollama, OpenAI).
    """
    def __init__(self, base_url: str, api_key: str, provider_name: str = "openai_compatible"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.provider_name = provider_name

    async def generate(
        self,
        model_name: str,
        prompt: str,
        system_instruction: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_format: bool = False,
        timeout: int = 60
    ) -> dict:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        # Ollama local doesn't require authorization header, but won't reject it either
        if self.api_key and self.api_key != "ollama":
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        # OpenRouter suggests additional headers
        if "openrouter.ai" in url:
            headers["HTTP-Referer"] = "https://github.com/ritheshrao197/Roshini-Marketing-Engine"
            headers["X-Title"] = "Roshini Marketing Engine"

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if json_format:
            payload["response_format"] = {"type": "json_object"}

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                
            latency = time.time() - start_time
            choices = res_data.get("choices", [])
            if not choices:
                raise ValueError("Empty choices in completion response.")
                
            text = choices[0]["message"]["content"]
            usage = res_data.get("usage", {})
            tokens = usage.get("total_tokens", 0)
            
            # Simple fallback cost calculations
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            # Lookup cost per million (default to 0 for free/local)
            cost = 0.0
            
            return {
                "text": text,
                "tokens": tokens,
                "latency": latency,
                "cost": cost,
                "status": "success",
                "error": None,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }
            }
        except Exception as e:
            latency = time.time() - start_time
            print(f"[{self.provider_name.upper()}] Request failed for model {model_name}: {e}")
            return {
                "text": "",
                "tokens": 0,
                "latency": latency,
                "cost": 0.0,
                "status": "failure",
                "error": str(e)
            }
