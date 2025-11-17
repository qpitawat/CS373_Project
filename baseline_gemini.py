import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    import google.generativeai as genai
    
    # Configure Gemini
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    
    genai.configure(api_key=api_key)
    gemini_client = genai.GenerativeModel('gemini-2.5-flash')
    print("Baseline (Gemini) ready")
except ImportError:
    print("google-generativeai not installed. Run: pip install google-generativeai")
    gemini_client = None
except Exception as e:
    print(f"Cannot connect to Gemini: {e}")
    gemini_client = None

MODEL_NAME = "gemini-2.5-flash"  # or "gemini-1.5-pro" for better quality

def generate_code_gemini(problem_prompt: str) -> dict:
    if not gemini_client:
        return {
            "code": "ERROR: Gemini client not initialized",
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
    full_prompt = f"{system_prompt}\n\nProblem:\n{problem_prompt}"
    
    start_time = time.time()
    
    try:
        response = gemini_client.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
            )
        )
        
        generated_code = response.text
        # Gemini doesn't provide token count in the same way
        tokens_used = len(full_prompt.split()) + len(generated_code.split())  # Approximate
        
    except Exception as e:
        print(f"Error (Gemini): {e}")
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
    result = generate_code_gemini(test_problem)
    print("Baseline (Gemini) Test")
    print(f"Time: {result['latency_sec']:.2f}s")
    print(f"Tokens: {result['tokens_used']}")
    print("Code:")
    print(result['code'])
