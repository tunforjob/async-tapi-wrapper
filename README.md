# Async-Tapi-Wrapper
![Supported Python Versions](https://img.shields.io/static/v1?label=python&message=>=3.6&color=blue)
[![GitHub license](https://img.shields.io/badge/license-MIT-green.svg)](https://raw.githubusercontent.com/vintasoftware/tapioca-wrapper/master/LICENSE)
[![Downloads](https://pepy.tech/badge/tapi-wrapper)](https://pepy.tech/project/tapi-yandex-metrika)
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

It's an async fork of [tapi-wrapper](https://github.com/pavelmaksimov/tapi-wrapper) library.

Tapioca helps you generating Python clients for APIs.
APIs wrapped by Tapioca are explorable and follow a simple interaction pattern that works uniformly so developers don't need to learn how to use a new coding interface/style for each service API.


### Api examples
[Async Yandex Metrika API](https://github.com/ilindrey/async-tapi-yandex-metrika)

[Yandex Direct API](https://github.com/pavelmaksimov/tapi-yandex-direct)


### Installed
    pip install async-tapi-wrapper

### Usage

First, you need to set up the mapping of the resources you want to work with:

```python
RESOURCE_MAPPING = {
    "test": {
        "resource": "test/{number}/",
        "docs": "http://test.com/docs",
        "spam": "eggs",
        "foo": "bar",
    },
}
```

Then create an adapter class that will work with resources:
```python
from async_tapi.adapters import TAPIAdapter

class TestClientAdapter(TAPIAdapter):
    serializer_class = ...  # default SimpleSerializer
    api_root = "https://api.test.com"
    resource_mapping = RESOURCE_MAPPING
```

Generate a class-based wrapper using `generate_wrapper_from_adapter`:
```python
from async_tapi.adapters import generate_wrapper_from_adapter

TestClient = generate_wrapper_from_adapter(TestClientAdapter)
```

Using:

```python
async with TestClient(**some_params) as client:
    
    response = await client.test(number=...).get(data=..., 
                                                 params=...,
                                                 debug=True)
    
    response = await client.test(number=...).post(data=..., 
                                                  params=..., 
                                                  debug=True)
    
    responses = await client.test(number=...).post_batch(data=[..., ...], 
                                                         params=..., 
                                                         debug=True)
```

You can also specify a resource mapping and serializer when creating an instance of the class:
```python

async with TestClient(resource_mapping=RESOURCE_MAPPING, 
                      serializer_class=..., 
                      **some_params,
                      ) as client:
    ...
```

### Help
Telegram: [Pavel Maksimow](https://t.me/pavel_maksimow), [Andrey Ilin](https://t.me/ilindrey)

Facebook: [Pavel Maksimow](https://www.facebook.com/pavel.maksimow)

### Authors
The author of this modification Pavel Maksimov
___
Powered by [Tapioca-Wrapper](https://github.com/vintasoftware/tapi-wrapper)

Copyright (c) 2013-2015 Vinta Software