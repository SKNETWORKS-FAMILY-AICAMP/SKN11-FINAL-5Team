from setuptools import setup, find_packages

setup(
    name="unified_agent_system",
    version="0.1.0",
    packages=find_packages(include=[
        'mental_agent*',
        'marketing_agent*',
        'customer_service_agent*',
        'buisness_planning_agent*',
        'task_agent*',
        'shared_modules*'
    ]),
    install_requires=[
        'google-auth',
        'google-api-python-client',
        'fastapi',
        'uvicorn',
        'pydantic',
    ],
)