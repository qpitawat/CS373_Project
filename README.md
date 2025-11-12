# Agentic AI Code Generation Evaluation

This project evaluates different AI code generation approaches using the HumanEval and MBPP benchmark datasets.

## Overview

The project compares **multiple baseline models** and an **Agentic AI system**:

### Baseline Models (Single-Agent)
1. **DeepSeek Coder** - 6.7B instruct (3.8 GB)
2. **Llama 3.1** - 8B (4.9 GB)
3. **Phi3** - 3.8B (2.2 GB)
4. **Qwen3** - 8B (5.2 GB)
5. **Gemma** - 7B instruct (5.0 GB)
6. **Mistral** - 7B instruct (4.4 GB)

### Agentic AI System (Multi-Agent) - Currently Disabled for Baseline Testing
- Multi-agent collaborative system with specialized roles
- Uses 3 different models working together
- Iterative refinement process

## Agentic Team Architecture (Currently Disabled)

```
User Problem
     |
     v
+--------------------+
| Generator Agent    |  (CodeLlama 7B)
| - Creates initial  |
|   code draft       |
+--------------------+
     |
     v
+--------------------+
| Manager Agent      |  (DeepSeek Coder 6.7B)
| - Reviews code     |
| - Provides feedback|
+--------------------+
     |
     v
   Perfect? ----No---> +--------------------+
     |                 | Refiner Agent      |  (Llama3 8B)
    Yes                | - Fixes code based |
     |                 |   on feedback      |
     v                 +--------------------+
Final Code                    |
                              v
                        (Loop max 1 time)
```

### Agent Roles

- **Generator** (CodeLlama 7B): Specializes in writing initial code drafts
- **Manager** (DeepSeek Coder 6.7B): Reviews code quality and provides feedback
- **Refiner** (Llama3 8B): Fixes code based on manager's feedback

**Note:** The Agentic AI system is currently commented out in `run_evaluation.py` to focus on baseline model comparison.

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

2. Pull required Ollama models for baseline testing:
```bash
ollama pull deepseek-coder:6.7b-instruct  # 3.8 GB
ollama pull llama3.1:8b                    # 4.9 GB
ollama pull phi3:3.8b                      # 2.2 GB
ollama pull qwen3:8b                       # 5.2 GB
ollama pull gemma:7b-instruct              # 5.0 GB
ollama pull mistral:7b-instruct            # 4.4 GB
```

3. (Optional) For Agentic AI system:
```bash
ollama pull codellama:7b-instruct
ollama pull llama3:8b
```

4. Ensure Ollama is running:
```bash
ollama serve
```

## Usage

### Run Full Baseline Evaluation

```bash
python run_evaluation.py
```

This will:
- Load all problems from HumanEval dataset
- Test all 7 baseline models on every problem
- Save results to `results/results_HumanEval_TIMESTAMP.csv`

### Test Individual Baseline Models

```bash
python baseline_deepseek.py        # DeepSeek Coder 6.7B (3.8 GB)
python baseline_llama31.py         # Llama 3.1 8B (4.9 GB)
python baseline_phi3.py            # Phi3 3.8B (2.2 GB)
python baseline_qwen.py            # Qwen3 8B (5.2 GB)
python baseline_gemma.py           # Gemma 7B (5.0 GB)
python baseline_mistral.py         # Mistral 7B (4.4 GB)
```

### Test Agentic AI System (Optional)

```bash
python agentic_ai.py
```

### Quick MBPP Test

```bash
python test_mbpp_quick.py
```

## Project Structure

```
.
├── agentic_ai.py                      # Multi-agent system (currently disabled)
├── baseline_deepseek.py               # DeepSeek Coder 6.7B (3.8 GB)
├── baseline_llama31.py                # Llama 3.1 8B (4.9 GB)
├── baseline_phi3.py                   # Phi3 3.8B (2.2 GB)
├── baseline_qwen.py                   # Qwen3 8B (5.2 GB)
├── baseline_gemma.py                  # Gemma 7B (5.0 GB)
├── baseline_mistral.py                # Mistral 7B (4.4 GB)
├── run_evaluation.py                  # Main evaluation script
├── test_mbpp_quick.py                 # Quick MBPP test script
├── data/
│   ├── human-eval-v2-20210705.jsonl  # HumanEval dataset
│   └── mbpp.jsonl                     # MBPP dataset
├── results/                           # Evaluation results (CSV files)
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## Workflow

```
Start
  |
  v
Load HumanEval Dataset (164 problems)
  |
  v
For each problem:
  |
  +---> For each baseline model (7 models):
  |       |
  |       +---> Generate code
  |       |
  |       +---> Measure metrics:
  |       |       - Correctness (pass/fail)
  |       |       - Latency (generation time)
  |       |       - Tokens (cost indicator)
  |       |       - Complexity (cyclomatic)
  |       |       - LOC (lines of code)
  |       |       - Exec Speed (runtime)
  |       |
  |       +---> Save to CSV
  |
  v
Generate results/results_HumanEval_TIMESTAMP.csv
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

- All models use temperature=0.1 for consistency and reproducibility
- Execution timeout is set to 5 seconds per test case
- Code complexity is calculated using AST analysis (cyclomatic complexity)
- The Agentic AI system uses 1 iteration maximum for refinement (when enabled)
- Results are saved in CSV format with UTF-8 encoding
- Total evaluation time: ~7-10 minutes per model for full HumanEval (164 problems)

## Troubleshooting

**Ollama connection error:**
- Make sure Ollama is running: `ollama serve`
- Check if models are downloaded: `ollama list`
- Verify Ollama is accessible at `http://localhost:11434`

**Model not found error:**
- Pull the missing model: `ollama pull <model-name>`
- Example: `ollama pull qwen2.5:7b`

**Unicode encoding error:**
- This is handled automatically with UTF-8 encoding in the code

**Slow evaluation:**
- Consider testing on a subset first by modifying `load_human_eval(limit=10)`
- Larger models (8B) are slower than smaller ones (3.8B)
- GPU acceleration significantly improves speed

**Import errors:**
- Make sure you've installed requirements: `pip install -r requirements.txt`
- Only dependency is `openai` package for Ollama API

## License

This project is for educational and research purposes.
