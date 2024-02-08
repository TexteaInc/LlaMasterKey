import json

from openai import OpenAI

client = (
    OpenAI()
)  # default to OPENAI_API_URL and OPENAI_API_KEY system environment variables

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is FastAPI?"},
    ],
)

print(json.dumps(completion.model_dump(), indent=2))

# print(completion.choices[0].message.content)
