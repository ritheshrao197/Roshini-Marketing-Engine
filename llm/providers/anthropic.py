import time
import httpx
from llm.providers.base import BaseProvider

class AnthropicProvider(BaseProvider):
    """
    Native client for Anthropic Claude models using HTTP requests.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

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
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": model_name,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }

        if system_instruction:
            payload["system"] = system_instruction

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()

            latency = time.time() - start_time
            content_list = res_data.get("content", [])
            text = ""
            for item in content_list:
                if item.get("type") == "text":
                    text += item.get("text", "")

            usage = res_data.get("usage", {})
            prompt_tokens = usage.get("input_tokens", 0)
            completion_tokens = usage.get("output_tokens", 0)
            tokens = prompt_tokens + completion_tokens

            return {
                "text": text,
                "tokens": tokens,
                "latency": latency,
                "cost": 0.0,
                "status": "success",
                "error": None,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }
            }
        except Exception as e:
            latency = time.time() - start_time
            print(f"[ANTHROPIC] Request failed for model {model_name}: {e}")
            return {
                "text": "",
                "tokens": 0,
                "latency": latency,
                "cost": 0.0,
                "status": "failure",
                "error": str(e)
            }
