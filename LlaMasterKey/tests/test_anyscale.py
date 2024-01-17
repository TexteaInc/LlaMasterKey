import os

import openai

client = openai.OpenAI(
    base_url=os.environ["ANYSCALE_BASE_URL"],
    api_key=os.environ["ANYSCALE_API_KEY"],
)

chat_completion = client.chat.completions.create(
    model="meta-llama/Llama-2-7b-chat-hf",
    messages=[{"role": "system", "content": "You are a helpful assistant."},
              {"role": "user", "content": "Who is Einstein?"}],
    temperature=0.7
)
print(chat_completion.model_dump())
