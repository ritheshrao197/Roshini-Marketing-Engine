import asyncio
import os
import sys

# Add root folder to path to import llm module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import call_llm
from llm.router import choose_models, calculate_score
from llm.cache import compute_hash, get_cached_response, set_cached_response
from llm.health import report_failure, is_provider_healthy

async def run_tests():
    print("=== STARTING LLM ROUTER & CACHE UNIT TESTS ===")
    
    # 1. Test Score Calculations
    print("\n--- 1. Testing Routing Scores ---")
    mock_free_model = {
        "name": "free-model",
        "is_free": True,
        "speed": 10,
        "context": 6,
        "json_support": True,
        "vision": False
    }
    mock_paid_model = {
        "name": "paid-model",
        "is_free": False,
        "speed": 5,
        "context": 8,
        "json_support": True,
        "vision": True
    }
    
    score_free = calculate_score(mock_free_model)
    score_paid = calculate_score(mock_paid_model)
    print(f"Calculated Score (Free Model): {score_free} (Expected: ~360)")
    print(f"Calculated Score (Paid Model): {score_paid} (Expected: ~325)")
    assert score_free > score_paid, "Free model should score higher in free-first routing!"
    
    # 2. Test Cooldown & Health tracking
    print("\n--- 2. Testing Health & Cooldown Tracking ---")
    report_failure("test_provider", is_429=True)
    healthy = is_provider_healthy("test_provider")
    print(f"Is 'test_provider' healthy after 429? {healthy} (Expected: False)")
    assert not healthy, "Provider should be cooled down after a 429!"
    
    # 3. Test SQLite cache layer
    print("\n--- 3. Testing SQLite Cache ---")
    sys_prompt = "You are a helpful cook."
    usr_prompt = "How do I boil an egg?"
    version = "v1"
    model = "test-model"
    temp = 0.7
    
    h_val = compute_hash(sys_prompt, usr_prompt, version, model, temp)
    print(f"Computed hash: {h_val}")
    
    # Clear previous cached entry if any
    set_cached_response(
        hash_val=h_val,
        system_prompt=sys_prompt,
        user_prompt=usr_prompt,
        prompt_version=version,
        model=model,
        temperature=temp,
        response="Boil it in hot water for 6 minutes.",
        provider="test_provider",
        latency=1.2,
        token_count=15,
        cost=0.0,
        status="success"
    )
    
    cached = get_cached_response(h_val)
    print(f"Retrieved cached response: {cached.get('response') if cached else 'None'}")
    assert cached is not None, "Cache insertion/retrieval failed!"
    assert cached["response"] == "Boil it in hot water for 6 minutes.", "Cached content mismatch!"
    
    # Test version mismatch doesn't retrieve old cache
    h_val_v2 = compute_hash(sys_prompt, usr_prompt, "v2", model, temp)
    cached_v2 = get_cached_response(h_val_v2)
    print(f"Retrieved cached response for v2: {cached_v2}")
    assert cached_v2 is None, "Cache did not respect version boundaries!"
    
    # 4. Test Router Candidates selection
    print("\n--- 4. Testing Router Selection ---")
    candidates = choose_models(requires_json=True)
    print(f"Found {len(candidates)} healthy candidate models for JSON:")
    for c in candidates[:3]:
        print(f" - Candidate: {c['provider']}/{c['model']} (Score: {c['score']})")
        
    print("\n=== ALL UNIT TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
