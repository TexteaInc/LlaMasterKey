import os
import fire
import json
import typing
import urllib3


local_configure_file = "llamakey_local.env"


class LlaMasterKey:
    @staticmethod
    def env(url: typing.Optional[str] = os.environ.get("BASE_URL", None)):
        """
        Download environment file from server

        :param url: LlaMasterKey server url
        """
        if url:
            response = urllib3.request("GET", url.rstrip("/") + "/lmk/env")
            content = response.data.decode("utf-8")
            if response.status != 200:
                print("LlaMasterKey client encountered an error: \n\n" + content)
                return
            with open(".env", "w") as f:
                f.write(content)
            print(f"Environment file written to `{local_configure_file}`, now run `source {local_configure_file}`")
        else:
            print("Usage: `lmkcli env <url>` or set `BASE_URL` environment variable")

    @staticmethod
    def overwrite_env(url: str):
        """
        Overwrite environment variables with those from server (in Python runtime, not in shell)

        :param url: LlaMasterKey server url
        """
        response = urllib3.request("GET", url.rstrip("/") + "/lmk/env?format=json")
        updated_env = response.data.decode("utf-8")
        os.environ.update(json.loads(updated_env))


def __main__():
    fire.Fire(LlaMasterKey)


if __name__ == "__main__":
    __main__()
