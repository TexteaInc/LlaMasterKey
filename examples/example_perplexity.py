import json, os

from openai import OpenAI # Perplexity API is OpenAI client-compatible

client = OpenAI(
    api_key=os.environ["PERPLEXITY_API_KEY"], 
    base_url=os.environ["PERPLEXITY_BASE_URL"]
)

messages = [{"role": "user", "content": ("How many stars are in the universe?")}]

response = client.chat.completions.create(model="pplx-7b-chat", messages=messages)

print(json.dumps(response.model_dump(), indent=2))

# print(response.choices[0].message.content)