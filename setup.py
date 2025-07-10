from setuptools import setup, find_packages

setup(
    name="unprompted",
    version="0.1.3",
    packages=find_packages(),
    install_requires=[],
    author="Robert Haase",
    author_email="robert.haase@uni-leipzig.de",
    description="An AI-assistant which gives unprompted feedback about code helping you to write better code in Jupyter notebooks",
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/haesleinhuepf/unprompted",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
) 