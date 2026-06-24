from setuptools import find_packages, setup

setup(
    name="agentbench",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "httpx>=0.27.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "agentbench=agentbench.cli:cli",
        ],
    },
)
