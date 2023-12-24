# One API token for calling all LLMs 

# When a call in OpenAI's API is made, the message was routed to llamaPass 


from openai import OpenAI
import cohere

import requests
from fastapi import FastAPI, HTTPException, Header, Request

app = FastAPI()


#############################################
# Debugging and utility functions ############
#############################################

async def print_request(request):
    print(f'request header       : {dict(request.headers.items())}' )
    print(f'request query params : {dict(request.query_params.items())}')  
    try : 
        print(f'request json         : {await request.json()}')
    except Exception as err:
        # could not parse json
        print(f'request body         : {await request.body()}')

@app.post("/print_request") # Use this function to decypher the request from an official API
async def print_request(request: Request):
    try:
        await print_request(request)
        return {"status": "OK"}
    except Exception as err:
        logging.error(f'could not print REQUEST: {err}')
        return {"status": "ERR"}
        

#############################################
#  Below is the beef ########################
#############################################

@app.post("/openai/chat/completions")
async def openai_proxy(
    Authorization: str = Header(),
    request_body: dict = None
):
    if request_body is None:
        raise HTTPException(status_code=400, detail="Request body is required")

    # now dispatch the request to real OpenAI end point 

    print ("This is the proxy request ")
    print ("header", Authorization)
    print ("body", request_body)

    print ("Now making real request to OpenAI")

    real_client = OpenAI()
    completion = real_client.chat.completions.create(
        **request_body
    )

    print ("This is the response from OpenAI")
    print (completion)

    return completion


# Cohere request is like this
# request header       : {'host': 'localhost:8000', 'user-agent': 'python-requests/2.31.0', 'accept-encoding': 'gzip, deflate, br', 'accept': '*/*', 'connection': 'keep-alive', 'authorization': 'BEARER WHATEVER PLACEHOLDER', 'request-source': 'python-sdk-4.39', 'content-type': 'application/json', 'content-length': '388'}
# request query params : {}
# request json         : {'message': 'Is Sun Yat-Sen?', 'conversation_id': '', 'model': 'command', 'return_chat_history': False, 'return_prompt': False, 'return_preamble': False, 'chat_history': None, 'preamble_override': None, 'temperature': 0.8, 'max_tokens': None, 'stream': False, 'user_name': None, 'p': None, 'k': None, 'logit_bias': None, 'search_queries_only': None, 'documents': None, 'connectors': None}

@app.post("/cohere/v1/chat") # Cohere's default API endpoint is {$CO_API_URL}/v1/{chat,rerank,summarize} where $CO_API_URL is an environment variable that Cohere client looks for
async def cohere_proxy(
    Authorization: str = Header(),
    request_body: dict = None
):
    if request_body is None:
        raise HTTPException(status_code=400, detail="Request body is required")

    # now dispatch the request to real OpenAI end point 

    print ("This is the proxy request")
    print ("header", Authorization)
    print ("body", request_body)

    print ("Now making real request to cohere")

    co = cohere.Client()
    # request_body = {"message": "howdy", "model": "command"} # a test case
    prediction = co.chat(**request_body)

    print ("This is the response from Cohere")
    print (prediction)

    # BUG: When trying to return here, FastAPI throws an error
    return prediction