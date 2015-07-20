from setuptools import setup, find_packages


VERSION = '0.1'


setup(
    name='pyintercept',
    version=VERSION,
    description="Intercept function calls from Python scripts",
    author="Caio Ariede",
    author_email="caio.ariede@gmail.com",
    url="http://github.com/caioariede/pyintercept",
    license="MIT",
    zip_safe=False,
    platforms=["any"],
    packages=find_packages(),
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
    ],
    include_package_data=True,
    install_requires=[
        'byteplay',
    ],
)
