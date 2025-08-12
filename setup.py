from setuptools import setup, find_packages

setup(
    name="langgraph_chat",
    version="0.1",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().splitlines(),
)