"""
Setup script for the LinkedIn Automation package.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="linkedin_automation",
    version="0.2.0",
    author="Eduardo Correa",
    author_email="educorrea17@example.com",
    description="LinkedIn automation tool for networking and job applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/educorrea17/linkedu",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "selenium>=4.1.0",
        "webdriver-manager>=3.8.0",
        "argparse>=1.4.0",
    ],
    entry_points={
        "console_scripts": [
            "linkedu=cli:main",
        ],
    },
)