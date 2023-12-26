import os
from typing import Optional
from urllib.parse import urlparse

import httpx
import pyjson5
from fastapi import FastAPI, Request, Response, status
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse


class Config:
    base_url: str
    openai_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None

    def __init__(self):
        self.base_url = os.environ.get("BASE_URL", default="http://127.0.0.1:8000")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.cohere_api_key = os.environ.get("CO_API_KEY")


def generate_env(_dict: dict[str, str]) -> str:
    """
    Generate a bash compatible environment exports according to string dictionary.
    """

    s = ""
    for k, v in _dict.items():
        s += f"export {k}=\"{v}\"\n"

    return s


user_env: dict[str, str] = dict()
config = Config()
if config.openai_api_key:
    user_env["OPENAI_BASE_URL"] = config.base_url
    user_env["OPENAI_API_KEY"] = "openai"
if config.cohere_api_key:
    user_env["CO_API_URL"] = config.base_url
    user_env["CO_API_KEY"] = "cohere"

with open("generated-keys.env", "w") as f:
    f.write(generate_env(user_env))
print("Please run bash command `source generated-keys.env` for easy key management.")

app = FastAPI()

client = httpx.AsyncClient()


@app.api_route("/{path:path}", methods=["GET", "POST"])
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
            return await __reverse_proxy(request, "https://api.openai.com/v1/", config.openai_api_key)
        case "cohere":
            return await __reverse_proxy(request, "https://api.cohere.ai", config.cohere_api_key)

        case _:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response


async def __reverse_proxy(request: Request, new_url: str, bearer_key: str):
    parsed_url = urlparse(new_url)
    url = httpx.URL(url=f"{parsed_url.scheme}://{parsed_url.netloc}", path=parsed_url.path + request.url.path,
                    query=request.url.query.encode("utf-8"))
    headers = request.headers.mutablecopy()
    headers["host"] = parsed_url.netloc
    headers["authorization"] = f"Bearer {bearer_key}"

    rp_req = client.build_request(request.method, url,
                                  headers=headers.raw,
                                  content=request.stream())
    rp_resp = await client.send(rp_req, stream=True)

    return StreamingResponse(
        rp_resp.aiter_raw(),
        status_code=rp_resp.status_code,
        headers=rp_resp.headers,
        background=BackgroundTask(rp_resp.aclose),
    )
