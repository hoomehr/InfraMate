from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="inframate",
    version="0.1.0",
    author="",
    author_email="",
    description="AI-powered infrastructure deployment assistant for AWS and more",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/inframate",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "pathlib>=1.0.1",
        "boto3>=1.28.41",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "google-generativeai>=0.3.2",
        "gitpython>=3.1.37",
        "click>=8.1.7",
        "tiktoken>=0.5.2",
        "flask>=3.1.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.16",
        "langchain-huggingface>=0.0.2",
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4",
        "colorama>=0.4.6"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "inframate=inframate.cli:main",
        ],
    },
) 