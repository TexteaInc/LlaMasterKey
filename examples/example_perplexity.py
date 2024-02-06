import os

from openai import OpenAI

messages = [
    {
        "role": "system",
        "content": (
            "You are an artificial intelligence assistant and you need to "
            "engage in a helpful, detailed, polite conversation with a user."
        ),
    },
    {
        "role": "user",
        "content": ("How many stars are in the universe?"),
    },
]

client = OpenAI(
    api_key=os.environ["PERPLEXITY_API_KEY"], base_url=os.environ["PERPLEXITY_BASE_URL"]
)

response = client.chat.completions.create(
    model="mistral-7b-instruct",
    messages=messages,
)
print(response)
