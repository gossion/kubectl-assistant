from setuptools import setup, find_packages

setup(
    name="kube-assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langchain-openai>=0.0.2",
        "openai>=1.0.0",
        "rich>=13.4.0",
    ],
    entry_points={
        "console_scripts": [
            "kubectl-assistant=kube_assistant.cli:main",
        ],
    },
    author="Guoxun Wei",
    author_email="guwe@microsoft.com",
    description="A kubectl plugin to assist with Kubernetes cluster management",
    keywords="kubernetes, kubectl, plugin, assistant, llm, ai",
    python_requires=">=3.8",
)
