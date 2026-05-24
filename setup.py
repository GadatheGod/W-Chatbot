from setuptools import setup, find_packages

setup(
    name="webaichat",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["*.html", "*.js", "*.yaml", "*.yaml.example", "*.css"],
    },
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn>=0.34.0",
        "pydantic>=2.10.0",
        "pydantic-settings>=2.7.0",
        "python-dotenv>=1.0.1",
        "bcrypt>=4.0.0",
        "aiohttp>=3.11.0",
        "ollama>=0.4.0",
        "chromadb>=0.5.20",
        "sentence-transformers>=3.3.0",
        "pdfplumber>=0.11.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.3.0",
        "PyYAML>=6.0.2",
        "sqlalchemy>=2.0.36",
        "aiosqlite>=0.20.0",
        "jinja2>=3.1.5",
        "python-multipart>=0.0.20",
        "tiktoken>=0.8.0",
        "litellm>=1.50.0",
    ],
    entry_points={
        "console_scripts": [
            "webaichat=webaichat.__main__:main_cli",
            "webaichat-wizard=wizard.__main__:main",
        ],
    },
    python_requires=">=3.10",
)
