import asyncio
from llm.router import choose_models
from llm.cache import compute_hash, get_cached_response, set_cached_response
from llm.analytics import log_request
from llm.retry import execute_with_failover


def _run_async(coro):
    """Run an async coroutine synchronously."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No loop running in this thread (the common case) - just run it directly.
        # Deliberately not falling back to asyncio.run(coro) from inside another
        # except/branch: doing so previously risked re-running a coroutine that
        # had already been partially driven by a failed loop.run_until_complete()
        # call, which raises "cannot reuse already awaited coroutine".
        return asyncio.run(coro)
    else:
        # Already inside a running loop (e.g. called from async code): run the
        # coroutine on a separate thread with its own fresh event loop instead.
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()


async def call_llm_async(
    prompt: str,
    system_instruction: str = None,
    json_format: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    version: str = "v1",
    timeout: int = 60
) -> str:
    """
    Async version of call_llm.
    Main entry point for unified, free-first AI text generation.
    Supports score-based routing, automatic failovers, SQLite caching, and performance logging.
    """
    # 1. Resolve candidates sorted by score matching capabilities
    candidates = choose_models(requires_json=json_format)
    if not candidates:
        raise ValueError("No healthy/configured LLM providers found for the requested criteria.")

    # 2. Check cache for the highest score model
    top_cand = candidates[0]
    top_model = top_cand["model"]
    top_provider = top_cand["provider"]

    hash_val = compute_hash(system_instruction, prompt, version, top_model, temperature)
    cached = get_cached_response(hash_val)

    if cached:
        print(f"[CACHE] Hit for {top_provider}/{top_model} (version: {version})")
        log_request(
            provider=cached["provider"],
            model=cached["model"],
            latency=cached["latency"],
            tokens=cached["token_count"],
            cached=True,
            status="success",
            cost=cached["cost"]
        )
        return cached["response"]

    # 3. Cache miss: Execute failover loop
    res = await execute_with_failover(
        candidates=candidates,
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature,
        max_tokens=max_tokens,
        json_format=json_format,
        timeout=timeout
    )

    # 4. Cache the successful execution response
    success_model = res["model"]
    success_provider = res["provider"]
    success_hash = compute_hash(system_instruction, prompt, version, success_model, temperature)
    
    set_cached_response(
        hash_val=success_hash,
        system_prompt=system_instruction,
        user_prompt=prompt,
        prompt_version=version,
        model=success_model,
        temperature=temperature,
        response=res["text"],
        provider=success_provider,
        latency=res["latency"],
        token_count=res["tokens"],
        cost=res["cost"],
        status="success"
    )

    return res["text"]


def call_llm(
    prompt: str,
    system_instruction: str = None,
    json_format: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    version: str = "v1",
    timeout: int = 60
) -> str:
    """
    Synchronous wrapper for call_llm_async.
    Main entry point for unified, free-first AI text generation.
    """
    coro = call_llm_async(
        prompt=prompt,
        system_instruction=system_instruction,
        json_format=json_format,
        temperature=temperature,
        max_tokens=max_tokens,
        version=version,
        timeout=timeout
    )
    return _run_async(coro)
