# pyintercept
Intercept function calls from Python scripts

## Installation

`pip install pyintercept`

## Examples

#### Reading information from setup.py files

```bash
python -m pyintercept setup.py setuptools.setup --args=install --handler=pyintercept.print
```

```javascript
{"name": "pyintercept", "license": "MIT", "author": "Caio Ariede", "author_email": "caio.ariede gmail.com", "include_package_data": true, "url": "http://github.com/caioariede/pyintercept", "version": "0.1", "zip_safe": false, "platforms": ["any"], "install_requires": ["byteplay"], "packages": ["pyintercept", "pyintercept.handlers"], "classifiers": ["Intended Audience :: Developers", "Operating System :: OS Independent", "License :: OSI Approved :: MIT License", "Programming Language :: Python", "Programming Language :: Python :: 3", "Programming Language :: Python :: 3.4"], "description": "Intercept function calls from Python scripts"}
```

#### Intercepting functions with pdb

```bash
python -m pyintercept setup.py setuptools.setup --handler=pyintercept.pdb
```

This will call pdb before any calls to `setuptools.setup`

#### Writing your own interceptor

Let's print the settings file to be used in a Django project.

**print_settings.py**

```python
def handler(origfn, *args, **kwargs):
    import os
    print(os.environ["DJANGO_SETTINGS_MODULE"])
```

```bash
python -m pyintercept manage.py django.core.management.execute_from_command_line --handler=print_settings.handler
```

## License

MIT
