import json
import gzip
import os
import csv
import subprocess
import tempfile
from datetime import datetime
import timeit
import ast

from baseline_deepseek import generate_code_deepseek
from baseline_ollama import generate_code_ollama
from baseline_llama3 import generate_code_llama3
from agentic_ai import run_agentic_team

def load_human_eval(limit: int = None):
    print("Loading HumanEval...")
    problems = []
    filepath = "data/human-eval-v2-20210705.jsonl"
    if not os.path.exists(filepath):
        print(f"File '{filepath}' not found")
        return []
        
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            problems.append(json.loads(line))
    
    if limit:
        return problems[:limit]
    return problems

def load_mbpp(limit: int = None):
    print("Loading MBPP...")
    problems = []
    filepath = "data/mbpp.jsonl"
    if not os.path.exists(filepath):
        print(f"File '{filepath}' not found")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            problems.append(json.loads(line))
            
    if limit:
        return problems[:limit]
    return problems

def check_correctness(problem: dict, generated_code: str, benchmark_type: str) -> bool:
    if "ERROR" in generated_code:
        return False
        
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(generated_code)
        f.write("\n\n")
        
        if benchmark_type == "HumanEval":
            f.write(problem['test'])
            f.write(f"\ncheck({problem['entry_point']})")
        elif benchmark_type == "MBPP":
            f.write("import sys\n")
            for test_case in problem['test_list']:
                f.write(f"try:\n    {test_case}\nexcept AssertionError:\n    print('Test Failed')\n    sys.exit(1)\n")
            f.write("print('All Tests Passed')\n")
            
        temp_file_name = f.name
        
    try:
        result = subprocess.run(
            ['python', temp_file_name],
            capture_output=True,
            text=True,
            timeout=5.0
        )
        
        if result.returncode == 0:
            return True
        else:
            return False
            
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        return False
    finally:
        os.remove(temp_file_name)

def get_cyclomatic_complexity(code_str: str) -> int:
    if "ERROR" in code_str or not code_str.strip():
        return 0
    
    try:
        tree = ast.parse(code_str)
        complexity = 1
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    except Exception:
        return 0

def get_code_length(code_str: str) -> int:
    if "ERROR" in code_str:
        return 0
    
    lines = [line.strip() for line in code_str.split('\n')]
    loc = len([line for line in lines if line and not line.startswith('#')])
    return loc

def get_exec_time(code_str: str, entry_point: str, benchmark_type: str) -> float:
    if "ERROR" in code_str or not code_str.strip():
        return float('inf')
        
    try:
        if benchmark_type == "HumanEval":
            setup_code = code_str
            test_code = f"{entry_point}()"
            if "add" in entry_point:
                test_code = f"{entry_point}(1, 2)"
            elif "check_if_even" in entry_point:
                test_code = f"{entry_point}(4)"
            
            try:
                t = timeit.timeit(stmt=test_code, setup=setup_code, number=100)
                return t / 100.0
            except Exception:
                return float('inf')
    except Exception:
        return float('inf')
        
    return float('inf')

def main():
    problems = load_human_eval()
    BENCHMARK_TYPE = "HumanEval"
    
    if not problems:
        print("Benchmark not found")
        return

    systems_to_test = {
        "Baseline_DeepSeek": generate_code_deepseek,
        "Baseline_CodeLlama7B": generate_code_ollama,
        "Baseline_Llama3_8B": generate_code_llama3,
        "Agentic_Team": run_agentic_team,
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_filename = f"results/results_{BENCHMARK_TYPE}_{timestamp}.csv"
    
    csv_headers = [
        "problem_id", "system_name", "generated_code",
        "passed_test", "generation_latency_sec", "total_tokens_used",
        "cyclomatic_complexity", "code_length_loc", "avg_exec_time_sec"
    ]

    print(f"Starting experiment: {len(problems)} problems | {len(systems_to_test)} systems")
    print(f"Results will be saved to: {results_filename}")

    with open(results_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()

        for i, problem in enumerate(problems):
            problem_id = problem.get('task_id', problem.get('id', i))
            problem_prompt = problem.get('prompt', problem.get('text', ''))
            entry_point = problem.get('entry_point', '')

            print(f"\n[Problem {i+1}/{len(problems)}] ID: {problem_id}")

            for system_name, system_func in systems_to_test.items():
                print(f"  [Testing: {system_name}]")
                
                stats = system_func(problem_prompt)
                generated_code = stats["code"]

                passed_test = check_correctness(problem, generated_code, BENCHMARK_TYPE)
                complexity = get_cyclomatic_complexity(generated_code)
                code_length = get_code_length(generated_code)
                avg_exec_time = get_exec_time(generated_code, entry_point, BENCHMARK_TYPE)
                
                print(f"    Passed: {passed_test} | Complexity: {complexity} | LOC: {code_length} | Latency: {stats['latency_sec']:.2f}s")

                writer.writerow({
                    "problem_id": problem_id,
                    "system_name": system_name,
                    "generated_code": generated_code.replace('\n', '\\n'),
                    "passed_test": passed_test,
                    "generation_latency_sec": stats["latency_sec"],
                    "total_tokens_used": stats["tokens_used"],
                    "cyclomatic_complexity": complexity,
                    "code_length_loc": code_length,
                    "avg_exec_time_sec": avg_exec_time
                })

    print(f"\nExperiment complete! Results saved to {results_filename}")

if __name__ == "__main__":
    main()