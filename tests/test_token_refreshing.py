import pytest
from aioresponses import aioresponses, CallbackResult

from async_tapi.exceptions import ClientError
from tests.client import TesterClient, TokenRefreshClient, FailTokenRefreshClient


default_params = {"token": "token", "refresh_token_by_default": True}


def callback_401(*args, **kwargs):
    return CallbackResult(status=401)


def callback_201(*args, **kwargs):
    return CallbackResult(status=201)


async def test_not_token_refresh_client_propagates_client_error():
    async with TesterClient() as no_refresh_client:
        with aioresponses() as mocked:
            mocked.post(
                no_refresh_client.test().data,
                callback=callback_401,
            )

            with pytest.raises(ClientError):
                await no_refresh_client.test().post()


async def test_disable_token_refreshing():
    async with TokenRefreshClient(**default_params) as client:
        with aioresponses() as mocked:
            mocked.post(
                client.test().data,
                callback=callback_401,
            )

            with pytest.raises(ClientError):
                await client.test().post(refresh_token=False)


async def test_token_expired_automatically_refresh_authentication():
    async with TokenRefreshClient(**default_params) as client:
        with aioresponses() as mocked:

            mocked.post(
                client.test().data,
                callback=callback_401,
                content_type="application/json",
            )

            mocked.post(
                client.test().data,
                callback=callback_201,
                content_type="application/json",
            )

            response = await client.test().post()

            # refresh_authentication method should be able to update api_params
            assert response._api_params["token"] == "new_token"


async def test_stores_refresh_authentication_method_response_for_further_access():
    async with TokenRefreshClient(**default_params) as client:
        with aioresponses() as mocked:

            mocked.post(
                client.test().data,
                callback=callback_401,
                content_type="application/json",
            )

            mocked.post(
                client.test().data,
                callback=callback_201,
                content_type="application/json",
            )

            response = await client.test().post()

            assert response().refresh_data == "new_token"


async def test_raises_error_if_refresh_authentication_method_returns_falsy_value():
    async with FailTokenRefreshClient(**default_params) as client:
        with aioresponses() as mocked:

            mocked.post(
                client.test().data,
                callback=callback_401,
                content_type="application/json",
            )

            with pytest.raises(ClientError):
                await client.test().post()
