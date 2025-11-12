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

MODEL_GENERATOR = "deepseek-coder:6.7b-instruct"
MODEL_REFINER = "codellama:7b-instruct"
MODEL_MANAGER = "llama3:8b"

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
        
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1].split("```")[0]
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0]
            
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
    system_prompt = "You are an expert Python programmer. Write a complete function to solve the problem. Respond ONLY with the raw Python code."
    user_prompt = f"Problem:\n{problem}"
    return call_ollama_worker(system_prompt, user_prompt, MODEL_GENERATOR)

def code_refiner_agent(code_draft: str, feedback: str) -> dict:
    print("   [Refiner working...]")
    system_prompt = "You are a programmer. Your task is to rewrite the 'Old Code' based on the 'Review Feedback'. Respond ONLY with the new, complete, fixed Python code."
    
    user_prompt = f"""
Old Code:
```python
{code_draft}
```
Review Feedback: {feedback}

New Fixed Code: """
    return call_ollama_worker(system_prompt, user_prompt, MODEL_REFINER)

def manager_reviewer_agent(problem: str, code_draft: str) -> dict:
    print("   [Manager reviewing...]")
    if not ollama_client:
        return {"feedback": "ERROR: Ollama client not initialized", "tokens_used": 0, "latency_sec": 0}

    system_prompt = """You are a Senior Software Architect and a strict code reviewer. Your task is to review the code against the problem statement. Look for:

- Logic errors or bugs.
- Missing edge cases (e.g., empty lists, null inputs).
- Bad readability (PEP 8) or inefficient code.

Provide concise, actionable feedback. If the code is PERFECT and needs no changes, respond ONLY with the word 'PERFECT'."""
    
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