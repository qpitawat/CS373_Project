import time
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    
    client = OpenAI(api_key=api_key)
    print("Baseline (ChatGPT) ready")
except Exception as e:
    print(f"Cannot connect to OpenAI: {e}")
    client = None

MODEL_NAME = "gpt-5.1"  # or "gpt-4o" for better quality

def generate_code_chatgpt(problem_prompt: str) -> dict:
    if not client:
        return {
            "code": "ERROR: OpenAI client not initialized",
            "latency_sec": 0,
            "tokens_used": 0
        }

    system_prompt = "You are an expert Python programmer. Respond ONLY with the raw Python code (no markdown, no explanations)."
    
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
        print(f"Error (ChatGPT): {e}")
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
    result = generate_code_chatgpt(test_problem)
    print("Baseline (ChatGPT) Test")
    print(f"Time: {result['latency_sec']:.2f}s")
    print(f"Tokens: {result['tokens_used']}")
    print("Code:")
    print(result['code'])
