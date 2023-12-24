# LLaMasterKey: One master key for all LLM/GenAI endpoints 

A big pain in the era of LLMs is that you need to get an API token for each of them, OpenAI, Cohere, Google Vertex AI, Anthropic, AnyScale, Huggingface, etc. 

If an intern in your startup accidentally pushes the code containing the API keys to Github, you would have to revoke each of the API tokens that was assigned to him. Even worse, you already forgot which API tokens were given to him. So what do you do? Revoke all keys and suffer from service interruption? 

This is when LlaMasterKey (pronounced as "La Master key" which stands for "Llama" + "Master" + "key" where "La" stands for "the" in French) comes to play. It severs as a proxy that dispatches the requests to the real cloud LLM/GenAI endpoints and returns the response to your team/customer. To authenticate, only one master key is needed between your team member or customer and your LlaMasterKey server. If any of them makes you unhappy, you only need to revoke one key to cut off his/her access to all cloud LLM/GenAI endpoints. The actual keys are hidden from your team members and customers.

## Roadmap 

1. Currently no master key is enabled. We will add authentication. This is important for the response from a cloud LLM/GenAI endpoint to be returned to the right team/customer.
2. More cloud LLM/GenAI endpoints will be supported. **Currently supports only `OpenAI/chat/completion`**. Planned support  in the next 1-2 weeks: 
   * AnyScale 
   * HuggingFace
   * Anthropic
   * Google Vertex AI
   * Cohere
   * Vectara AI

## Usage

1. On your server, set up the keys for each cloud LLM/GenAI endpoint you want to use. For example, if you want to use OpenAI, set the OS environment variable `OPENAI_API_KEY`. 

   ```bash
   export OPENAI_API_KEY=sk-xxx #openai
   export HF_API_KEY=hf-xxx # huggingface
   export ANYSCALE_API_KEY=as-xxx # anyscale
   export ANTHROPIC_API_KEY=an-xxx # anthropic
   export VECTOR_AI_API_KEY=va-xxx # vectara 
   ```

2. Start your LlaMasterKey server

   ```bash
   uvicorn LlaMasterKey:app --reload  # Currently only supports OpenAI 
   ```

   The server will read keys set in the OS environment variables and start a server at `http://localhost:8000` (8000 because it's the default port of FastAPI).

3. On each computer that needs to connect to a cloud LLM, e.g., the laptop of your intern, set the OS environment variable `OPENAI_BASE_URL` to `http://{Your_LlaMasterKey_SERVER}/openai` where `{Your_LlaMasterKey_SERVER}` is the address of your LlaMasterKey server. 

   For example, 
   
   ```bash
    export OPENAI_BASE_URL=http://localhost:8000/openai
    ```

4. Make requests to the cloud LLM/GenAI endpoint as usual.

   For example, `test_chatgpt.py` is a client request. 

## How it works under the hood

### OpenAI

OpenAI's API has [a field](https://github.com/openai/openai-python/blob/f1c7d714914e3321ca2e72839fe2d132a8646e7f/src/openai/_client.py#L102) called `base_url` which is default to `os.environ.get("OPENAI_BASE_URL")`. To use LlaMasterKey, you can set the OS environment variable `OPENAI_BASE_URL` on the computers where your client runs to `http://{Your_LlaMasterKey}/openai` so your team members make requests to a LlaMasterKey server which will then forward the request to openAI server. 


## License

Ah, this is important. Let's say MIT for now? 