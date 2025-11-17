import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from anthropic import Anthropic
    
    # Initialize Claude client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in .env file")
    
    client = Anthropic(api_key=api_key)
    print("Baseline (Claude) ready")
except ImportError:
    print("anthropic not installed. Run: pip install anthropic")
    client = None
except Exception as e:
    print(f"Cannot connect to Claude: {e}")
    client = None

MODEL_NAME = "claude-3-5-sonnet-20241022"  # or "claude-3-opus-20240229" for best quality

def generate_code_claude(problem_prompt: str) -> dict:
    if not client:
        return {
            "code": "ERROR: Claude client not initialized",
            "latency_sec": 0,
            "tokens_used": 0
        }

    system_prompt = "You are an expert Python programmer. Respond ONLY with the raw Python code (no markdown, no explanations)."
    
    start_time = time.time()
    
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=2048,
            temperature=0.1,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Problem:\n{problem_prompt}"}
            ]
        )
        
        generated_code = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        
    except Exception as e:
        print(f"Error (Claude): {e}")
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
    result = generate_code_claude(test_problem)
    print("Baseline (Claude) Test")
    print(f"Time: {result['latency_sec']:.2f}s")
    print(f"Tokens: {result['tokens_used']}")
    print("Code:")
    print(result['code'])
