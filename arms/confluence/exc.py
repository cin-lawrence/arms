from aiohttp.client_exceptions import ClientResponseError

from .models.errors import ErrorResponse


class ClientError(Exception):
    def __init__(
        self,
        err: ClientResponseError,
        payload: ErrorResponse | str,
    ):
        self.request_info = err.request_info
        self.status = err.status
        self.message = err.message
        self.headers = err.headers
        self.history = err.history
        self.args = err.args
        self.payload = payload


class ClientInternalError(ClientError):
    ...


class ClientNotAuthenticated(ClientError):
    ...
