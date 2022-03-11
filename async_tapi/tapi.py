import copy
import json
import asyncio
import aiohttp
import webbrowser
from collections import OrderedDict

from .exceptions import ResponseProcessException


class TAPIInstaller:
    def __init__(self, adapter_class):
        self.adapter_class = adapter_class

    def __call__(
        self, serializer_class=None, session=None, resource_mapping=None, **kwargs
    ):
        refresh_token_default = kwargs.pop("refresh_token_by_default", False)
        return TAPIClient(
            self.adapter_class(
                serializer_class=serializer_class,
                resource_mapping=resource_mapping,
            ),
            api_params=kwargs,
            refresh_token_by_default=refresh_token_default,
            session=session,
        )


class TAPIClient:
    def __init__(
        self,
        api,
        data=None,
        response=None,
        request_kwargs=None,
        api_params=None,
        resource=None,
        refresh_token_by_default=False,
        refresh_data=None,
        session=None,
        store=None,
        resource_name=None,
        *args,
        **kwargs,
    ):
        self._api = api
        self._data = data
        self._response = response
        self._api_params = api_params or {}
        self._request_kwargs = request_kwargs
        self._resource = resource
        self._resource_name = resource_name
        self._refresh_token_default = refresh_token_by_default
        self._refresh_data = refresh_data
        self._session = session
        self.store = store or {}

    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._session is not None:
            await self._session.close()

    @property
    def data(self):
        return self._data

    @property
    def request_kwargs(self):
        return self._request_kwargs

    @property
    def response(self):
        return self._response

    @property
    def status(self):
        return self.response.status

    def _satiate_api(self):
        serializer_class = None
        if self._api.serializer:
            serializer_class = self._api.serializer.__class__
        return self._api.__class__(serializer_class=serializer_class)

    def _wrap_in_tapi(self, data, *args, **kwargs):
        request_kwargs = kwargs.pop("request_kwargs", self._request_kwargs)
        response = kwargs.pop("response", self._response)
        resource_name = kwargs.pop("resource_name", self._resource_name)
        return TAPIClient(
            self._satiate_api(),
            data=data,
            api_params=self._api_params,
            response=response,
            request_kwargs=request_kwargs,
            refresh_token_by_default=self._refresh_token_default,
            refresh_data=self._refresh_data,
            resource_name=resource_name,
            session=self._session,
            store=self.store,
            *args,
            **kwargs,
        )

    def _wrap_in_tapi_executor(self, data, *args, **kwargs):
        request_kwargs = kwargs.pop("request_kwargs", self._request_kwargs)
        return TAPIClientExecutor(
            self._satiate_api(),
            data=data,
            api_params=self._api_params,
            request_kwargs=request_kwargs,
            refresh_token_by_default=self._refresh_token_default,
            refresh_data=self._refresh_data,
            resource_name=self._resource_name,
            session=self._session,
            store=self.store,
            *args,
            **kwargs,
        )

    def _get_doc(self):
        resources = copy.copy(self._resource)
        docs = (
            "Automatic generated __doc__ from resource_mapping.\n"
            "Resource: %s\n"
            "Docs: %s\n" % (resources.pop("resource", ""), resources.pop("docs", ""))
        )
        for key, value in sorted(resources.items()):
            docs += "%s: %s\n" % (key.title(), value)
        docs = docs.strip()
        return docs

    __doc__ = property(_get_doc)

    def __call__(self, *args, **kwargs):
        data = self._data

        url_params = self._api_params.get("default_url_params", {})
        url_params.update(kwargs)
        if self._resource and url_params:
            data = self._api.fill_resource_template_url(
                self._data, url_params, self._resource_name
            )

        return self._wrap_in_tapi_executor(
            data, resource=self._resource, response=self._response
        )

    """
    Convert a snake_case string in CamelCase.
    http://stackoverflow.com/questions/19053707/convert-snake-case-snake-case-to-lower-camel-case-lowercamelcase-in-python
    """

    def _to_camel_case(self, name):
        if isinstance(name, int):
            return name
        components = name.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def _get_client_from_name(self, name):
        # if could not access, falback to resource mapping
        resource_mapping = self._api.resource_mapping
        if name in resource_mapping:
            resource = resource_mapping[name]
            api_root = self._api.get_api_root(self._api_params, resource_name=name)
            url = api_root.rstrip("/") + "/" + resource["resource"].lstrip("/")
            return self._wrap_in_tapi(url, resource=resource, resource_name=name)

        if name in self.store:
            return self.store[name]

        return None

    def _get_client_from_name_or_fallback(self, name):
        client = self._get_client_from_name(name)
        if client is not None:
            return client

        camel_case_name = self._to_camel_case(name)
        client = self._get_client_from_name(camel_case_name)
        if client is not None:
            return client

        normal_camel_case_name = camel_case_name[0].upper()
        normal_camel_case_name += camel_case_name[1:]

        client = self._get_client_from_name(normal_camel_case_name)
        if client is not None:
            return client

        return None

    def __getattr__(self, name):
        ret = self._get_client_from_name_or_fallback(name)
        if ret is None:
            raise AttributeError(f"Undeclared resource '{name}'")
        return ret

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        self._it = iter(self._data)
        return self

    def __next__(self):
        return next(self._it)

    def __dir__(self):
        if self._api and self._data is None:
            return list(self._api.resource_mapping.keys())

        return list(self.store.keys()) + ["data", "response", "store"]

    def __str__(self):
        try:
            return self._api.__str__(
                self._data, self._request_kwargs, self._response, self._api_params
            )
        except NotImplementedError:
            if type(self._data) == OrderedDict:
                return "<{} object, printing as dict:\n" "{}>".format(
                    self.__class__.__name__, json.dumps(self._data, indent=4)
                )
            else:
                import pprint

                pp = pprint.PrettyPrinter(indent=4)
                return "<{} object\n" "{}>".format(
                    self.__class__.__name__, pp.pformat(self._data)
                )

    def _repr_pretty_(self, p, cycle):
        p.text(self.__str__())

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data


class TAPIClientExecutor(TAPIClient):
    def __init__(self, api, *args, **kwargs):
        super().__init__(api, *args, **kwargs)

    def __getitem__(self, key):
        raise Exception(
            "This operation cannot be done on a" + " TAPIClientExecutor object"
        )

    def __iter__(self):
        raise Exception("Cannot iterate over a TAPIClientExecutor object")

    def __getattr__(self, name):
        if name.startswith("to_") or name in self._api.native_methods:
            return self._api._get_to_native_method(name, self._data, **self._context())
        raise AttributeError(name)

    def __call__(self, *args, **kwargs):
        return self._wrap_in_tapi(self._data.__call__(*args, **kwargs))

    @property
    def request_kwargs(self):
        return self._request_kwargs

    @property
    def data(self):
        return self._data

    @property
    def response(self):
        if self._response is None:
            raise Exception("This instance has no response object")
        return self._response

    @property
    def status(self):
        return self.response.status

    @property
    def refresh_data(self):
        return self._refresh_data

    def _context(self, **kwargs):
        return {
            "response": self._response,
            "request_kwargs": self._request_kwargs,
            "api_params": self._api_params,
            "store": self.store,
            "client": self,
            "resource_name": self._resource_name,
            **kwargs,
        }

    async def _make_request(
        self, request_method, refresh_token=None, repeat_number=0, *args, **kwargs
    ):
        if "url" not in kwargs:
            kwargs["url"] = self._data

        request_kwargs = self._api.get_request_kwargs(
            self._api_params, request_method, *args, **kwargs
        )

        response_data = None
        response = await self._session.request(request_method, **request_kwargs)
        try:
            response_data = await self._api.process_response(
                **self._context(response=response, request_kwargs=request_kwargs)
            )
        except ResponseProcessException as e:
            repeat_number += 1
            client = self._wrap_in_tapi(
                e.data, response=response, request_kwargs=request_kwargs
            )
            context = self._context(
                response=response, request_kwargs=request_kwargs, client=client
            )
            error_message = await self._api.get_error_message(
                data=e.data, response=response
            )
            tapi_exception = e.tapi_exception(message=error_message, client=client)

            should_refresh_token = (
                refresh_token is not False and self._refresh_token_default
            )
            auth_expired = self._api.is_authentication_expired(
                tapi_exception, **context
            )

            if should_refresh_token and auth_expired:
                self._refresh_data = self._api.refresh_authentication(**context)
                if self._refresh_data:
                    return await self._make_request(
                        request_method,
                        refresh_token=False,
                        repeat_number=repeat_number,
                        *args,
                        **kwargs,
                    )

            if self._api.retry_request(
                tapi_exception, error_message, repeat_number, **context
            ):
                return await self._make_request(
                    request_method,
                    refresh_token=False,
                    repeat_number=repeat_number,
                    *args,
                    **kwargs,
                )

            self._api.error_handling(
                tapi_exception, error_message, repeat_number, **context
            )

        return self._wrap_in_tapi(
            response_data, response=response, request_kwargs=request_kwargs
        )

    async def _send(self, request_method, *args, **kwargs):
        debug = kwargs.pop("debug") if "debug" in kwargs else False
        response = await self._make_request(request_method, *args, **kwargs)
        if debug:
            response_info = "status: {} - response data: {}".format(
                response.status, response.data
            )
            print(response_info)
        return response

    async def _send_batch(self, request_method, *args, **kwargs):

        data = kwargs.pop("data") if "data" in kwargs else []
        semaphore = kwargs.pop("semaphore") if "semaphore" in kwargs else 1

        async with asyncio.Semaphore(semaphore):
            results = await asyncio.gather(
                *[
                    self._send(
                        request_method, *args, **{**kwargs, "data": row}
                    )
                    for row in data
                ]
            )

        return results

    async def get(self, *args, **kwargs):
        return await self._send("GET", *args, **kwargs)

    async def post(self, *args, **kwargs):
        return await self._send("POST", *args, **kwargs)

    async def options(self, *args, **kwargs):
        return await self._send("OPTIONS", *args, **kwargs)

    async def put(self, *args, **kwargs):
        return await self._send("PUT", *args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await self._send("PATCH", *args, **kwargs)

    async def delete(self, *args, **kwargs):
        return await self._send("DELETE", *args, **kwargs)

    async def post_batch(self, *args, **kwargs):
        return await self._send_batch("POST", *args, **kwargs)

    async def options_batch(self, *args, **kwargs):
        return await self._send_batch("OPTIONS", *args, **kwargs)

    async def put_batch(self, *args, **kwargs):
        return await self._send_batch("PUT", *args, **kwargs)

    async def patch_batch(self, *args, **kwargs):
        return await self._send_batch("PATCH", *args, **kwargs)

    async def delete_batch(self, *args, **kwargs):
        return await self._send_batch("DELETE", *args, **kwargs)

    def _get_iterator_next_request_kwargs(self):
        return self._api.get_iterator_next_request_kwargs(
            response_data=self._data, **self._context()
        )

    def _get_iterator_iteritems(self):
        return self._api.get_iterator_iteritems(
            response_data=self._data, **self._context()
        )

    def _get_iterator_pages(self):
        return self._api.get_iterator_pages(response_data=self._data, **self._context())

    def _get_iterator_items(self):
        return self._api.get_iterator_items(data=self._data, **self._context())

    @staticmethod
    def _reached_max_limit(page_count, item_count, max_pages, max_items):
        reached_page_limit = max_pages is not None and max_pages <= page_count
        reached_item_limit = max_items is not None and max_items <= item_count
        return reached_page_limit or reached_item_limit

    async def iter_items(self, max_pages=None, max_items=None):
        executor = self
        iterator_list = executor._get_iterator_iteritems()
        page_count = 0
        item_count = 0

        while iterator_list:
            if self._reached_max_limit(page_count, item_count, max_pages, max_items):
                break

            for item in iterator_list:
                if self._reached_max_limit(
                    page_count, item_count, max_pages, max_items
                ):
                    break
                yield item
                item_count += 1

            page_count += 1

            next_request_kwargs = executor._get_iterator_next_request_kwargs()

            if not next_request_kwargs:
                break

            request_method = executor.response.method.lower()
            method = getattr(self, request_method)
            response = await method(**next_request_kwargs)
            executor = response()
            iterator_list = executor._get_iterator_iteritems()

    async def pages(self, max_pages=None):
        executor = self
        pages = executor._get_iterator_pages()
        page_count = 0

        while pages:
            for page in pages:
                if self._reached_max_limit(page_count, None, max_pages, None):
                    break
                yield self._wrap_in_tapi(page)
                page_count += 1

            next_request_kwargs = executor._get_iterator_next_request_kwargs()

            if not next_request_kwargs or self._reached_max_limit(
                page_count, None, max_pages, None
            ):
                break

            request_method = executor.response.method.lower()
            method = getattr(self, request_method)
            response = await method(**next_request_kwargs)
            executor = response()
            pages = executor._get_iterator_pages()

    def items(self, max_items=None):
        items = self._get_iterator_items()
        item_count = 0

        for item in items:
            if self._reached_max_limit(None, item_count, None, max_items):
                break
            yield item
            item_count += 1

    def open_docs(self):
        if not self._resource:
            raise KeyError()

        new = 2  # open in new tab
        webbrowser.open(self._resource["docs"], new=new)

    def open_in_browser(self):
        new = 2  # open in new tab
        webbrowser.open(self._data, new=new)

    def help(self):
        if not self._resource:
            raise KeyError("Resource {} not registered".format(self._resource))

        help_info = ""

        if self._resource.get("docs"):
            help_info += "Documentation: {}".format(self._resource["docs"])

        if self._resource.get("resource"):
            help_info += "\nResource path: {}".format(self._resource["resource"])

        if self._resource.get("description"):
            help_info += "\nDescription:"
            help_info += "\n{}".format(self._resource["description"])

        if self._resource.get("methods"):
            help_info += "\nAvailable HTTP methods:"
            help_info += "\n{}".format(self._resource["methods"])

        if self._resource.get("params"):
            help_info += "\nAvailable query parameters:"
            help_info += "\n{}".format(self._resource["params"])

        print(help_info)

        return help_info

    def __dir__(self):
        methods = [
            m for m in TAPIClientExecutor.__dict__.keys() if not m.startswith("_")
        ]
        methods += [m for m in dir(self._api.serializer) if m.startswith("to_")]
        methods += self._api.native_methods

        return methods
