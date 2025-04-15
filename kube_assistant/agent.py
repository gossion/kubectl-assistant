"""
Kubernetes assistant agent using LangChain ReAct framework.
"""

import json
import os
import subprocess
import shlex
import functools
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Literal, ClassVar, Callable

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
from rich.box import ROUNDED

# Initialize Rich console
console = Console()

# Global flag for tool call display
SHOW_TOOL_CALLS = True

# Default memory storage location
DEFAULT_MEMORY_PATH = os.path.expanduser("~/.kube_assistant/memory.pkl")


def display_kubectl(tool_name: str = None):
    """
    Decorator for kubectl functions to display execution details.

    Args:
        tool_name: The name of the kubectl tool being executed
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Skip display if global flag is off
            if not SHOW_TOOL_CALLS:
                return func(*args, **kwargs)

            # Extract function name and parameters
            func_name = tool_name or func.__name__
            display_name = func_name.upper()

            # Display the command being executed
            console.print()
            console.rule(f"[bold blue]EXECUTING: {func_name}")

            # Create a table for parameters
            table = Table(
                title="Parameters",
                box=ROUNDED,
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Parameter", style="cyan")
            table.add_column("Value", style="yellow")

            # Add positional args to table
            for i, arg in enumerate(args):
                table.add_row(f"arg{i}", str(arg))

            # Add keyword args to table
            for key, value in kwargs.items():
                table.add_row(key, str(value))

            console.print(table)

            # Try to construct and display the kubectl command if possible
            if func_name == "kubectl_exec" and args:
                cmd_str = args[0]
                console.print("[bold cyan]Command:")
                console.print(Syntax(cmd_str, "bash", theme="monokai"))

            # Execute the function
            try:
                output = func(*args, **kwargs)

                # Display the output with appropriate formatting
                if output.startswith("{") and output.endswith("}"):
                    try:
                        # Format as JSON
                        parsed_output = json.loads(output)
                        output_str = json.dumps(parsed_output, indent=2)
                        syntax = Syntax(
                            output_str, "json", theme="monokai", line_numbers=True
                        )
                        console.print("[bold green]Output:")
                        console.print(syntax)
                    except json.JSONDecodeError:
                        _print_regular_output(output)
                else:
                    _print_regular_output(output)

                console.rule()
                return output
            except Exception as e:
                error_msg = str(e)
                console.print("[bold red]Error:")
                console.print(error_msg)
                console.rule()
                return f"Error: {error_msg}"

        return wrapper

    return decorator


def _print_regular_output(output: str) -> None:
    """Print regular (non-JSON) output with truncation for long outputs."""
    output_lines = output.split("\n")
    if len(output_lines) > 20:
        # Truncate for display
        preview = "\n".join(output_lines[:20])
        console.print("[bold green]Output (truncated):")
        console.print(preview)
        console.print(f"[italic]...and {len(output_lines) - 20} more lines")
    else:
        console.print("[bold green]Output:")
        console.print(output)


@display_kubectl(tool_name="kubectl_exec")
def kubectl_exec(command: str) -> str:
    """
    Execute a kubectl command.

    Args:
        command: The kubectl command to execute (without the 'kubectl' prefix)

    Returns:
        Output of the kubectl command
    """
    # Ensure we have a safe command to execute
    command = command.strip()

    # Add kubectl prefix if not already present
    if not command.startswith("kubectl "):
        command = f"kubectl {command}"

    # Convert to list for subprocess
    cmd_args = shlex.split(command)

    try:
        result = subprocess.run(cmd_args, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


class KubeAssistantAgent:
    """
    Kubernetes assistant agent using LangChain ReAct agent.
    """

    def __init__(
        self,
        namespace: Optional[str] = None,
        verbose: bool = False,
        show_tool_calls: bool = True,
        provider: Literal["openai", "azure"] = "openai",
        model_name: str = "gpt-4o",
        # OpenAI specific params
        openai_api_key: Optional[str] = None,
        # Azure OpenAI specific params
        azure_api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        azure_api_version: str = "2023-05-15",
        # Memory
        memory: Optional[ConversationBufferMemory] = None,
        memory_path: str = DEFAULT_MEMORY_PATH,
    ):
        """
        Initialize the Kubernetes assistant agent.

        Args:
            namespace: Kubernetes namespace to focus on (if None, will be determined by the AI)
            verbose: Enable verbose output from LangChain
            show_tool_calls: Enable enhanced tool call display using Rich
            provider: The LLM provider to use ("openai" or "azure")
            model_name: LLM model to use for the agent (for OpenAI provider)
            openai_api_key: OpenAI API key (will use OPENAI_API_KEY env var if not provided)
            azure_api_key: Azure OpenAI API key (will use AZURE_OPENAI_API_KEY env var if not provided)
            azure_endpoint: Azure OpenAI endpoint URL (will use AZURE_OPENAI_ENDPOINT env var if not provided)
            azure_deployment: Azure OpenAI deployment name (will use AZURE_OPENAI_DEPLOYMENT env var if not provided)
            azure_api_version: Azure OpenAI API version
            memory: Optional memory object to maintain conversation history
            memory_path: Path to persistent memory storage
        """
        self.verbose = verbose
        self.show_tool_calls = show_tool_calls
        self.provider = provider
        self.default_namespace = namespace
        self.memory_path = memory_path
        # Initialize memory attribute explicitly
        self.memory = memory

        # Set the global display flag
        global SHOW_TOOL_CALLS
        SHOW_TOOL_CALLS = show_tool_calls

        # Setup callbacks
        self.callbacks = []

        # Initialize tools
        self._initialize_tools()

        # Initialize LLM based on provider
        if provider == "azure":
            self.llm = AzureChatOpenAI(
                api_key=azure_api_key or os.environ.get("AZURE_OPENAI_API_KEY"),
                azure_endpoint=azure_endpoint
                or os.environ.get("AZURE_OPENAI_ENDPOINT"),
                azure_deployment=azure_deployment
                or os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
                api_version=azure_api_version,
                temperature=0,
            )
        else:  # default to OpenAI
            self.llm = ChatOpenAI(
                api_key=openai_api_key or os.environ.get("OPENAI_API_KEY"),
                model_name=model_name,
                temperature=0,
            )

        # Create the ReAct agent prompt template
        memory_context = "Chat History:\n{chat_history}\n" if self.memory else ""
        agent_prompt = PromptTemplate.from_template(
            f"""You are a Kubernetes troubleshooting assistant.
            You help users diagnose and fix issues with their Kubernetes clusters.
            
            {memory_context}{{tools}}
            
            When using kubectl commands, always consider the appropriate namespace. If a namespace is specified in the user's query, use that namespace.
            If no namespace is specified and you need to target a specific namespace, use the correct namespace based on the context of the query.
            
            Use the following format:
            
            Question: the user's question
            Thought: consider what to do
            Action: the action to take, should be one of [{{tool_names}}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original user question
            
            Begin!
            
            Question: {{input}}
            {{agent_scratchpad}}"""
        )

        self.agent = create_react_agent(
            llm=self.llm, tools=self.tools, prompt=agent_prompt
        )

        # Configure the agent executor with memory if provided
        executor_kwargs = {
            "agent": self.agent,
            "tools": self.tools,
            "verbose": verbose,
            "callbacks": self.callbacks,
            "handle_parsing_errors": True,
        }

        if self.memory:
            executor_kwargs["memory"] = self.memory

        self.agent_executor = AgentExecutor(**executor_kwargs)

    def _initialize_tools(self):
        """Initialize the kubectl tools."""
        self.tools = [
            Tool(
                name="kubectl_exec",
                func=kubectl_exec,
                description="Execute a kubectl command. Provide the full command without the 'kubectl' prefix. Include namespace with -n or --namespace if needed.",
            ),
        ]

    def run(self, query: str) -> str:
        """
        Run the Kubernetes assistant agent with the given query.

        Args:
            query: Natural language query describing the issue or request

        Returns:
            Agent's response to the query
        """
        # if self.show_tool_calls:
        #     # Display default namespace info if provided
        #     namespace_info = ""
        #     if self.default_namespace:
        #         namespace_info = f"\nDefault Namespace: {self.default_namespace}"

        #     console.print(
        #         Panel(
        #             f"Query: {query}{namespace_info}",
        #             title="Kube Assistant",
        #             border_style="blue",
        #         )
        #     )

        # Modify the query to include namespace info if default was provided
        modified_query = query
        if self.default_namespace:
            modified_query = f"{query} (Use namespace: {self.default_namespace})"

        result = self.agent_executor.invoke({"input": modified_query})["output"]

        if self.show_tool_calls:
            console.print()
            console.print(Panel(result, title="Final Answer", border_style="green"))

        return result

    def create_memory(self) -> ConversationBufferMemory:
        """
        Create a new conversation memory for interactive mode.

        Returns:
            ConversationBufferMemory: A new conversation memory instance
        """
        # Create memory with the required input_key parameter to prevent the
        # "One input key expected got []" error
        return ConversationBufferMemory(
            memory_key="chat_history", input_key="input", return_messages=True
        )

    def save_memory(self) -> None:
        """
        Save the current memory to persistent storage.
        """
        if hasattr(self, "memory") and self.memory:
            try:
                # Get the chat history messages
                chat_messages = self.memory.chat_memory.messages

                # Create directory if it doesn't exist
                Path(self.memory_path).parent.mkdir(parents=True, exist_ok=True)

                # Save the messages directly
                with open(self.memory_path, "wb") as f:
                    pickle.dump(chat_messages, f)

                console.print("[dim]Memory saved successfully[/dim]")
            except Exception as e:
                console.print(f"[bold red]Error saving memory: {str(e)}")

    def load_memory(self) -> None:
        """
        Load memory from persistent storage.
        """
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, "rb") as f:
                    chat_messages = pickle.load(f)

                    # Create memory if it doesn't exist yet
                    if not hasattr(self, "memory") or self.memory is None:
                        self.memory = self.create_memory()

                    # Check if chat_messages is a list of BaseMessage objects
                    if isinstance(chat_messages, list) and all(
                        isinstance(msg, BaseMessage) for msg in chat_messages
                    ):
                        # Clear existing messages to avoid duplicates
                        self.memory.chat_memory.messages.clear()
                        # Load the messages directly
                        self.memory.chat_memory.messages.extend(chat_messages)
                        console.print("[dim]Memory loaded successfully[/dim]")
                    else:
                        console.print(
                            "[bold yellow]Warning: Invalid memory format. Creating new memory.[/bold yellow]"
                        )
                        self.memory = self.create_memory()
            except Exception as e:
                console.print(f"[bold red]Error loading memory: {str(e)}")
                # Create a new memory if loading fails
                self.memory = self.create_memory()
        else:
            # Create new memory if no existing memory file
            self.memory = self.create_memory()
            console.print(
                "[dim]No previous memory found. Starting new conversation.[/dim]"
            )

    def start_interactive_session(self) -> None:
        """
        Start an interactive session with the agent.
        This method creates a new memory object if none exists or loads from persistent storage.
        """
        # Always try to load memory first
        self.load_memory()

        # Always recreate the agent executor with memory to ensure it's using the current memory
        memory_context = "Chat History:\n{chat_history}\n"
        agent_prompt = PromptTemplate.from_template(
            f"""You are a Kubernetes troubleshooting assistant.
            You help users diagnose and fix issues with their Kubernetes clusters.
            
            {memory_context}{{tools}}
            
            When using kubectl commands, always consider the appropriate namespace. If a namespace is specified in the user's query, use that namespace.
            If no namespace is specified and you need to target a specific namespace, use the correct namespace based on the context of the query.
            
            Use the following format:
            
            Question: the user's question
            Thought: consider what to do
            Action: the action to take, should be one of [{{tool_names}}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original user question
            
            Begin!
            
            Question: {{input}}
            {{agent_scratchpad}}"""
        )

        # Recreate the agent with the updated prompt
        self.agent = create_react_agent(
            llm=self.llm, tools=self.tools, prompt=agent_prompt
        )

        # Recreate agent executor with memory
        executor_kwargs = {
            "agent": self.agent,
            "tools": self.tools,
            "verbose": self.verbose,
            "callbacks": self.callbacks,
            "handle_parsing_errors": True,
            "memory": self.memory,
        }

        self.agent_executor = AgentExecutor(**executor_kwargs)

        console.print(
            Panel(
                "Interactive mode started. Type 'exit' or 'quit' to end the session.",
                title="Kube Assistant",
                border_style="blue",
            )
        )

    def run_interactive(self) -> None:
        """
        Run the agent in interactive mode, maintaining conversation history.
        """
        self.start_interactive_session()

        try:
            while True:
                try:
                    # Get user input without Rich markup
                    query = input("Query: ")  # Regular input without Rich markup

                    # Check for exit command
                    if query.lower() in ("exit", "quit"):
                        self.save_memory()
                        console.print(
                            Panel(
                                "Interactive session ended.",
                                title="Kube Assistant",
                                border_style="blue",
                            )
                        )
                        break

                    # Handle "continue" command or similar for resuming iteration
                    if query.lower() in (
                        "continue",
                        "continue to iterate",
                        "continue to iterate?",
                    ):
                        console.print(
                            "[dim]Continuing with the previous context...[/dim]"
                        )
                        # No action needed - we'll just continue the loop with the loaded memory
                        continue

                    # Run the query and display the result
                    self.run(query)

                    # Save memory after each interaction to ensure nothing is lost
                    self.save_memory()

                except KeyboardInterrupt:
                    self.save_memory()
                    console.print("\nInteractive session ended.")
                    break
                except Exception as e:
                    # Use plain print instead of rich console to avoid markup issues
                    print(f"Error: {str(e)}")
        finally:
            # Make sure memory is saved even if there's an unexpected error
            self.save_memory()
