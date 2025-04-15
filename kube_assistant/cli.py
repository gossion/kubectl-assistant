#!/usr/bin/env python3
import argparse
import os
import sys
from rich.console import Console
from .agent import KubeAssistantAgent
from . import config

console = Console()


def config_command(args):
    """Handle configuration-related commands."""
    if args.view:
        # View current configuration
        config_str = config.view_config()
        console.print(f"Current Configuration:")
        console.print(config_str)
        return 0

    elif args.clear:
        # Clear all configuration
        config.clear_config()
        console.print("[green]Configuration cleared successfully[/green]")
        return 0

    elif args.set_provider:
        # Set provider
        provider = args.set_provider
        if provider not in ["openai", "azure"]:
            console.print("[red]Error:[/red] Provider must be 'openai' or 'azure'")
            return 1

        config.update_provider(provider)
        console.print(f"[green]Provider set to: {provider}[/green]")

    # Handle OpenAI settings
    if args.set_openai_key:
        config.update_openai_settings(api_key=args.set_openai_key)
        console.print("[green]OpenAI API key updated[/green]")

    if args.set_openai_model:
        config.update_openai_settings(model=args.set_openai_model)
        console.print(f"[green]OpenAI model set to: {args.set_openai_model}[/green]")

    # Handle Azure settings
    if args.set_azure_key:
        config.update_azure_settings(api_key=args.set_azure_key)
        console.print("[green]Azure OpenAI API key updated[/green]")

    if args.set_azure_endpoint:
        config.update_azure_settings(endpoint=args.set_azure_endpoint)
        console.print(f"[green]Azure endpoint updated[/green]")

    if args.set_azure_deployment:
        config.update_azure_settings(deployment=args.set_azure_deployment)
        console.print(
            f"[green]Azure deployment set to: {args.set_azure_deployment}[/green]"
        )

    if args.set_azure_version:
        config.update_azure_settings(api_version=args.set_azure_version)
        console.print(
            f"[green]Azure API version set to: {args.set_azure_version}[/green]"
        )

    return 0


def main():
    # When used as a kubectl plugin, the first argument will be the subcommand name
    # For 'kubectl assistant config', sys.argv[1] would be 'config'
    # For 'kubectl assistant query ...', sys.argv[1] would be 'query'
    # For 'kubectl assistant ...query...', we need to treat it as a direct query

    parser = argparse.ArgumentParser(
        description="A kubectl plugin for assisting with Kubernetes cluster management",
        prog="kubectl assistant",  # Set the program name to kubectl assistant
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Config command
    config_parser = subparsers.add_parser(
        "config", help="Configure kubectl assistant settings"
    )
    config_parser.add_argument(
        "--view", action="store_true", help="View current configuration"
    )
    config_parser.add_argument(
        "--clear", action="store_true", help="Clear all configuration"
    )

    # Provider settings
    config_parser.add_argument(
        "--set-provider", choices=["openai", "azure"], help="Set the default provider"
    )

    # OpenAI settings
    config_parser.add_argument("--set-openai-key", help="Set OpenAI API key")
    config_parser.add_argument("--set-openai-model", help="Set OpenAI model")

    # Azure settings
    config_parser.add_argument("--set-azure-key", help="Set Azure OpenAI API key")
    config_parser.add_argument(
        "--set-azure-endpoint", help="Set Azure OpenAI endpoint URL"
    )
    config_parser.add_argument(
        "--set-azure-deployment", help="Set Azure OpenAI deployment name"
    )
    config_parser.add_argument(
        "--set-azure-version", help="Set Azure OpenAI API version"
    )

    # Query command (no command explicitly specified becomes a query)
    query_parser = subparsers.add_parser("query", help="Run a query")
    query_parser.add_argument(
        "query",
        nargs="+",
        help="Natural language query describing the issue or request",
    )
    query_parser.add_argument(
        "--namespace",
        "-n",
        help="Default Kubernetes namespace to use (if not specified, will be determined by the AI)",
        default=None,
    )
    query_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    query_parser.add_argument(
        "--no-tool-display",
        action="store_true",
        help="Disable the rich display of tool calls and their results",
    )

    # Interactive mode command
    interactive_parser = subparsers.add_parser(
        "interactive", help="Start an interactive session"
    )
    interactive_parser.add_argument(
        "--namespace",
        "-n",
        help="Default Kubernetes namespace to use (if not specified, will be determined by the AI)",
        default=None,
    )
    interactive_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    interactive_parser.add_argument(
        "--no-tool-display",
        action="store_true",
        help="Disable the rich display of tool calls and their results",
    )

    # LLM provider configuration
    interactive_parser.add_argument(
        "--provider",
        choices=["openai", "azure"],
        help="LLM provider to use (overrides config file setting)",
    )

    # OpenAI specific options
    openai_group_interactive = interactive_parser.add_argument_group("OpenAI options")
    openai_group_interactive.add_argument(
        "--model",
        help="OpenAI model to use (overrides config file setting)",
    )
    openai_group_interactive.add_argument(
        "--openai-api-key",
        help="OpenAI API key (overrides config file setting)",
    )

    # Azure OpenAI specific options
    azure_group_interactive = interactive_parser.add_argument_group(
        "Azure OpenAI options"
    )
    azure_group_interactive.add_argument(
        "--azure-api-key",
        help="Azure OpenAI API key (overrides config file setting)",
    )
    azure_group_interactive.add_argument(
        "--azure-endpoint",
        help="Azure OpenAI endpoint URL (overrides config file setting)",
    )
    azure_group_interactive.add_argument(
        "--azure-deployment",
        help="Azure OpenAI deployment name (overrides config file setting)",
    )
    azure_group_interactive.add_argument(
        "--azure-api-version",
        help="Azure OpenAI API version (overrides config file setting)",
    )

    # LLM provider configuration
    query_parser.add_argument(
        "--provider",
        choices=["openai", "azure"],
        help="LLM provider to use (overrides config file setting)",
    )

    # OpenAI specific options
    openai_group = query_parser.add_argument_group("OpenAI options")
    openai_group.add_argument(
        "--model",
        help="OpenAI model to use (overrides config file setting)",
    )
    openai_group.add_argument(
        "--openai-api-key",
        help="OpenAI API key (overrides config file setting)",
    )

    # Azure OpenAI specific options
    azure_group = query_parser.add_argument_group("Azure OpenAI options")
    azure_group.add_argument(
        "--azure-api-key",
        help="Azure OpenAI API key (overrides config file setting)",
    )
    azure_group.add_argument(
        "--azure-endpoint",
        help="Azure OpenAI endpoint URL (overrides config file setting)",
    )
    azure_group.add_argument(
        "--azure-deployment",
        help="Azure OpenAI deployment name (overrides config file setting)",
    )
    azure_group.add_argument(
        "--azure-api-version",
        help="Azure OpenAI API version (overrides config file setting)",
    )

    # Check if we have any arguments
    if len(sys.argv) <= 1:
        parser.print_help()
        return 0

    # Check if the first argument is a recognized command
    known_commands = ["config", "query", "interactive", "-h", "--help"]

    # If the first argument isn't a recognized command, treat everything as a query
    if sys.argv[1] not in known_commands and not sys.argv[1].startswith("-"):
        # Insert 'query' at the beginning of the arguments
        sys.argv.insert(1, "query")

    args = parser.parse_args()

    # Handle config command
    if args.command == "config":
        return config_command(args)

    # Handle query command
    if args.command == "query":
        query = " ".join(args.query)

        # Load settings from config file
        config_provider = config.get_provider()
        openai_settings = config.get_openai_settings()
        azure_settings = config.get_azure_settings()

        # Initialize the agent with appropriate settings, prioritizing CLI arguments over config file
        provider = args.provider or config_provider

        agent_kwargs = {
            "namespace": args.namespace,
            "verbose": args.verbose,
            "show_tool_calls": not args.no_tool_display,
            "provider": provider,
        }

        # Add provider-specific settings
        if provider == "azure":
            # Get Azure settings, prioritizing CLI arguments
            azure_api_key = (
                args.azure_api_key
                or azure_settings.get("api_key")
                or os.environ.get("AZURE_OPENAI_API_KEY")
            )
            azure_endpoint = (
                args.azure_endpoint
                or azure_settings.get("endpoint")
                or os.environ.get("AZURE_OPENAI_ENDPOINT")
            )
            azure_deployment = (
                args.azure_deployment
                or azure_settings.get("deployment")
                or os.environ.get("AZURE_OPENAI_DEPLOYMENT")
            )
            azure_api_version = (
                args.azure_api_version
                or azure_settings.get("api_version")
                or os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
            )

            # Check required Azure settings
            if not azure_api_key:
                console.print(
                    "[red]Error:[/red] Azure OpenAI API key is required. Set with --azure-api-key, config command, or AZURE_OPENAI_API_KEY environment variable."
                )
                return 1

            if not azure_endpoint:
                console.print(
                    "[red]Error:[/red] Azure OpenAI endpoint is required. Set with --azure-endpoint, config command, or AZURE_OPENAI_ENDPOINT environment variable."
                )
                return 1

            if not azure_deployment:
                console.print(
                    "[red]Error:[/red] Azure OpenAI deployment name is required. Set with --azure-deployment, config command, or AZURE_OPENAI_DEPLOYMENT environment variable."
                )
                return 1

            agent_kwargs.update(
                {
                    "azure_api_key": azure_api_key,
                    "azure_endpoint": azure_endpoint,
                    "azure_deployment": azure_deployment,
                    "azure_api_version": azure_api_version,
                }
            )

            # Save new values to config if provided via CLI
            if args.azure_api_key:
                config.update_azure_settings(api_key=args.azure_api_key)
            if args.azure_endpoint:
                config.update_azure_settings(endpoint=args.azure_endpoint)
            if args.azure_deployment:
                config.update_azure_settings(deployment=args.azure_deployment)
            if args.azure_api_version:
                config.update_azure_settings(api_version=args.azure_api_version)

        else:  # OpenAI
            # Get OpenAI settings, prioritizing CLI arguments
            openai_api_key = (
                args.openai_api_key
                or openai_settings.get("api_key")
                or os.environ.get("OPENAI_API_KEY")
            )
            model = (
                args.model
                or openai_settings.get("model")
                or os.environ.get("OPENAI_MODEL", "gpt-4o")
            )

            # Check required OpenAI settings
            if not openai_api_key:
                console.print(
                    "[red]Error:[/red] OpenAI API key is required. Set with --openai-api-key, config command, or OPENAI_API_KEY environment variable."
                )
                return 1

            agent_kwargs.update(
                {
                    "model_name": model,
                    "openai_api_key": openai_api_key,
                }
            )

            # Save new values to config if provided via CLI
            if args.openai_api_key:
                config.update_openai_settings(api_key=args.openai_api_key)
            if args.model:
                config.update_openai_settings(model=args.model)

        # Save provider to config if provided via CLI
        if args.provider:
            config.update_provider(args.provider)

        try:
            agent = KubeAssistantAgent(**agent_kwargs)
            result = agent.run(query)

            # Only print the result directly if rich tool display is disabled
            if args.no_tool_display:
                print(result)

            return 0
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            return 1

    # Handle interactive mode command
    if args.command == "interactive":
        # Load settings from config file
        config_provider = config.get_provider()
        openai_settings = config.get_openai_settings()
        azure_settings = config.get_azure_settings()

        # Initialize the agent with appropriate settings
        provider = args.provider or config_provider

        agent_kwargs = {
            "namespace": args.namespace,
            "verbose": args.verbose,
            "show_tool_calls": not args.no_tool_display,
            "provider": provider,
        }

        # Add provider-specific settings
        if provider == "azure":
            # Get Azure settings, prioritizing CLI arguments
            azure_api_key = (
                args.azure_api_key
                or azure_settings.get("api_key")
                or os.environ.get("AZURE_OPENAI_API_KEY")
            )
            azure_endpoint = (
                args.azure_endpoint
                or azure_settings.get("endpoint")
                or os.environ.get("AZURE_OPENAI_ENDPOINT")
            )
            azure_deployment = (
                args.azure_deployment
                or azure_settings.get("deployment")
                or os.environ.get("AZURE_OPENAI_DEPLOYMENT")
            )
            azure_api_version = (
                args.azure_api_version
                or azure_settings.get("api_version")
                or os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
            )

            # Check required Azure settings
            if not azure_api_key:
                console.print(
                    "[red]Error:[/red] Azure OpenAI API key is required. Set with --azure-api-key, config command, or AZURE_OPENAI_API_KEY environment variable."
                )
                return 1

            if not azure_endpoint:
                console.print(
                    "[red]Error:[/red] Azure OpenAI endpoint is required. Set with --azure-endpoint, config command, or AZURE_OPENAI_ENDPOINT environment variable."
                )
                return 1

            if not azure_deployment:
                console.print(
                    "[red]Error:[/red] Azure OpenAI deployment name is required. Set with --azure-deployment, config command, or AZURE_OPENAI_DEPLOYMENT environment variable."
                )
                return 1

            agent_kwargs.update(
                {
                    "azure_api_key": azure_api_key,
                    "azure_endpoint": azure_endpoint,
                    "azure_deployment": azure_deployment,
                    "azure_api_version": azure_api_version,
                }
            )

        else:  # OpenAI
            # Get OpenAI settings, prioritizing CLI arguments
            openai_api_key = (
                args.openai_api_key
                or openai_settings.get("api_key")
                or os.environ.get("OPENAI_API_KEY")
            )
            model = (
                args.model
                or openai_settings.get("model")
                or os.environ.get("OPENAI_MODEL", "gpt-4o")
            )

            # Check required OpenAI settings
            if not openai_api_key:
                console.print(
                    "[red]Error:[/red] OpenAI API key is required. Set with --openai-api-key, config command, or OPENAI_API_KEY environment variable."
                )
                return 1

            agent_kwargs.update(
                {
                    "model_name": model,
                    "openai_api_key": openai_api_key,
                }
            )

        try:
            console.print(
                "[bold blue]Starting interactive session. Type 'exit' or 'quit' to end the session.[/bold blue]"
            )
            agent = KubeAssistantAgent(**agent_kwargs)
            agent.run_interactive()  # Changed from start_interactive_session() to run_interactive()
            return 0
        except Exception as e:
            # Use plain print instead of Rich console to avoid markup issues
            print(f"Error: {str(e)}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
