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

MODEL_GENERATOR = "codellama:7b-instruct"
MODEL_REFINER = "llama3:8b"
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
    system_prompt = """You are an expert Python programmer. Generate ONLY the function code to solve the problem.

CRITICAL RULES:
1. Include ALL necessary imports at the top (typing, re, math, heapq, collections, etc.)
2. Follow the EXACT function signature if provided in the problem
3. Write minimal, efficient code - avoid unnecessary complexity
4. Handle edge cases (empty inputs, None, single elements)
5. NO explanations, NO test code, NO print statements
6. Return ONLY the raw Python function code"""
    
    user_prompt = f"Write the function for this problem:\n\n{problem}"
    return call_ollama_worker(system_prompt, user_prompt, MODEL_GENERATOR)

def code_refiner_agent(code_draft: str, feedback: str) -> dict:
    print("   [Refiner working...]")
    system_prompt = """You are an expert Python programmer. Fix the code based on feedback.

RULES:
1. Keep ALL imports from the original code
2. Fix ONLY what the feedback mentions
3. Keep the function signature unchanged
4. Make minimal changes - don't rewrite working code
5. Return ONLY the complete fixed Python code, no explanations"""
    
    user_prompt = f"""Fix this code based on the feedback.

Current Code:
```python
{code_draft}
```

Feedback: {feedback}

Fixed Code:"""
    return call_ollama_worker(system_prompt, user_prompt, MODEL_REFINER)

def manager_reviewer_agent(problem: str, code_draft: str) -> dict:
    print("   [Manager reviewing...]")
    if not ollama_client:
        return {"feedback": "ERROR: Ollama client not initialized", "tokens_used": 0, "latency_sec": 0}

    system_prompt = """You are a code reviewer. Check if the code solves the problem correctly.

REVIEW CHECKLIST:
1. Does it have all required imports?
2. Does the function signature match the problem?
3. Will it handle edge cases (empty lists, None, single elements)?
4. Is the logic correct for the problem description?
5. Is it simple and efficient?

RESPONSE RULES:
- If code is correct and complete: respond ONLY "PERFECT"
- If there are issues: state ONE specific fix in 10 words or less
- Be strict but concise"""
    
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
def run_agentic_team(problem_prompt: str, max_iterations: int = 1) -> dict:
    print(f"\nAGENTIC TEAM: Starting")

    total_latency_sec = 0
    total_tokens_used = 0
    current_code_draft = ""

    gen_result = code_generator_agent(problem_prompt)
    current_code_draft = gen_result["code"]
    total_latency_sec += gen_result["latency_sec"]
    total_tokens_used += gen_result["tokens_used"]

    print(f"   [Iteration 0] Draft complete (Time: {gen_result['latency_sec']:.2f}s)")
    print("```python\n" + current_code_draft + "\n```")

    for i in range(max_iterations):
        print(f"[Iteration {i+1}]")
        
        review_result = manager_reviewer_agent(problem_prompt, current_code_draft)
        total_latency_sec += review_result["latency_sec"]
        total_tokens_used += review_result["tokens_used"]
        feedback = review_result["feedback"]
        
        feedback_first_line = feedback.splitlines()[0] if '\n' in feedback else feedback
        print(f"   [Manager Feedback] (Time: {review_result['latency_sec']:.2f}s): {feedback_first_line}...")
        
        if "PERFECT" in feedback.upper():
            print("   [Manager] Approved")
            break
            
        refine_result = code_refiner_agent(current_code_draft, feedback)
        current_code_draft = refine_result["code"]
        total_latency_sec += refine_result["latency_sec"]
        total_tokens_used += refine_result["tokens_used"]
        
        print(f"   [Refiner] Code updated (Time: {refine_result['latency_sec']:.2f}s)")
        print("```python\n" + current_code_draft + "\n```")

    print(f"AGENTIC TEAM: Complete")

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