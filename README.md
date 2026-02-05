# URLicon - v0.2.1

`URLicon` helps you to discover an possible icon from a URL.

We check for the metatag `icons`, `favicons` and, if we don't find, we check the
first image in the URL html code. Finally, if nothing is found, we use the
[https://ui-avatars.com/api/](https://ui-avatars.com/api/) to bring you at least
some avatar-like icon.

### How to install and use

Install with `uv` or `pip`
```shell
uv add urlicon
# or
pip urlicon
```

Usage:
```python
from urlicon import urlicon

url = "https://this-is.your-url.com/some-path"

icon_url = urlicon.get_url_icon(url)

print("icon:", icon_url)
# icon: "https://this-is.your-url.com/icon.jpeg"
```

### Caching

`URLicon` use the [unforgettable "cache"](https://github.com/bouli/unforgettable) to avoid unecessary URL requests.
It uses a [temp dir](https://docs.python.org/3/library/tempfile.html) for each
execution. But you can define a your own directory and use the cache as much as
you want setting `SIMPLE_CACHE_ROOT_DIR` env var.

```python
SIMPLE_CACHE_ROOT_DIR = os.getenv("SIMPLE_CACHE_ROOT_DIR", None)
cache = unforgettable(cache_folder=SIMPLE_CACHE_ROOT_DIR)
```

And you can clean the cache with:
```python
urlicon.unforgettable.clean()
```

## See Also

- Github: https://github.com/bouli/urlicon
- PyPI: https://pypi.org/project/urlicon/

## License
This package is distributed under the [MIT license](https://opensource.org/license/MIT).
