# One API token and one API for calling all LLMs 

# When a call in OpenAI's API is made, the message was routed to llamaPass 

import requests

from openai import OpenAI

from fastapi import FastAPI, HTTPException, Header

app = FastAPI()

@app.post("/openai/chat/completions")
async def openai(
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