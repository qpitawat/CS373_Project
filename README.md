# Agentic AI Code Generation Evaluation

This project evaluates different AI code generation approaches using the HumanEval benchmark dataset.

## Overview

The project compares **4 different systems**:
1. **Baseline_DeepSeek** - Single DeepSeek Coder 6.7B model
2. **Baseline_CodeLlama7B** - Single CodeLlama 7B model
3. **Baseline_Llama3_8B** - Single Llama3 8B model  
4. **Agentic_Team** - Multi-agent system with specialized roles

## Agentic Team Architecture

```
User Problem
     |
     v
+--------------------+
| Generator Agent    |  (DeepSeek Coder 6.7B)
| - Creates initial  |
|   code draft       |
+--------------------+
     |
     v
+--------------------+
| Manager Agent      |  (Llama3 8B)
| - Reviews code     |
| - Provides feedback|
+--------------------+
     |
     v
   Perfect? ----No---> +--------------------+
     |                 | Refiner Agent      |  (CodeLlama 7B)
    Yes                | - Fixes code based |
     |                 |   on feedback      |
     v                 +--------------------+
Final Code                    |
                              v
                        (Loop max 3 times)
```

### Agent Roles

- **Generator** (DeepSeek Coder 6.7B): Specializes in writing initial code
- **Manager** (Llama3 8B): Reviews code quality and provides feedback
- **Refiner** (CodeLlama 7B): Fixes code based on manager's feedback

## Evaluation Metrics

The system measures 6 key metrics:

1. **Correctness (Pass Rate)** - Does the code pass all test cases?
2. **Generation Latency** - How long does the AI take to generate code?
3. **Token Usage** - How many tokens are consumed? (cost indicator)
4. **Cyclomatic Complexity** - How complex is the generated code?
5. **Code Length (LOC)** - How many lines of code? (conciseness)
6. **Execution Speed** - How fast does the generated code run?

## Installation

### Prerequisites

1. Install Python 3.8+
2. Install Ollama: https://ollama.ai

### Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Pull required Ollama models:
```bash
ollama pull deepseek-coder:6.7b-instruct
ollama pull codellama:7b-instruct
ollama pull llama3:8b
```

3. Ensure Ollama is running:
```bash
ollama serve
```

## Usage

### Run Full Evaluation

```bash
python run_evaluation.py
```

This will:
- Load all problems from HumanEval dataset
- Test each system on every problem
- Save results to `results_HumanEval_TIMESTAMP.csv`

### Test Individual Systems

Test Agentic Team:
```bash
python agentic_ai.py
```

Test Baseline Models:
```bash
python baseline_deepseek.py        # DeepSeek Coder 6.7B
python baseline_ollama.py          # CodeLlama 7B
python baseline_llama3.py          # Llama3 8B
```

## Project Structure

```
.
├── agentic_ai.py                 # Multi-agent system implementation
├── baseline_deepseek.py          # DeepSeek Coder 6.7B baseline
├── baseline_ollama.py            # CodeLlama 7B baseline
├── baseline_llama3.py            # Llama3 8B baseline
├── run_evaluation.py             # Main evaluation script
├── human-eval-v2-20210705.jsonl  # HumanEval dataset
├── mbpp.jsonl                    # MBPP dataset (optional)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Workflow

```
Start
  |
  v
Load HumanEval Dataset
  |
  v
For each problem:
  |
  +---> For each system (4 systems):
  |       |
  |       +---> Generate code
  |       |
  |       +---> Measure metrics:
  |       |       - Correctness
  |       |       - Latency
  |       |       - Tokens
  |       |       - Complexity
  |       |       - LOC
  |       |       - Exec Speed
  |       |
  |       +---> Save to CSV
  |
  v
Generate results_HumanEval_TIMESTAMP.csv
  |
  v
End
```

## Results

Results are saved in CSV format with the following columns:

- `problem_id` - HumanEval problem identifier
- `system_name` - Which system generated the code
- `generated_code` - The actual code generated
- `passed_test` - Boolean, did it pass all tests?
- `generation_latency_sec` - Time to generate code
- `total_tokens_used` - Number of tokens consumed
- `cyclomatic_complexity` - Code complexity score
- `code_length_loc` - Lines of code
- `avg_exec_time_sec` - Average execution time

## Notes

- The Agentic Team uses 3 iterations maximum for refinement
- All models use temperature=0.1 for consistency
- Execution timeout is set to 5 seconds per test
- Code complexity is calculated using AST analysis

## Troubleshooting

**Ollama connection error:**
- Make sure Ollama is running: `ollama serve`
- Check if models are downloaded: `ollama list`

**Unicode encoding error:**
- This is handled automatically with UTF-8 encoding

**Model not found:**
- Pull the missing model: `ollama pull <model-name>`

## License

This project is for educational and research purposes.
