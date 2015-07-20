# pyintercept
Intercept function calls from Python scripts

# Example

```bash
pyintercept setup.py --args="install" --function=setuptools.setup --handler=pyintercept.json
```

```javascript
{'package_data': {'location_field': ['static/location_field/js/*', 'templates/locati...
```
