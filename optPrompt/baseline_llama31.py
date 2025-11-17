import time
from openai import OpenAI

try:
    client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama',
    )
    client.models.list()
    print("Baseline (Llama3.1) ready")
except Exception as e:
    print(f"Cannot connect to Ollama: {e}")
    client = None

MODEL_NAME = "llama3.1:8b"

def generate_code_llama31(problem_prompt: str) -> dict:
    if not client:
        return {
            "code": "ERROR: Ollama client not initialized",
            "latency_sec": 0,
            "tokens_used": 0
        }

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
    
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Problem:\n{problem_prompt}"}
            ],
            temperature=0.1,
        )
        
        generated_code = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
    except Exception as e:
        print(f"Error (Llama3.1): {e}")
        generated_code = f"ERROR: {e}"
        tokens_used = 0
        
    end_time = time.time()
    latency_sec = end_time - start_time
    
    if "```python" in generated_code:
        generated_code = generated_code.split("```python")[1].split("```")[0]
    elif "```" in generated_code:
        generated_code = generated_code.split("```")[1].split("```")[0]

    return {
        "code": generated_code.strip(),
        "latency_sec": latency_sec,
        "tokens_used": tokens_used
    }

if __name__ == "__main__":
    test_problem = "def add(a, b):\n    \"\"\"Return the sum of two numbers.\"\"\""
    result = generate_code_llama31(test_problem)
    print("Baseline (Llama3.1) Test")
    print(f"Time: {result['latency_sec']:.2f}s")
    print(f"Tokens: {result['tokens_used']}")
    print("Code:")
    print(result['code'])
