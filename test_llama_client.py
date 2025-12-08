from src.agentic.llama_learning_integration.llama_client import llama_cpp_text

if __name__ == "__main__":
    out = llama_cpp_text(
        "You are an OHS assistant. Answer in one short sentence: say hello to the user."
    )
    print("LLAMA RESPONSE:\n", out)
