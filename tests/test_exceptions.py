import aiohttp
import pytest
from aioresponses import aioresponses

from async_tapi.exceptions import (
    ClientError,
    ServerError,
    ResponseProcessException,
    TAPIException,
)
from async_tapi.tapi import TAPIClient

from tests.client import TesterClient, TesterClientAdapter as ClientAdapter


"""
test TAPIException
"""


async def test_exception_contain_tapi_client():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='',
                status=400,
                content_type="application/json",
            )
            try:
                await client.test().get()
            except TAPIException as e:
                exception = e
            assert exception.client.__class__ is TAPIClient


async def test_exception_contain_status_code():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='',
                status=400,
                content_type="application/json",
            )
            try:
                await client.test().get()
            except TAPIException as e:
                exception = e
            assert exception.status == 400


async def test_exception_message():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='',
                status=400,
                content_type="application/json",
            )

            try:
                await client.test().get()
            except TAPIException as e:
                exception = e
            assert str(exception) == "response status code: 400"


"""
test Exceptions
"""


async def test_adapter_raises_response_process_exception_on_400s():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"erros": "Server Error"}',
                status=400,
                content_type="application/json",
            )
            async with aiohttp.ClientSession() as session:
                response = await session.get(client.test().data)
            with pytest.raises(ResponseProcessException):
                await ClientAdapter().process_response(response, {})


async def test_adapter_raises_response_process_exception_on_500s():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"erros": "Server Error"}',
                status=500,
                content_type="application/json",
            )
            async with aiohttp.ClientSession() as session:
                response = await session.get(client.test().data)
            with pytest.raises(ResponseProcessException):
                await ClientAdapter().process_response(response, {})


async def test_raises_request_error():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=400,
                content_type="application/json",
            )
            with pytest.raises(ClientError):
                await client.test().get()


async def test_raises_server_error():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(client.test().data, status=500, content_type="application/json")
            with pytest.raises(ServerError):
                await client.test().get()
