"""Evaluation script for HumanEval benchmark"""
import json
import os
import csv
import subprocess
import tempfile
from datetime import datetime
import timeit
import ast
import time

#from optPrompt.baseline_deepseek import generate_code_deepseek
#from optPrompt.baseline_llama31 import generate_code_llama31
#from optPrompt.baseline_phi3 import generate_code_phi3
#from optPrompt.baseline_qwen import generate_code_qwen
#from optPrompt.baseline_gemma import generate_code_gemma
#from optPrompt.baseline_mistral import generate_code_mistral
#from baseline_chatgpt import generate_code_chatgpt
from baseline_gemini import generate_code_gemini

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

def check_correctness(problem: dict, generated_code: str) -> bool:
    if "ERROR" in generated_code:
        return False
        
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(generated_code)
        f.write("\n\n")
        f.write(problem['test'])
        f.write(f"\ncheck({problem['entry_point']})")
        temp_file_name = f.name
        
    try:
        result = subprocess.run(
            ['python', temp_file_name],
            capture_output=True,
            text=True,
            timeout=5.0
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False
    finally:
        os.remove(temp_file_name)

def get_code_quality_metrics(code_str: str) -> dict:
    """Get comprehensive code quality metrics"""
    if "ERROR" in code_str or not code_str.strip():
        return {
            "loc": 0,
            "has_imports": False,
            "has_docstring": False,
            "syntax_valid": False,
            "num_functions": 0,
            "cyclomatic_complexity": 0
        }
    
    try:
        tree = ast.parse(code_str)
        
        # Count lines of code
        lines = [line.strip() for line in code_str.split('\n')]
        loc = len([line for line in lines if line and not line.startswith('#')])
        
        # Check for imports
        has_imports = any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree))
        
        # Calculate cyclomatic complexity
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        # Check for docstrings and count functions
        has_docstring = False
        num_functions = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                num_functions += 1
                if ast.get_docstring(node):
                    has_docstring = True
        
        return {
            "loc": loc,
            "has_imports": has_imports,
            "has_docstring": has_docstring,
            "syntax_valid": True,
            "num_functions": num_functions,
            "cyclomatic_complexity": complexity
        }
    except Exception:
        lines = [line.strip() for line in code_str.split('\n')]
        loc = len([line for line in lines if line and not line.startswith('#')])
        return {
            "loc": loc,
            "has_imports": False,
            "has_docstring": False,
            "syntax_valid": False,
            "num_functions": 0,
            "cyclomatic_complexity": 0
        }

def get_exec_time(code_str: str, entry_point: str, problem: dict) -> float:
    """Measure average execution time"""
    if "ERROR" in code_str or not code_str.strip():
        return float('inf')
    
    try:
        setup_code = """
from typing import List, Tuple, Optional, Dict, Any, Set
import re
import math
import statistics
import heapq
import collections
from collections import Counter, defaultdict
from itertools import chain
"""
        setup_code += "\n" + code_str + "\n"
        
        test_code = None
        prompt = problem.get('prompt', '')
        
        # Strategy 1: Extract from docstring
        if '>>>' in prompt:
            for line in prompt.split('\n'):
                if '>>>' in line and entry_point in line:
                    test_code = line.split('>>>')[1].strip()
                    if '\n' in test_code:
                        test_code = test_code.split('\n')[0].strip()
                    break
        
        # Strategy 2: Parse function signature
        if not test_code:
            try:
                tree = ast.parse(code_str)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == entry_point:
                        test_params = []
                        for arg in node.args.args:
                            arg_name = arg.arg
                            if 'list' in arg_name.lower() or 'arr' in arg_name.lower():
                                test_params.append('[1, 2, 3]')
                            elif 'str' in arg_name.lower() or 'text' in arg_name.lower():
                                test_params.append("'test'")
                            elif 'dict' in arg_name.lower():
                                test_params.append('{}')
                            else:
                                test_params.append('1')
                        test_code = f"{entry_point}({', '.join(test_params)})"
                        break
            except:
                pass
        
        # Strategy 3: Keyword-based fallback
        if not test_code:
            prompt_lower = prompt.lower()
            if 'list' in prompt_lower:
                test_code = f"{entry_point}([1, 2, 3])"
            elif 'string' in prompt_lower:
                test_code = f"{entry_point}('test')"
            elif 'int' in prompt_lower:
                test_code = f"{entry_point}(5)"
            else:
                test_code = f"{entry_point}()"
        
        if test_code:
            try:
                # First verify it can run at least once with subprocess (has timeout)
                test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
                test_file.write(setup_code)
                test_file.write(f"\n{test_code}\n")
                test_file.close()
                
                # Try to run with 20 second timeout
                result = subprocess.run(
                    ['python', test_file.name],
                    capture_output=True,
                    timeout=20.0,
                    stdin=subprocess.DEVNULL
                )
                os.remove(test_file.name)
                
                if result.returncode != 0:
                    return -1  # Return -1 for execution errors
                
                # Now time it with maximum precision
                # Use time.perf_counter_ns() for nanosecond precision
                try:
                    import time as time_module
                    
                    # Warm up
                    exec(setup_code, {})
                    
                    # Determine optimal number of iterations
                    # Quick test with 10 iterations
                    test_globals = {}
                    exec(setup_code, test_globals)
                    
                    start_ns = time_module.perf_counter_ns()
                    for _ in range(10):
                        exec(test_code, test_globals.copy())
                    elapsed_ns = time_module.perf_counter_ns() - start_ns
                    avg_per_run_ns = elapsed_ns / 10
                    
                    # If each run < 1ms, do more iterations for precision
                    if avg_per_run_ns < 1_000_000:  # < 1ms
                        iterations = 10000
                    elif avg_per_run_ns < 10_000_000:  # < 10ms
                        iterations = 1000
                    elif avg_per_run_ns < 100_000_000:  # < 100ms
                        iterations = 100
                    else:
                        iterations = 10
                    
                    # Final precise measurement
                    test_globals = {}
                    exec(setup_code, test_globals)
                    
                    start_ns = time_module.perf_counter_ns()
                    for _ in range(iterations):
                        exec(test_code, test_globals.copy())
                    elapsed_ns = time_module.perf_counter_ns() - start_ns
                    
                    # Return average time in nanoseconds
                    return elapsed_ns / iterations
                    
                except Exception:
                    return -1  # Return -1 for timing errors
            except Exception:
                return float('inf')
        
        return float('inf')
    except Exception:
        return float('inf')

def main():
    problems = load_human_eval()
    
    if not problems:
        print("HumanEval dataset not found")
        return

    systems_to_test = {
        #"Opt_DeepSeek": generate_code_deepseek,
        #"Opt_Llama31_8B": generate_code_llama31,
        #"Opt_Phi3_3.8B": generate_code_phi3,
        #"Opt_Qwen3_8B": generate_code_qwen,
        #"Opt_Gemma_7B": generate_code_gemma,
        #"Opt_Mistral_7B": generate_code_mistral,
        #"Agentic_Team": run_agentic_team,
        #"Baseline_ChatGPT": generate_code_chatgpt
        "Baseline_Gemini": generate_code_gemini
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_filename = f"results/humanevalOpt_{timestamp}.csv"
    
    csv_headers = [
        "problem_id", "system_name", "generated_code",
        "passed_test", "generation_latency_sec", "total_tokens_used",
        "loc", "cyclomatic_complexity", "has_imports", "has_docstring", 
        "syntax_valid", "num_functions", "avg_exec_time_ns"
    ]

    print(f"HumanEval Evaluation")
    print(f"Problems: {len(problems)} | Systems: {len(systems_to_test)}")
    print(f"Results: {results_filename}\n")

    with open(results_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()

        for i, problem in enumerate(problems):
            problem_id = problem['task_id']
            problem_prompt = problem['prompt']
            entry_point = problem['entry_point']

            print(f"[{i+1}/{len(problems)}] {problem_id}")

            for system_name, system_func in systems_to_test.items():
                print(f"  {system_name}...", end=" ", flush=True)
                
                # Add delay to avoid API rate limits
                if "Gemini" in system_name or "ChatGPT" in system_name or "Claude" in system_name:
                    if i > 0:  # Skip delay for first problem
                        time.sleep(10)  # 5 second delay between API calls
                
                stats = system_func(problem_prompt)
                generated_code = stats["code"]

                passed_test = check_correctness(problem, generated_code)
                quality_metrics = get_code_quality_metrics(generated_code)
                avg_exec_time = get_exec_time(generated_code, entry_point, problem)
                
                # Format execution time in nanoseconds
                if avg_exec_time > 0:
                    exec_time_str = f"{avg_exec_time:.0f}ns"
                else:
                    exec_time_str = "N/A"
                print(f"Passed: {passed_test} | Latency: {stats['latency_sec']:.2f}s | Tokens: {stats['tokens_used']} | LOC: {quality_metrics['loc']} | Complexity: {quality_metrics['cyclomatic_complexity']} | Exec: {exec_time_str}")

                writer.writerow({
                    "problem_id": problem_id,
                    "system_name": system_name,
                    "generated_code": generated_code.replace('\n', '\\n'),
                    "passed_test": passed_test,
                    "generation_latency_sec": stats["latency_sec"],
                    "total_tokens_used": stats["tokens_used"],
                    "loc": quality_metrics["loc"],
                    "cyclomatic_complexity": quality_metrics["cyclomatic_complexity"],
                    "has_imports": quality_metrics["has_imports"],
                    "has_docstring": quality_metrics["has_docstring"],
                    "syntax_valid": quality_metrics["syntax_valid"],
                    "num_functions": quality_metrics["num_functions"],
                    "avg_exec_time_ns": avg_exec_time if avg_exec_time > 0 else -1
                })

    print(f"\nComplete! Results: {results_filename}")

if __name__ == "__main__":
    main()
