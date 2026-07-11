import asyncio
import time
from llm.health import report_success, report_failure
from llm.analytics import log_request
from llm.providers.gemini import GeminiProvider
from llm.providers.openai_compatible import OpenAICompatibleProvider

def get_provider_client(provider_name: str, base_url: str, api_key: str):
    """Factory function returning the configured provider client."""
    if provider_name == "gemini":
        return GeminiProvider(api_key=api_key)
    else:
        return OpenAICompatibleProvider(base_url=base_url, api_key=api_key, provider_name=provider_name)


async def execute_with_failover(
    candidates: list[dict],
    prompt: str,
    system_instruction: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    json_format: bool = False,
    timeout: int = 60
) -> dict:
    """
    Executes the generation task sequentially over candidates.
    Updates health profiles, handles backoff retries, and rotates models on failure.
    """
    last_error = "No active providers configured or available."
    
    for index, candidate in enumerate(candidates):
        provider = candidate["provider"]
        model = candidate["model"]
        base_url = candidate["base_url"]
        api_key = candidate["api_key"]
        
        print(f"[RETRY] Attempting candidate {index + 1}/{len(candidates)}: {provider}/{model}")
        
        client = get_provider_client(provider, base_url, api_key)
        
        # Exponential backoff sleep (0 for first attempt, then starting at 2s)
        if index > 0:
            backoff_sleep = 2 ** index
            print(f"[RETRY] Backoff delay: Sleeping for {backoff_sleep}s...")
            await asyncio.sleep(backoff_sleep)
            
        res = await client.generate(
            model_name=model,
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
            json_format=json_format,
            timeout=timeout
        )
        
        latency = res["latency"]
        cost = res["cost"]
        tokens = res["tokens"]
        
        # Calculate cost based on candidate model spec if cost rates exist
        spec = candidate.get("spec", {})
        c_input = spec.get("cost_per_million_input", 0.0)
        c_output = spec.get("cost_per_million_output", 0.0)
        usage = res.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        if prompt_tokens or completion_tokens:
            cost = (prompt_tokens * c_input / 1_000_000.0) + (completion_tokens * c_output / 1_000_000.0)
        
        if res["status"] == "success" and res["text"]:
            # Success! Record success metrics, cache result, log stats, and return.
            report_success(provider, latency)
            log_request(
                provider=provider,
                model=model,
                latency=latency,
                tokens=tokens,
                cached=False,
                status="success",
                cost=cost
            )
            res["cost"] = cost  # Update cost in result
            res["provider"] = provider
            res["model"] = model
            return res
        else:
            # Failure. Report statistics and continue to next candidate.
            err_msg = res["error"] or "Empty response text returned."
            last_error = f"{provider}/{model} failed: {err_msg}"
            print(f"[RETRY] Candidate failed: {last_error}")
            
            # Check if rate-limited (429 status code or RESOURCE_EXHAUSTED string)
            is_429 = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
            report_failure(provider, is_429=is_429)
            
            log_request(
                provider=provider,
                model=model,
                latency=latency,
                tokens=tokens,
                cached=False,
                status="failure",
                cost=cost,
                error=err_msg
            )
            
    # If all candidates failed, raise an Exception
    raise RuntimeError(f"All routed providers failed to generate content. Last error: {last_error}")
