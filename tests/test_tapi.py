import pytest
from aioresponses import aioresponses, CallbackResult

from tapi2.adapters import Resource
from tapi2.exceptions import ClientError, ServerError
from tests.client import TesterClient


"""
tests TapiClient
"""


async def test_added_custom_resources():
    resource_mapping = [
        Resource("myresource", "http://url.ru/myresource"),
        Resource("myresource2", "https://url.ru/myresource2"),
    ]
    async with TesterClient(resource_mapping=resource_mapping) as client:
        with aioresponses() as mocked:
            mocked.get(
                url=client.myresource().data,
                body="[]",
                status=200,
                content_type="application/json",
            )

            response = await client.myresource().get()
            assert response.data == []


async def test_in_operator():
    async with TesterClient() as client:
        with aioresponses() as mocked:

            mocked.get(
                client.test().data,
                body='{"data": 1, "other": 2}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            assert "data" in response
            assert "other" in response
            assert "wat" not in response


async def test_accessing_index_out_of_bounds_should_raise_index_error():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='["a", "b", "c"]',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            with pytest.raises(IndexError):
                response[3]


async def test_accessing_empty_list_should_raise_index_error():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body="[]",
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            with pytest.raises(IndexError):
                response[3]


async def test_fill_url_template():
    expected_url = "https://api.test.com/user/123/"

    client = TesterClient()
    resource = client.user(id="123")

    assert resource.data == expected_url


async def test_fill_another_root_url_template():
    expected_url = "https://api.another.com/another-root/"

    client = TesterClient()
    resource = client.another_root()

    assert resource.data == expected_url


async def test_calling_len_on_tapioca_list():
    client = TesterClient()
    client = client._wrap_in_tapi([0, 1, 2])
    assert len(client) == 3


async def test_iterated_client_items():
    client = TesterClient()
    client = client._wrap_in_tapi([0, 1, 2])

    for i, item in enumerate(client):
        assert item == i


async def test_client_data_dict():
    client = TesterClient()
    client = client._wrap_in_tapi({"data": 0})

    assert client["data"] == 0
    assert client.data == {"data": 0}


async def test_client_data_list():
    client = TesterClient()
    client = client._wrap_in_tapi([0, 1, 2])

    assert client[0] == 0
    assert client[1] == 1


async def test_fill_url_from_default_params():
    client = TesterClient(default_url_params={"id": 123})
    assert client.user().data == "https://api.test.com/user/123/"


"""
tests TapiExecutor
"""


async def test_resource_executor_data_should_be_composed_url():
    expected_url = "https://api.test.com/test/"

    client = TesterClient()
    resource = client.test()

    assert resource.data == expected_url


async def test_docs():
    client = TesterClient()
    assert "\n".join(client.resource.__doc__.split("\n")[1:]) == (
        "Resource: " + client.resource._resource["resource"] + "\n"
        "Docs: " + client.resource._resource["docs"] + "\n"
        "Foo: " + client.resource._resource["foo"] + "\n"
        "Spam: " + client.resource._resource["spam"]
    )


async def test_cannot__getittem__():
    client = TesterClient()
    client = client._wrap_in_tapi([0, 1, 2])
    with pytest.raises(Exception):
        client()[0]


async def test_cannot_iterate():
    client = TesterClient()
    client = client._wrap_in_tapi([0, 1, 2])
    with pytest.raises(Exception):
        for item in client():
            pass


async def test_dir_call_returns_executor_methods():
    client = TesterClient()
    client = client._wrap_in_tapi([0, 1, 2])

    e_dir = dir(client())

    assert "data" in e_dir
    assert "response" in e_dir
    assert "get" in e_dir
    assert "post" in e_dir
    assert "pages" in e_dir
    assert "open_docs" in e_dir
    assert "open_in_browser" in e_dir


async def test_response_executor_object_has_a_response():
    next_url = "http://api.teste.com/next_batch"
    async with TesterClient() as client:
        with aioresponses() as mocked:

            mocked.get(
                client.test().data,
                body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}'
                % next_url,
                status=200,
                content_type="application/json",
            )

            mocked.get(
                next_url,
                body='{"data": [{"key": "value"}], "paging": {"next": ""}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()
            executor = response()

            executor.response

            executor._response = None


async def test_raises_error_if_executor_does_not_have_a_response_object():
    client = TesterClient()

    with pytest.raises(Exception):
        client().response


async def test_response_executor_has_a_status_code():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            assert response().status == 200


"""
tests TapiExecutorRequests
"""


async def test_when_executor_has_no_response():
    client = TesterClient()
    with pytest.raises(Exception) as context:
        client.test().response

        exception = context.exception

        assert "has no response" == str(exception)


async def test_get_request():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            assert response().data == {"data": {"key": "value"}}


async def test_access_response_field():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            assert response.data == {"data": {"key": "value"}}


async def test_post_request():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.post(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=201,
                content_type="application/json",
            )

            response = await client.test().post()

            assert response().data == {"data": {"key": "value"}}


async def test_put_request():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.put(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=201,
                content_type="application/json",
            )

            response = await client.test().put()

            assert response().data == {"data": {"key": "value"}}


async def test_patch_request():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.patch(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=201,
                content_type="application/json",
            )

            response = await client.test().patch()

            assert response().data == {"data": {"key": "value"}}


async def test_delete_request():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.delete(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=201,
                content_type="application/json",
            )

            response = await client.test().delete()

            assert response().data == {"data": {"key": "value"}}


async def test_carries_request_kwargs_over_calls():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"data": {"key": "value"}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            assert "url" in response._request_kwargs
            assert "data" in response._request_kwargs
            assert "headers" in response._request_kwargs


async def test_thrown_tapi_exception_with_client_error_data():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"error": "bad request test"}',
                status=400,
                content_type="application/json",
            )
            with pytest.raises(ClientError) as client_exception:
                await client.test().get()
            assert "bad request test" in client_exception.value.args


async def test_thrown_tapi_exception_with_servererror_data():
    async with TesterClient() as client:
        with aioresponses() as mocked:
            mocked.get(
                client.test().data,
                body='{"error": "server error test"}',
                status=500,
                content_type="application/json",
            )
            with pytest.raises(ServerError) as server_exception:
                await client.test().get()
            assert "server error test" in server_exception.value.args


"""
tests IteratorFeatures
"""


async def test_simple_pages_iterator():
    next_url = "http://api.teste.com/next_batch"
    async with TesterClient() as client:
        with aioresponses() as mocked:

            mocked.get(
                client.test().data,
                body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}'
                % next_url,
                status=200,
                content_type="application/json",
            )

            mocked.get(
                next_url,
                body='{"data": [{"key": "value"}], "paging": {"next": ""}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            iterations_count = 0
            async for item in response().pages():
                assert item["key"] in "value"
                iterations_count += 1

            assert iterations_count == 2


async def test_simple_pages_with_max_items_iterator():
    next_url = "http://api.teste.com/next_batch"
    async with TesterClient() as client:
        with aioresponses() as mocked:

            mocked.get(
                client.test().data,
                body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}'
                % next_url,
                status=200,
                content_type="application/json",
            )

            mocked.get(
                next_url,
                body='{"data": [{"key": "value"}, {"key": "value"}, {"key": "value"}], "paging": {"next": ""}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            iterations_count = 0
            async for item in response().iter_items(max_items=3, max_pages=2):
                assert item["key"] == "value"
                iterations_count += 1

            assert iterations_count == 3


async def test_simple_pages_with_max_pages_iterator():
    next_url = "http://api.teste.com/next_batch"
    async with TesterClient() as client:
        with aioresponses() as mocked:

            mocked.get(
                client.test().data,
                body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}'
                % next_url,
                status=200,
                content_type="application/json",
            )
            mocked.get(
                next_url,
                body='{"data": [{"key": "value"}, {"key": "value"}, {"key": "value"}], "paging": {"next": '
                '"%s"}}' % next_url,
                status=200,
                content_type="application/json",
            )

            mocked.get(
                next_url,
                body='{"data": [{"key": "value"}, {"key": "value"}, {"key": "value"}], "paging": {"next": '
                '"%s"}}' % next_url,
                status=200,
                content_type="application/json",
            )

            mocked.get(
                next_url,
                body='{"data": [{"key": "value"}, {"key": "value"}, {"key": "value"}], "paging": {"next": '
                '""}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            iterations_count = 0
            async for item in response().iter_items(max_pages=3):
                assert item["key"] in "value"
                iterations_count += 1

            assert iterations_count == 7


async def test_simple_pages_max_page_zero_iterator():
    next_url = "http://api.teste.com/next_batch"

    async with TesterClient() as client:
        with aioresponses() as mocked:

            mocked.get(
                client.test().data,
                body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}'
                % next_url,
                status=200,
                content_type="application/json",
            )

            mocked.get(
                next_url,
                body='{"data": [{"key": "value"}], "paging": {"next": ""}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            iterations_count = 0
            async for item in response().pages(max_pages=0):
                assert item.key().data in "value"
                iterations_count += 1

            assert iterations_count == 0


async def test_simple_pages_max_item_zero_iterator():
    next_url = "http://api.teste.com/next_batch"
    async with TesterClient() as client:
        with aioresponses() as mocked:

            mocked.get(
                client.test().data,
                body='{"data": [{"key": "value"}], "paging": {"next": "%s"}}'
                % next_url,
                status=200,
                content_type="application/json",
            )

            mocked.get(
                next_url,
                body='{"data": [{"key": "value"}], "paging": {"next": ""}}',
                status=200,
                content_type="application/json",
            )

            response = await client.test().get()

            iterations_count = 0
            async for item in response().iter_items(max_items=0):
                assert item.key().data in "value"
                iterations_count += 1

            assert iterations_count == 0
