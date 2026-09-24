import httpx

# Nominatim rejects requests without an identifying User-Agent.
_USER_AGENT = "br-taqtile-workshop-agents-eval (https://github.com/indigotech/br-taqtile-workshop-agents-eval)"


def build_http_client() -> httpx.Client:
    return httpx.Client(timeout=10.0, headers={"User-Agent": _USER_AGENT})
