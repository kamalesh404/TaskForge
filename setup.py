from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="taskforge",
    version="0.1.0",
    author="TaskForge Contributors",
    author_email="dev@taskforge.dev",
    description="Distributed task queue for Python with pluggable backends",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kamalesh404/TaskForge",
    packages=find_packages(include=["src", "src.*", "cli", "cli.*"]),
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "redis": ["redis>=4.0"],
        "rabbitmq": ["pika>=1.3"],
        "dashboard": ["fastapi>=0.100", "uvicorn>=0.22"],
        "msgpack": ["msgpack>=1.0"],
        "lz4": ["lz4>=4.0"],
        "dev": ["pytest>=7.0", "pytest-asyncio>=0.21", "ruff>=0.1", "mypy>=1.0"],
    },
    entry_points={
        "console_scripts": [
            "taskforge=cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Distributed Computing",
    ],
)