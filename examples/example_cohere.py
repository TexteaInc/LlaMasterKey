import json

import cohere

co = cohere.Client()  # API key default to CO_API_KEY

# generate a prediction for a prompt
prediction = co.chat(message="How many days in a year?")

# print the predicted text
print(f"The response from Cohere Chat API is \n ===========\n  {prediction.text}")
