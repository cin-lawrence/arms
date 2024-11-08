from aiohttp.client_exceptions import ClientResponseError

from .models.errors import ResponseError


class ClientError(Exception):
    def __init__(
        self,
        err: ClientResponseError,
        payload: ResponseError | str,
    ) -> None:
        self.request_info = err.request_info
        self.status = err.status
        self.message = err.message
        self.headers = err.headers
        self.history = err.history
        self.args = err.args
        self.payload = payload


class ClientInternalError(ClientError): ...


class ClientNotAuthenticatedError(ClientError): ...
