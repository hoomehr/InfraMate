from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

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
        "google-generativeai>=0.3.2"
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