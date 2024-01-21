import json
import os
from typing import Optional
from urllib.parse import urlparse, parse_qs

import httpx
from fastapi import FastAPI, Request, Response, status
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse

local_configure_file = "llamakey_local.env"

class VectaraToken:
    customer_id: str
    client_id: str
    client_secret: str

    def __init__(self, customer_id: str, client_id: str, client_secret: str):
        self.customer_id = customer_id
        self.client_id = client_id
        self.client_secret = client_secret

    def is_valid(self) -> bool:
        return self.customer_id is not None and self.client_id is not None and self.client_secret is not None


class Config:
    base_url: str
    openai_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    anyscale_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    vectara_token: Optional[VectaraToken] = None

    def __init__(self):
        """
        Loads keys for server from env vars
        """
        self.base_url = os.environ.get("BASE_URL", default="http://127.0.0.1:8000")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.cohere_api_key = os.environ.get("CO_API_KEY")
        self.anyscale_api_key = os.environ.get("ANYSCALE_API_KEY")
        self.huggingface_api_key = os.environ.get("HF_TOKEN")
        self.vectara_token = VectaraToken(
            customer_id=os.environ.get("VECTARA_CUSTOMER_ID"),
            client_id=os.environ.get("VECTARA_CLIENT_ID"),
            client_secret=os.environ.get("VECTARA_CLIENT_SECRET")
        )

    def user_env(self) -> dict[str, str]:
        """
        Get a dictionary of env vars for user
        """
        _user_env: dict[str, str] = dict()
        if self.openai_api_key:
            _user_env["OPENAI_BASE_URL"] = self.base_url
            _user_env["OPENAI_API_KEY"] = "openai"
        if self.cohere_api_key:
            _user_env["CO_API_URL"] = self.base_url
            _user_env["CO_API_KEY"] = "cohere"
        if self.anyscale_api_key:
            _user_env["ANYSCALE_BASE_URL"] = self.base_url
            _user_env["ANYSCALE_API_KEY"] = "anyscale"
        if self.huggingface_api_key:
            _user_env["HF_INFERENCE_ENDPOINT"] = self.base_url
            _user_env["HF_TOKEN"] = "huggingface"
        if self.vectara_token.is_valid():
            _user_env["VECTARA_CUSTOMER_ID"] = "vectara-customer"
            _user_env["VECTARA_CLIENT_ID"] = "vectara-client"
            _user_env["VECTARA_CLIENT_SECRET"] = "vectara-secret"
            _user_env["VECTARA_BASE_URL"] = self.base_url + "/vectara"

        return _user_env

    def user_env_file(self) -> str:
        return self.__generate_env(self.user_env())

    @staticmethod
    def __generate_env(_dict: dict[str, str]) -> str:
        """
        Generate a bash compatible environment exports according to string dictionary.
        """

        s = ""
        for k, v in _dict.items():
            s += f"export {k}=\"{v}\"\n"

        return s


user_env: dict[str, str] = dict()
config = Config()
with open(local_configure_file, "w") as f:
    f.write(config.user_env_file())
print (f"Please tell your clients to set the following environment variables before running their code using the Python SDK of OpenAI/Cohere/etc.:\n{config.user_env_file()}")
print(f"For convenience, the shell command to set such environment variables are written to `./{local_configure_file}`. Simply run `source {local_configure_file}` activate them.")
print (f"For example, \n `source {local_configure_file} && python3 -c \"import openai; openai.Completion.create(...)\"`" )
# BUG: Why is this message printed twice? 

app = FastAPI()

client = httpx.AsyncClient()


@app.api_route(
    path="/vectara/{path:path}",
    methods=["GET", "POST", "HEAD", "DELETE", "PUT", "CONNECT", "OPTIONS", "TRACE", "PATCH"]
)
async def catch_vectara_all(request: Request, path: str, response: Response):
    if path == "oauth2/token":
        modified_payload = f"grant_type=client_credentials&client_id={config.vectara_token.client_id}&client_secret={config.vectara_token.client_secret}"

        return await __reverse_proxy(
            request,
            f"https://vectara-prod-{config.vectara_token.customer_id}.auth.us-west-2.amazoncognito.com",
            payload=modified_payload.encode("utf-8"),
            remove_path="/vectara"
        )
    else:
        return await __reverse_proxy(
            request,
            "https://api.vectara.io",
            customer_id=config.vectara_token.customer_id,
            remove_path="/vectara"
        )


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "HEAD", "DELETE", "PUT", "CONNECT", "OPTIONS", "TRACE", "PATCH"]
)
async def catch_all(request: Request, path: str, response: Response):
    authorization = request.headers.get("authorization")
    if authorization is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    split = authorization.split(' ')

    if len(split) != 2:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return response

    auth_type, auth_value = split

    match auth_value:
        case "openai":
            return await __reverse_proxy(request, "https://api.openai.com/v1", config.openai_api_key)
        case "cohere":
            return await __reverse_proxy(request, "https://api.cohere.ai", config.cohere_api_key)
        case "anyscale":
            return await __reverse_proxy(request, "https://api.endpoints.anyscale.com/v1", config.anyscale_api_key)
        case "huggingface":
            return await __reverse_proxy(request, "https://api-inference.huggingface.co", config.huggingface_api_key)
        case _:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response


async def __reverse_proxy(
    request: Request,
    new_url: str,
    bearer_key: Optional[str] = None,
    payload: Optional[bytes] = None,
    customer_id: Optional[str] = None,
    remove_path: Optional[str] = None
):
    parsed_url = urlparse(new_url)
    query = request.url.query
    if customer_id and query:
        query = parse_qs(query)
        query["c"] = [customer_id]
        query = "&".join([f"{k}={v[0]}" for k, v in query.items()])
    request_path = request.url.path
    if remove_path is not None:
        request_path = request_path.replace(remove_path, "")
    new_path = parsed_url.path + request_path
    url = httpx.URL(url=f"{parsed_url.scheme}://{parsed_url.netloc}", path=parsed_url.path + new_path,
                    query=query.encode("utf-8"))
    headers = request.headers.mutablecopy()
    headers["host"] = parsed_url.netloc
    if bearer_key is not None:
        headers["authorization"] = f"Bearer {bearer_key}"

    if customer_id is not None:
        headers["customer-id"] = customer_id

    if payload is not None:
        del headers["content-length"]
        rp_req = client.build_request(request.method, url,
                                      headers=headers.raw,
                                      content=payload, timeout=None)
    else:
        rp_req = client.build_request(request.method, url,
                                      headers=headers.raw,
                                      content=request.stream(), timeout=None)
    rp_resp = await client.send(rp_req, stream=True)

    return StreamingResponse(
        rp_resp.aiter_raw(),
        status_code=rp_resp.status_code,
        headers=rp_resp.headers,
        background=BackgroundTask(rp_resp.aclose),
    )


def start():
    import uvicorn
    base_url = urlparse(config.base_url)
    uvicorn.run(app, host=base_url.hostname, port=base_url.port)
