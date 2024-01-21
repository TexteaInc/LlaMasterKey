import cohere

co = cohere.Client()  # use placeholder API key

# generate a prediction for a prompt
prediction = co.chat(message='How many days in a year?', model='command')

# print the predicted text
print(f'Chatbot: {prediction.text}')
