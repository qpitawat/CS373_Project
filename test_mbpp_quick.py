"""Quick test script for MBPP with Agentic AI"""
import json
from agentic_ai import run_agentic_team
from run_evaluation import check_correctness

# Load first 5 MBPP problems
problems = []
with open("data/mbpp.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 5:
            break
        problems.append(json.loads(line))

print(f"Testing {len(problems)} MBPP problems with Agentic AI\n")

for i, problem in enumerate(problems):
    task_id = problem.get('task_id', i)
    text = problem.get('text', '')
    
    print(f"\n{'='*60}")
    print(f"Problem {i+1}/{len(problems)} - Task ID: {task_id}")
    print(f"Description: {text}")
    print('='*60)
    
    # Generate code
    result = run_agentic_team(text)
    generated_code = result["code"]
    
    print(f"\nGenerated Code:")
    print("```python")
    print(generated_code)
    print("```")
    
    # Test correctness
    passed = check_correctness(problem, generated_code, "MBPP")
    
    print(f"\n✓ PASSED" if passed else "\n✗ FAILED")
    print(f"Time: {result['latency_sec']:.2f}s | Tokens: {result['tokens_used']}")

print("\n" + "="*60)
print("Test Complete!")
