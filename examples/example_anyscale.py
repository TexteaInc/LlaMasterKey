import json
import os

import openai

client = openai.OpenAI( # AnyScale API is OpenAI client-compatible
    base_url=os.environ["ANYSCALE_BASE_URL"],
    api_key=os.environ["ANYSCALE_API_KEY"],
)

chat_completion = client.chat.completions.create(
    model="meta-llama/Llama-2-7b-chat-hf",
    messages=[{"role": "user", "content": "Who is Einstein?"}],
)

print(json.dumps(chat_completion.model_dump(), indent=2))

# print(chat_completion.model_dump())
