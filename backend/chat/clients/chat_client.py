import logging
from typing import List, Dict
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class ChatClient:
    """Reusable client for Chat Completions (GPT-5.1/4o)"""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        system_prompt: str,
        api_version: str = "2024-08-01-preview",
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Determine client type based on endpoint URL
        # If it looks like a standard OpenAI URL or custom Gateway but NOT specific Azure format
        # The provided sample uses standard `OpenAI` client pointing to a custom base_url
        logger.info(f"Initializing ChatClient for model: {model}")

        self.client = OpenAI(base_url=endpoint, api_key=api_key)

    def run(self):
        """Run interactive chat session"""
        print(f"\n💬 Chat Session Started ({self.model})")
        print("Type 'quit', 'exit', or Ctrl+C to end.")
        print("-" * 50)

        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                if user_input.lower() in ["quit", "exit"]:
                    print("👋 Goodbye!")
                    break

                if not user_input:
                    continue

                self.history.append({"role": "user", "content": user_input})

                print("🤖 Assistant: ", end="", flush=True)

                response_content = ""
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.history,  # type: ignore
                    temperature=0.7,
                    stream=True,
                )

                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        response_content += content

                print()  # Newline
                self.history.append({"role": "assistant", "content": response_content})

            except KeyboardInterrupt:
                print("\n\n👋 Exiting...")
                break
            except Exception as e:
                logger.error(f"Error calling API: {e}")
                print(f"\n❌ Error: {e}")
