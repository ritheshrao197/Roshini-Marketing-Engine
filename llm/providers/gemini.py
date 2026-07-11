import time
from google import genai
from google.genai import types
from llm.providers.base import BaseProvider

class GeminiProvider(BaseProvider):
    """
    Native client for Gemini models using the google-genai SDK.
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
        start_time = time.time()
        try:
            client = genai.Client(api_key=self.api_key)
            
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            if system_instruction:
                config.system_instruction = system_instruction
                
            if json_format:
                config.response_mime_type = "application/json"
                
            # Perform async content generation using standard SDK methods
            # Note: We run this using standard await with standard client.aio
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            
            latency = time.time() - start_time
            text = response.text or ""
            
            # Extract usage metadata
            tokens = 0
            prompt_tokens = 0
            completion_tokens = 0
            usage = getattr(response, "usage_metadata", None)
            if usage:
                prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
                completion_tokens = getattr(usage, "candidates_token_count", 0) or 0
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
            print(f"[GEMINI] Request failed for model {model_name}: {e}")
            return {
                "text": "",
                "tokens": 0,
                "latency": latency,
                "cost": 0.0,
                "status": "failure",
                "error": str(e)
            }
