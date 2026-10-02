import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

load_dotenv()


def pick_llm(level: str):
    """
    Select an LLM based on the difficulty level.

    Levels:
        low    -> Cloudflare GPT-OSS 120B
        medium -> Groq GPT-OSS 120B
        high   -> Gemini 3.8 Flash

    Returns:
        A LangChain chat model.
    """

    level = level.lower()

    # ---------------------------------------------------------
    # LOW -> CLOUDFLARE GPT-OSS 120B
    # ---------------------------------------------------------
    if level == "low":

        llm = ChatOpenAI(
            model="@cf/openai/gpt-oss-120b",
            temperature=0,
            api_key=os.getenv("CLOUDFLARE_API_TOKEN"),
            base_url=(
                "https://api.cloudflare.com/client/v4/"
                f"accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID')}/ai/v1"
            ),
        )

    # ---------------------------------------------------------
    # MEDIUM -> GROQ GPT-OSS 120B
    # ---------------------------------------------------------
    elif level == "medium":

        llm = ChatOpenAI(
            model="openai/gpt-oss-120b",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )

    # ---------------------------------------------------------
    # HIGH -> GEMINI 3.8 FLASH
    # ---------------------------------------------------------
    elif level == "high":

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )

    else:
        raise ValueError(
            f"Unsupported level: {level}. "
            "Use 'low', 'medium', or 'high'."
        )

    return llm


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    for level in ["low", "medium", "high"]:

        print(f"\n===== Testing {level.upper()} =====")

        llm = pick_llm(level)

        response = llm.invoke(
            "What is the capital of France? "
            "Answer in one sentence."
        )

        print(response.content)
