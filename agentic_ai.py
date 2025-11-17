import time
from openai import OpenAI

try:
    ollama_client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama',
    )
    ollama_client.models.list()
    print("Ollama ready")
except Exception as e:
    print(f"Cannot connect to Ollama: {e}")
    ollama_client = None

MODEL_GENERATOR = "qwen3:8b"
MODEL_REFINER = "llama3.1:8b"
MODEL_MANAGER = "deepseek-coder:6.7b-instruct"

def call_ollama_worker(system_prompt: str, user_prompt: str, model_name: str) -> dict:
    if not ollama_client:
        return {"code": "ERROR: Ollama client not initialized", "tokens_used": 0, "latency_sec": 0}
        
    try:
        start_time = time.time()
        response = ollama_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
        )
        latency_sec = time.time() - start_time
        generated_code = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        # Extract code from markdown blocks
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0]
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0]
        
        # Remove any test/print statements at the end
        lines = generated_code.strip().split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip print, assert, and test-related lines
            if stripped.startswith('print(') or stripped.startswith('assert ') or stripped.startswith('# Test'):
                continue
            clean_lines.append(line)
        generated_code = '\n'.join(clean_lines)
            
        return {
            "code": generated_code.strip(), 
            "latency_sec": latency_sec, 
            "tokens_used": tokens_used
        }
    except Exception as e:
        print(f"Error (Ollama Worker {model_name}): {e}")
        return {"code": f"ERROR: {e}", "tokens_used": 0, "latency_sec": time.time() - start_time}

def code_generator_agent(problem: str) -> dict:
    print("   [Generator working...]")
    system_prompt = """You are a world-class Python programmer competing in a coding challenge.

YOUR MISSION: Write PERFECT, PRODUCTION-READY code that passes ALL test cases.

MANDATORY REQUIREMENTS:
1. Include ALL necessary imports (typing, re, math, heapq, collections, itertools, etc.)
2. Follow the EXACT function signature from the problem
3. Handle ALL edge cases:
    - Empty inputs ([], "", None)
    - Single element inputs
    - Negative numbers
    - Zero values
    - Large inputs
4. Write efficient O(n) or O(n log n) solutions when possible
5. Use appropriate data structures (dict, set, deque, heap)
6. NO explanations, NO test code, NO print/input statements

OUTPUT: Raw Python code ONLY. No markdown, no comments except docstring."""
    
    user_prompt = f"Solve this problem with PERFECT code:\n\n{problem}"
    return call_ollama_worker(system_prompt, user_prompt, MODEL_GENERATOR)

def code_refiner_agent(code_draft: str, feedback: str, problem: str) -> dict:
    print("   [Refiner working...]")
    system_prompt = """You are an expert Python debugger and optimizer.

YOUR TASK: Fix the code to be PERFECT based on the feedback.

RULES:
1. Keep ALL imports (add more if needed)
2. Fix the EXACT issue mentioned in feedback
3. Maintain function signature
4. Add edge case handling if missing
5. Ensure no syntax errors
6. Remove any print() or input() calls
7. Return COMPLETE working code

OUTPUT: Raw Python code ONLY."""
    
    user_prompt = f"""Problem:
{problem}

Current Code:
```python
{code_draft}
```

Feedback: {feedback}

Provide the COMPLETE fixed code:"""
    return call_ollama_worker(system_prompt, user_prompt, MODEL_REFINER)

def manager_reviewer_agent(problem: str, code_draft: str) -> dict:
    print("   [Manager reviewing...]")
    if not ollama_client:
        return {"feedback": "ERROR: Ollama client not initialized", "tokens_used": 0, "latency_sec": 0}

    system_prompt = """You are a Senior Code Reviewer.
Your goal is to find LOGIC ERRORS that would cause the code to fail tests.

INSTRUCTIONS:
- Look for: Off-by-one errors, missing edge cases (empty input, negative numbers), or wrong algorithms.
- IGNORE: Variable names, comments, or style issues.
- If the logic is correct, output ONLY: "PERFECT"
- If there is a bug, output: "Fix: [explain the logic error briefly]"
"""
    
    user_prompt = f"""
Problem Statement:
{problem}

Code to Review:
```python
{code_draft}
```
Your Feedback: """

    start_time = time.time()
    try:
        response = ollama_client.chat.completions.create(
            model=MODEL_MANAGER,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
        )
        feedback = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
    except Exception as e:
        print(f"Error (Manager): {e}")
        feedback = f"ERROR: {e}"
        tokens_used = 0
        
    latency_sec = time.time() - start_time

    return {
        "feedback": feedback.strip(),
        "latency_sec": latency_sec,
        "tokens_used": tokens_used
    }
def run_agentic_team(problem_prompt: str, max_iterations: int = 3) -> dict:
    print(f"\nAGENTIC TEAM: Starting (Max {max_iterations} iterations)")

    total_latency_sec = 0
    total_tokens_used = 0
    
    # Phase 1: Generate initial solution
    gen_result = code_generator_agent(problem_prompt)
    current_code_draft = gen_result["code"]
    total_latency_sec += gen_result["latency_sec"]
    total_tokens_used += gen_result["tokens_used"]

    print(f"   [Iteration 0] Draft complete (Time: {gen_result['latency_sec']:.2f}s, Tokens: {gen_result['tokens_used']})")
    
    # Phase 2: Iterative refinement
    for i in range(max_iterations):
        print(f"\n[Iteration {i+1}]")
        
        # Manager reviews
        review_result = manager_reviewer_agent(problem_prompt, current_code_draft)
        total_latency_sec += review_result["latency_sec"]
        total_tokens_used += review_result["tokens_used"]
        feedback = review_result["feedback"]
        
        feedback_preview = feedback[:80] + "..." if len(feedback) > 80 else feedback
        print(f"   [Manager] {feedback_preview}")
        
        # Check if perfect
        if "PERFECT" in feedback.upper():
            print(f"   [Manager] APPROVED")
            break
        
        # Refiner fixes issues
        refine_result = code_refiner_agent(current_code_draft, feedback, problem_prompt)
        current_code_draft = refine_result["code"]
        total_latency_sec += refine_result["latency_sec"]
        total_tokens_used += refine_result["tokens_used"]
        
        print(f"   [Refiner] Code updated (Time: {refine_result['latency_sec']:.2f}s, Tokens: {refine_result['tokens_used']})")
    
    print(f"\nAGENTIC TEAM: Complete (Total: {total_latency_sec:.2f}s, {total_tokens_used} tokens)")

    return {
        "code": current_code_draft,
        "latency_sec": total_latency_sec,
        "tokens_used": total_tokens_used
    }

if __name__ == "__main__":
    test_problem = "Write a Python function `add(a, b)` that returns the sum of two numbers. Include a docstring."

    if not ollama_client:
        print("\nCannot run test")
        print("Check Ollama connection")
    else:
        print("\nTesting Agentic AI")
        result = run_agentic_team(test_problem)
        print("\nAgentic AI Test Results")
        print(f"Total Time: {result['latency_sec']:.2f}s")
        print(f"Total Tokens: {result['tokens_used']}")
        print("Final Code:")
        print(result['code'])