from __future__ import annotations

from backend.src.microservices.agentic.llm import OpenAILLMClient


def main() -> None:
    client = OpenAILLMClient(api_key="sk-dummy", model="gpt-dummy")
    resp = client.generate(messages=[{"role": "user", "content": "Hello"}])
    print("model:", resp.get("model"))
    print("assistant:", resp["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

