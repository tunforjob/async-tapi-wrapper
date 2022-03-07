class ResponseProcessException(Exception):
    def __init__(self, tapi_exception, data, *args, **kwargs):
        self.tapi_exception = tapi_exception
        self.data = data
        super().__init__(*args, **kwargs)


class TAPIException(Exception):
    def __init__(self, message, client):
        self.status = None
        self.client = client
        if client is not None:
            self.status = client().status

        if not message:
            message = "response status code: {}".format(self.status)
        super().__init__(message)


class ClientError(TAPIException):
    def __init__(self, message="", client=None):
        super().__init__(message, client=client)


class ServerError(TAPIException):
    def __init__(self, message="", client=None):
        super().__init__(message, client=client)


class NotFound404Error(TAPIException):
    def __init__(self, message="Error 404 page not found", client=None):
        super().__init__(message, client=client)
