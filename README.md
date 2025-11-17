# AI Code Generation Evaluation Framework

เฟรมเวิร์กสำหรับประเมินและเปรียบเทียบความสามารถในการสร้างโค้ดของ AI models โดยใช้ HumanEval benchmark (164 problems)

---

## 📋 ภาพรวม

โปรเจคนี้ทดสอบ 3 แนวทางในการสร้างโค้ด:

1. **Agentic AI System** - Multi-agent collaborative system (3 agents ทำงานร่วมกัน)
2. **Optimized Prompt** - Single model + prompt engineering
3. **Poor Prompt** - Single model + simple prompt
4. **Cloud APIs** - Gemini, ChatGPT, Claude

---

## 🤖 Agentic AI System Architecture

### Agent Roles

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTIC AI WORKFLOW                       │
└─────────────────────────────────────────────────────────────┘

[Problem] → [Generator] → [Draft Code v1]
                              ↓
                         [Manager Review]
                              ↓
                    ┌─────────┴─────────┐
                    │                   │
              [PERFECT?]            [Issues Found]
                    │                   │
                    ↓                   ↓
              [APPROVED]           [Refiner Fix]
                                        ↓
                                  [Draft Code v2]
                                        ↓
                                  [Manager Review]
                                        ↓
                                  (วนซ้ำ max 3 รอบ)
```

### 3 Agents และหน้าที่

**1. Generator Agent (Qwen3 8B)**
- **หน้าที่:** สร้างโค้ดเริ่มต้นจาก problem statement
- **Prompt:** Optimized prompt พร้อม edge case handling
- **Output:** Draft code version 1

**2. Manager Agent (DeepSeek Coder 6.7B)**
- **หน้าที่:** รีวิวโค้ดและหา logic errors
- **Focus:** Off-by-one errors, missing edge cases, wrong algorithms
- **Output:** 
  - `"PERFECT"` → อนุมัติโค้ด
  - `"Fix: [issue]"` → ส่งต่อให้ Refiner แก้ไข

**3. Refiner Agent (Llama3.1 8B)**
- **หน้าที่:** แก้ไขโค้ดตาม feedback จาก Manager
- **Focus:** Fix bugs, add edge cases, maintain function signature
- **Output:** Improved code version

### Workflow Steps

```python
# Iteration 0: Initial Generation
Generator → Draft Code v1

# Iteration 1-3: Refinement Loop
for i in range(max_iterations):
    Manager reviews Draft Code
    
    if "PERFECT" in feedback:
        APPROVED → Return final code
        break
    
    Refiner fixes issues → Draft Code v(i+1)
    Manager reviews again
```

### ตัวอย่าง Output

```
AGENTIC TEAM: Starting (Max 3 iterations)
   [Generator working...]
   [Iteration 0] Draft complete (Time: 8.54s, Tokens: 512)

[Iteration 1]
   [Manager reviewing...]
   [Manager] Fix: Missing edge case for empty list input
   [Refiner working...]
   [Refiner] Code updated (Time: 6.23s, Tokens: 384)

[Iteration 2]
   [Manager reviewing...]
   [Manager] APPROVED
   
AGENTIC TEAM: Complete (Total: 18.45s, 1248 tokens)
```

---

## 🔄 Flow การทดสอบ

### 1. Evaluation Flow (eval_humanevalOpt.py)

```
START
  ↓
Load HumanEval Dataset (164 problems)
  ↓
For each problem:
  ├─→ [1] Call Agentic AI System
  │     ├─ Generator creates draft
  │     ├─ Manager reviews (loop)
  │     └─ Refiner fixes issues
  │
  ├─→ [2] Extract generated code
  │
  ├─→ [3] Execute code with test cases
  │     ├─ Create temp file
  │     ├─ Run subprocess (5s timeout)
  │     └─ Check pass/fail
  │
  ├─→ [4] Measure 9 metrics
  │     ├─ Correctness (pass/fail)
  │     ├─ Latency (seconds)
  │     ├─ Tokens used
  │     ├─ Lines of Code (LOC)
  │     ├─ Cyclomatic Complexity
  │     ├─ Has Imports (boolean)
  │     ├─ Has Docstring (boolean)
  │     ├─ Syntax Valid (boolean)
  │     └─ Execution Speed (ns)
  │
  └─→ [5] Write results to CSV
  
END → Save results/humanevalOpt_[timestamp].csv
```

### 2. Test Execution Flow

```python
# สำหรับแต่ละ problem:

# Step 1: Generate Code
result = run_agentic_team(problem_prompt)
generated_code = result["code"]
latency = result["latency_sec"]
tokens = result["tokens_used"]

# Step 2: Test Correctness
with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
    f.write(generated_code)
    f.write("\n\n")
    f.write(problem['test'])  # Test cases from HumanEval
    f.write(f"\ncheck({problem['entry_point']})")
    
    # Run with 5-second timeout
    result = subprocess.run(
        ['python', temp_file],
        capture_output=True,
        timeout=5
    )
    
    passed = (result.returncode == 0)

# Step 3: Measure Code Quality
loc = count_lines_of_code(generated_code)
complexity = calculate_cyclomatic_complexity(generated_code)
has_imports = check_imports(generated_code)
syntax_valid = check_syntax(generated_code)
exec_time = measure_execution_speed(generated_code)

# Step 4: Save to CSV
csv_writer.writerow({
    'problem_id': problem['task_id'],
    'system_name': 'Agentic_AI',
    'passed_test': passed,
    'generation_latency_sec': latency,
    'total_tokens_used': tokens,
    'loc': loc,
    'cyclomatic_complexity': complexity,
    ...
})
```

### 3. Metrics Measurement Flow

```
Generated Code
  ↓
┌─────────────────────────────────────┐
│  METRIC MEASUREMENT PIPELINE        │
├─────────────────────────────────────┤
│                                     │
│  [1] Correctness                    │
│      └─ subprocess.run() → pass/fail│
│                                     │
│  [2] Latency                        │
│      └─ time.time() → seconds       │
│                                     │
│  [3] Tokens                         │
│      └─ Ollama API → count          │
│                                     │
│  [4] LOC                            │
│      └─ Line counting → lines       │
│                                     │
│  [5] Complexity                     │
│      └─ AST analysis → score        │
│                                     │
│  [6] Has Imports                    │
│      └─ AST parsing → boolean       │
│                                     │
│  [7] Has Docstring                  │
│      └─ AST parsing → boolean       │
│                                     │
│  [8] Syntax Valid                   │
│      └─ ast.parse() → boolean       │
│                                     │
│  [9] Execution Speed                │
│      └─ timeit → nanoseconds        │
│                                     │
└─────────────────────────────────────┘
  ↓
Write to CSV
```

---

## 📊 Evaluation Metrics

### Primary Metrics

| Metric | วิธีวัด | หน่วย | ค่าที่ดี |
|--------|---------|-------|----------|
| **Correctness** | subprocess.run() | Boolean | True |
| **Latency** | time.time() | Seconds | ต่ำ |
| **Tokens** | Ollama API | Count | ต่ำ |

### Code Quality Metrics

| Metric | วิธีวัด | หน่วย | ค่าที่ดี |
|--------|---------|-------|----------|
| **LOC** | Line counting | Lines | ต่ำ (แต่ไม่เกินไป) |
| **Complexity** | AST analysis | Score | ต่ำ |
| **Has Imports** | AST parsing | Boolean | True |
| **Has Docstring** | AST parsing | Boolean | True |
| **Syntax Valid** | ast.parse() | Boolean | True |
| **Exec Speed** | timeit | Nanoseconds | ต่ำ |

---

## 🚀 การติดตั้ง

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `openai` - สำหรับ Ollama API และ ChatGPT
- `google-generativeai` - สำหรับ Gemini
- `anthropic` - สำหรับ Claude
- `python-dotenv` - สำหรับ .env

### 2. ติดตั้ง Ollama และ Models

```bash
# ติดตั้ง Ollama
# https://ollama.ai

# ดาวน์โหลด models สำหรับ Agentic AI
ollama pull qwen3:8b                       # Generator (5.2 GB)
ollama pull llama3.1:8b                    # Refiner (4.9 GB)
ollama pull deepseek-coder:6.7b-instruct   # Manager (3.8 GB)

# (Optional) Models สำหรับ Poor Prompt testing
ollama pull phi3:3.8b                      # 2.2 GB
ollama pull gemma:7b-instruct              # 5.0 GB
ollama pull mistral:7b-instruct            # 4.4 GB

# เริ่ม Ollama service
ollama serve
```

### 3. ตั้งค่า API Keys (Optional - สำหรับ Cloud APIs)

```bash
# Copy .env.example
cp .env.example .env

# แก้ไข .env
GOOGLE_API_KEY=your-gemini-key-here
OPENAI_API_KEY=your-chatgpt-key-here
ANTHROPIC_API_KEY=your-claude-key-here
```

**ขอ API Keys:**
- Gemini: https://aistudio.google.com/app/apikey
- ChatGPT: https://platform.openai.com/api-keys
- Claude: https://console.anthropic.com/settings/keys

---

## 💻 วิธีใช้งาน

### 1. ทดสอบ Agentic AI System

```bash
python eval_humanevalOpt.py
```

**Output:**
```
Ollama ready
Loading HumanEval...
HumanEval Evaluation
Problems: 164 | Systems: 1
Results: results/humanevalOpt_20251116_180610.csv

[1/164] HumanEval/0
AGENTIC TEAM: Starting (Max 3 iterations)
   [Generator working...]
   [Iteration 0] Draft complete (Time: 8.54s, Tokens: 512)
[Iteration 1]
   [Manager reviewing...]
   [Manager] APPROVED
AGENTIC TEAM: Complete (Total: 12.34s, 768 tokens)
Agentic_AI... Passed: True | Latency: 12.34s | Tokens: 768 | LOC: 15 | Complexity: 3

[2/164] HumanEval/1
...
```

### 2. ทดสอบ Poor Prompt (6 Local Models)

```bash
python eval_humanevalPoor.py
```

**Models ที่ทดสอบ:**
- DeepSeek Coder 6.7B
- Llama 3.1 8B
- Phi3 3.8B
- Qwen3 8B
- Gemma 7B
- Mistral 7B

### 3. ทดสอบ Cloud APIs

```bash
python eval_humanevalAi.py
```

**APIs ที่ทดสอบ:**
- Google Gemini 2.5 Flash
- OpenAI GPT-4o
- Anthropic Claude 3.5 Sonnet

**หมายเหตุ:** มี rate limiting 5 วินาทีระหว่าง requests

### 4. ทดสอบ Agentic AI แบบเดี่ยว

```bash
python agentic_ai.py
```

---

## 📁 โครงสร้างโปรเจค

```
project/
│
├── eval_humanevalOpt.py          # ทดสอบ Agentic AI
├── eval_humanevalPoor.py         # ทดสอบ Poor Prompt (6 models)
├── eval_humanevalAi.py           # ทดสอบ Cloud APIs
├── run_evaluation.py             # Legacy script
│
├── agentic_ai.py                 # ⭐ Multi-agent system
│   ├── code_generator_agent()   # Generator (Qwen3 8B)
│   ├── manager_reviewer_agent() # Manager (DeepSeek 6.7B)
│   ├── code_refiner_agent()     # Refiner (Llama3.1 8B)
│   └── run_agentic_team()       # Main orchestrator
│
├── baseline_gemini.py            # Gemini API wrapper
├── baseline_chatgpt.py           # ChatGPT API wrapper
├── baseline_claude.py            # Claude API wrapper
│
├── optPrompt/                    # Optimized prompt versions
│   ├── baseline_deepseek.py
│   ├── baseline_llama31.py
│   ├── baseline_phi3.py
│   ├── baseline_qwen.py
│   ├── baseline_gemma.py
│   └── baseline_mistral.py
│
├── poorPrompt/                   # Poor prompt versions
│   ├── baseline_deepseek.py
│   ├── baseline_llama31.py
│   ├── baseline_phi3.py
│   ├── baseline_qwen.py
│   ├── baseline_gemma.py
│   └── baseline_mistral.py
│
├── data/
│   └── human-eval-v2-20210705.jsonl  # 164 problems
│
├── results/                      # CSV outputs
│   ├── humanevalOpt_*.csv       # Agentic AI results
│   ├── humanevalPoor_*.csv      # Poor prompt results
│   └── humanevalAi_*.csv        # Cloud API results
│
├── .env.example                  # API keys template
├── .env                          # Your API keys (gitignored)
├── requirements.txt
└── README.md
```

---

## 📈 ผลลัพธ์ (CSV Format)

### Columns

```csv
problem_id,system_name,generated_code,passed_test,generation_latency_sec,total_tokens_used,loc,cyclomatic_complexity,has_imports,has_docstring,syntax_valid,num_functions,avg_exec_time_ns
HumanEval/0,Agentic_AI,"def has_close_elements...",True,12.34,768,15,3,True,True,True,1,1250000
HumanEval/1,Agentic_AI,"def separate_paren...",True,15.67,892,22,5,True,True,True,1,980000
```

### ตัวอย่างผลลัพธ์

| Problem | System | Passed | Latency | Tokens | LOC | Complexity |
|---------|--------|--------|---------|--------|-----|------------|
| HumanEval/0 | Agentic_AI | ✅ True | 12.34s | 768 | 15 | 3 |
| HumanEval/1 | Agentic_AI | ✅ True | 15.67s | 892 | 22 | 5 |
| HumanEval/2 | Agentic_AI | ❌ False | 18.23s | 1024 | 28 | 7 |

---

## ⚙️ Configuration

### Model Parameters

```python
# Temperature
temperature = 0.1  # ความสม่ำเสมอสูง

# Timeout
test_timeout = 5  # วินาที

# Max Iterations (Agentic AI)
max_iterations = 3  # รอบ

# Rate Limiting (Cloud APIs)
delay_between_requests = 5  # วินาที
```

### Agentic AI Configuration

```python
# agentic_ai.py
MODEL_GENERATOR = "qwen3:8b"                    # Generator
MODEL_REFINER = "llama3.1:8b"                   # Refiner  
MODEL_MANAGER = "deepseek-coder:6.7b-instruct"  # Manager

# Workflow
max_iterations = 3  # จำนวนรอบ refinement สูงสุด
```

---

## 🔧 การแก้ปัญหา

### Ollama Connection Error

```bash
# ตรวจสอบ Ollama service
ollama serve

# ตรวจสอบ models
ollama list

# ทดสอบ connection
curl http://localhost:11434
```

### API Key Expired

```bash
# สร้าง API key ใหม่
# Gemini: https://aistudio.google.com/app/apikey
# ChatGPT: https://platform.openai.com/api-keys
# Claude: https://console.anthropic.com/settings/keys

# อัพเดทใน .env
GOOGLE_API_KEY=your-new-key
```

### Model Not Found

```bash
# ดาวน์โหลด models ที่จำเป็น
ollama pull qwen3:8b
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b-instruct
```

### ทดสอบแบบเร็ว (Subset)

```python
# แก้ไขใน eval_*.py
def load_human_eval(limit: int = None):
    # ...
    return problems[:10]  # ทดสอบแค่ 10 problems
```

---

## 📊 เวลาที่ใช้ในการทดสอบ

| Script | Models | Problems | เวลาโดยประมาณ |
|--------|--------|----------|----------------|
| `eval_humanevalOpt.py` | Agentic AI (3 agents) | 164 | ~30-40 นาที |
| `eval_humanevalPoor.py` | 6 local models | 164 | ~60-80 นาที |
| `eval_humanevalAi.py` | 3 cloud APIs | 164 | ~20-30 นาที |

**หมายเหตุ:**
- Agentic AI ใช้เวลานานกว่าเพราะมีหลายรอบ refinement
- Cloud APIs มี rate limiting (5s delay)
- เวลาขึ้นอยู่กับ hardware และ network

---

## 🎯 ความแตกต่างระหว่าง Prompts

### Optimized Prompt

```python
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
```

### Poor Prompt

```python
system_prompt = "You are an expert Python programmer. Respond ONLY with the raw Python code (no markdown, no explanations)."
```

### ผลลัพธ์ที่คาดหวัง

- **Optimized Prompt:** Pass rate สูงกว่า, handle edge cases ดีกว่า
- **Poor Prompt:** อาจมีปัญหา missing imports, edge cases
- **Agentic AI:** Pass rate สูงสุด เพราะมี review และ refinement loop

---

## 📝 License

โปรเจคนี้สำหรับการศึกษาและวิจัย
