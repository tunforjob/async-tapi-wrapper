import pytest
from aioresponses import aioresponses

from async_tapi.adapters import TAPIAdapter

from tests.client import TesterClient


def test_fill_resource_template_url():
    adapter = TAPIAdapter()

    template = "{country}/{city}"
    resource = "point"

    url = adapter.fill_resource_template_url(
        template, {"city": "Moscow", "country": "Russia"}, resource
    )
    assert url == "Russia/Moscow"

    with pytest.raises(TypeError):
        adapter.fill_resource_template_url(template, {}, resource)


def test_fill_resource_template_url_exception():
    adapter = TAPIAdapter()

    template = "{country}/{city}"
    resource = "point"

    try:
        adapter.fill_resource_template_url(template, {}, resource)
    except BaseException as exc:
        assert exc.args == ("point() missing 2 required url params: 'city', 'country'",)


async def test_json_response_to_native():

    async with TesterClient() as client:

        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=200,
                content_type="application/json",
            )
            response = await client.test().get()
            assert isinstance(response.data, dict)

        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=200,
                content_type="text/html",
            )
            response = await client.test().get()
            assert isinstance(response.data, dict)

        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"data": {"key": "value"}}error',
                status=200,
                content_type="text/html",
            )
            response = await client.test().get()
            assert isinstance(response.data, str)

        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"data": {"key": "value"}}error',
                status=200,
                content_type="application/json",
            )
            response = await client.test().get()
            assert isinstance(response.data, str)
