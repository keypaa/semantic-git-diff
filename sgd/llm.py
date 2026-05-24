import ollama

DEFAULT_MODEL = "qwen2.5:3b"


def query_llm(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 120) -> str:
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": 4096, "temperature": 0.3},
        )
        return response["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"LLM query failed: {e}")
