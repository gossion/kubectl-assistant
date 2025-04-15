# Kube Assistant

A kubectl plugin that uses AI to assist users with Kubernetes cluster management and troubleshooting.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Commands](#basic-commands)
  - [Configuration](#configuration)
  - [Interactive Mode](#interactive-mode)
  - [Examples](#examples)
- [Advanced Topics](#advanced-topics)
  - [Namespace Inference](#namespace-inference)
  - [Configuration Priority](#configuration-priority)
  - [Using Azure OpenAI](#using-azure-openai)
  - [Environment Variables](#environment-variables)
- [Development](#development)
- [License](#license)

## Overview

Kube Assistant provides a natural language interface to interact with your Kubernetes cluster, helping you manage and troubleshoot your applications more efficiently. Simply ask questions in plain English, and the assistant will execute the appropriate kubectl commands for you.

## Features

- **Natural language interface** for interacting with your Kubernetes cluster
- **Multi-step reasoning** using LangChain's ReAct agent framework
- **Support for common kubectl operations** (get, describe, logs)
- **AI-powered namespace selection** based on your query context
- **Multiple AI providers** including OpenAI and Azure OpenAI
- **Rich console display** for tool calls and their results
- **Configuration management** to store API keys and preferences
- **Interactive mode** with conversation memory to maintain context

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/gossion/kube-assistant.git
   cd kube-assistant
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

3. Set up your API keys using the config command (recommended):
   
   For OpenAI:
   ```bash
   kubectl assistant config --set-provider openai --set-openai-key your_api_key --set-openai-model gpt-4o
   ```
   
   For Azure OpenAI:
   ```bash
   kubectl assistant config --set-provider azure --set-azure-key your_api_key \
     --set-azure-endpoint https://your-resource.openai.azure.com \
     --set-azure-deployment your_deployment_name
   ```

   Or using environment variables:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   # Or for Azure OpenAI
   export AZURE_OPENAI_API_KEY="your-azure-api-key"
   export AZURE_OPENAI_ENDPOINT="your-azure-endpoint"
   export AZURE_OPENAI_DEPLOYMENT="your-azure-deployment-name"
   ```

## Usage

### Basic Commands

The primary way to interact with Kube Assistant is through natural language queries:

```bash
kubectl assistant your question or request
```

Options:
```
-n, --namespace NAMESPACE      Kubernetes namespace to focus on 
                              (if not specified, will be inferred from your query)
-v, --verbose                  Enable verbose output
--no-tool-display              Disable the rich display of tool calls and their results
```

Provider options:
```
--provider {openai,azure}      LLM provider to use (overrides config setting)

# OpenAI options
--model MODEL                  OpenAI model to use (overrides config setting)
--openai-api-key KEY           OpenAI API key (overrides config setting)

# Azure OpenAI options
--azure-api-key KEY            Azure OpenAI API key (overrides config setting)
--azure-endpoint URL           Azure OpenAI endpoint URL (overrides config setting)
--azure-deployment NAME        Azure OpenAI deployment name (overrides config setting)
--azure-api-version VERSION    Azure OpenAI API version (overrides config setting)
```

### Configuration

The `config` command allows you to manage your settings:

```bash
kubectl assistant config [options]
```

Options:
```
--view                         View current configuration settings
--clear                        Clear all configuration settings

--set-provider {openai,azure}  Set the default provider

# OpenAI settings
--set-openai-key KEY           Set OpenAI API key
--set-openai-model MODEL       Set OpenAI model (default: gpt-4o)

# Azure OpenAI settings
--set-azure-key KEY            Set Azure OpenAI API key
--set-azure-endpoint URL       Set Azure OpenAI endpoint URL
--set-azure-deployment NAME    Set Azure OpenAI deployment name
--set-azure-version VERSION    Set Azure OpenAI API version
```

Examples:
```bash
# View current configuration
kubectl assistant config --view

# Set OpenAI as provider with API key
kubectl assistant config --set-provider openai --set-openai-key sk-xxxxxxxxxxxx

# Clear all configuration
kubectl assistant config --clear
```

### Interactive Mode

Interactive mode maintains conversation history between queries, allowing for more natural, multi-turn conversations with your Kubernetes cluster.

To start an interactive session:

```bash
kubectl assistant interactive
```

Features:
- **Conversation Memory**: The assistant remembers the context of your previous questions
- **Session Persistence**: Your conversation history is saved between sessions
- **Simple Navigation**: Type `exit` or `quit` to end the interactive session

Example session:
```
$ kubectl assistant interactive

[Kube Assistant]
Interactive mode started. Type 'exit' or 'quit' to end the session.

Query: show me pods in the default namespace

[Tool Call] kubectl_execute: kubectl get pods -n default
NAME                         READY   STATUS    RESTARTS   AGE
nginx-deployment-abc123      1/1     Running   0          2d
postgres-5b7f99b8c9-d8z9x    1/1     Running   0          6h

There are 2 pods running in the default namespace:
1. nginx-deployment-abc123 (Running)
2. postgres-5b7f99b8c9-d8z9x (Running)

Query: show me more details about the nginx pod
```

### Examples

```bash
# Set up your configuration once
kubectl assistant config --set-provider openai --set-openai-key your_api_key

# Get information about pods (namespace will be inferred)
kubectl assistant why are some of my pods pending?

# Inquire about a specific namespace without using -n flag
kubectl assistant what's happening in the kube-system namespace?

# Explicitly specify a namespace
kubectl assistant -n production check the status of my deployments
 
# Troubleshoot using Azure OpenAI (assuming Azure is configured)
kubectl assistant my deployment isn't starting, help me diagnose the issue

# Override your configured provider for a specific query
kubectl assistant --provider azure my deployment isn't starting

# Run without the rich console display
kubectl assistant --no-tool-display pods in my cluster keep crashing
```

## Advanced Topics

### Namespace Inference

The assistant can automatically determine which namespace to use based on your query:

- If you mention a namespace explicitly: "What's happening in the **monitoring** namespace?"
- If you use kubectl syntax: "Get pods **-n production**"
- If your query clearly relates to a specific namespace

When no namespace is detected, it defaults to "default". You can always override this by using the `-n` flag.

### Configuration Priority

Kube Assistant uses the following priority order when determining settings:

1. Command-line arguments (highest priority)
2. Configuration file (~/.kube-assistant/config.json)
3. Environment variables
4. Default values (lowest priority)

This means your saved settings will be used automatically, but you can override them with command-line arguments when needed.

### Using Azure OpenAI

To use Azure OpenAI with Kube Assistant:

1. Set up your Azure OpenAI service in the Azure portal
2. Create a deployment with an appropriate model (e.g., GPT-4)
3. Configure Kube Assistant:

   ```bash
   kubectl assistant config --set-provider azure \
     --set-azure-key your_azure_key \
     --set-azure-endpoint https://your-resource.openai.azure.com \
     --set-azure-deployment your_deployment_name
   ```

4. Run queries as normal:
   ```bash
   kubectl assistant what pods are running in my cluster?
   ```

To temporarily override settings:
```bash
kubectl assistant --azure-deployment your_other_deployment what pods are running?
```

### Environment Variables

You can use environment variables instead of command-line parameters:

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model to use | "gpt-4o" |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | - |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | - |
| `AZURE_OPENAI_DEPLOYMENT` | Azure OpenAI deployment name | - |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API version | "2023-05-15" |
| `KUBE_ASSISTANT_PROVIDER` | Default provider to use | "openai" |

## Development

### Setup development environment

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

## License

MIT