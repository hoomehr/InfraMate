from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Core dependencies required for basic functionality
REQUIRED_DEPENDENCIES = [
    "requests>=2.31.0",
    "pathlib>=1.0.1",
    "boto3>=1.28.41",
    "pyyaml>=6.0.1",
    "python-dotenv>=1.0.0",
    "google-generativeai>=0.3.2",
    "gitpython>=3.1.37",
    "click>=8.1.7",
    "colorama>=0.4.6",
    "numpy>=1.24.0",
]

# Optional dependencies for enhanced features
OPTIONAL_DEPENDENCIES = {
    "rag": [
        "tiktoken>=0.5.2",
        "langchain>=0.1.0",
        "langchain-community>=0.0.16",
        "langchain-huggingface>=0.0.2",
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4",
        "huggingface_hub[hf_xet]>=0.20.3"
    ],
    "web": [
        "flask>=3.1.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "flake8>=6.0.0",
    ],
}

# All dependencies
ALL_DEPENDENCIES = REQUIRED_DEPENDENCIES + \
    OPTIONAL_DEPENDENCIES["rag"] + \
    OPTIONAL_DEPENDENCIES["web"]

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
    install_requires=REQUIRED_DEPENDENCIES,
    extras_require={
        "rag": OPTIONAL_DEPENDENCIES["rag"],
        "web": OPTIONAL_DEPENDENCIES["web"],
        "dev": OPTIONAL_DEPENDENCIES["dev"],
        "all": ALL_DEPENDENCIES,
    },
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