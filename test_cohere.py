import os
os.environ['CO_API_URL'] = "http://localhost:8000/cohere" # LlaMasterKey endpoint 
os.environ['CO_API_KEY'] = "WHATEVER PLACEHOLDER"


import cohere

co = cohere.Client() # use placeholder API key

# generate a prediction for a prompt
prediction = co.chat(message='Howdy!', model='command')

# print the predicted text
print(f'Chatbot: {prediction.text}')