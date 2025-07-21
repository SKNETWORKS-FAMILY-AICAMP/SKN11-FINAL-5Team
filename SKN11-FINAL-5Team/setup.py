from setuptools import setup, find_packages

setup(
    name="task_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'google-auth',
        'google-api-python-client',
    ],
)