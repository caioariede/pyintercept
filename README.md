# pyintercept
Intercept function calls from Python scripts

# Example

```bash
python -m pyintercept setup.py setuptools.setup --args=install --handler=pyintercept.print
```

```javascript
{"name": "pyintercept", "license": "MIT", "author": "Caio Ariede", "author_email": "caio.ariede gmail.com", "include_package_data": true, "url": "http://github.com/caioariede/pyintercept", "version": "0.1", "zip_safe": false, "platforms": ["any"], "install_requires": ["byteplay"], "packages": ["pyintercept", "pyintercept.handlers"], "classifiers": ["Intended Audience :: Developers", "Operating System :: OS Independent", "License :: OSI Approved :: MIT License", "Programming Language :: Python", "Programming Language :: Python :: 3", "Programming Language :: Python :: 3.4"], "description": "Intercept function calls from Python scripts"}
```
