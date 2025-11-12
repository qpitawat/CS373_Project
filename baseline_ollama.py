# baseline_ollama.py
import time
from openai import OpenAI # ใช้ library ของ OpenAI เพื่อคุยกับ Ollama

# ตั้งค่าให้ชี้ไปที่ Ollama ที่รันบนเครื่อง
try:
    client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama', # ใส่ 'ollama'
    )
    client.models.list()
    print("✅ Baseline (Ollama) พร้อมใช้งาน")
except Exception as e:
    print(f"❌ ไม่สามารถเชื่อมต่อ Ollama (http://localhost:11434)")
    print("👉 ตรวจสอบว่าคุณรัน 'ollama serve' หรือเปิดโปรแกรม Ollama แล้ว")
    client = None

# โมเดลที่เราจะใช้ (ต้อง 'ollama pull codellama:7b-instruct' ก่อน)
# หรือ 'ollama pull llama3:8b'
MODEL_NAME = "codellama:7b-instruct"

def generate_code_ollama(problem_prompt: str) -> dict:
    """
    สร้างโค้ดโดยใช้ Ollama (CodeLlama) แบบ One-shot
    """
    if not client:
        return {
            "code": "ERROR: Ollama client not initialized",
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
        print(f"!! Error (Ollama): {e}")
        generated_code = f"ERROR: {e}"
        tokens_used = 0
        
    end_time = time.time()
    latency_sec = end_time - start_time
    
    # แกะโค้ด
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
    # ตัวอย่างการทดสอบ
    test_problem = "def add(a, b):\n    \"\"\"Return the sum of two numbers.\"\"\""
    result = generate_code_ollama(test_problem)
    print("--- Baseline (Ollama) Test ---")
    print(f"Time taken: {result['latency_sec']:.2f}s")
    print(f"Tokens used: {result['tokens_used']}")
    print("--- Code ---")
    print(result['code'])