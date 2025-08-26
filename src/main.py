"""
Main entry point for the Pokedex Agent.
"""

import asyncio
import typer
from typing import Optional
import logging
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import sys

from llm_agent import LLMAgent
from report_printer import ReportPrinter
from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

app = typer.Typer()
console = Console()


def check_api_key():
    """Check if OpenAI API key is configured."""
    if not settings.openai_api_key:
        console.print("[red]❌ Error: OpenAI API key not found![/red]")
        console.print("\n[yellow]Please set your OpenAI API key:[/yellow]")
        sys.exit(1)


@app.command()
def research(
    query: str = typer.Argument(..., help="Your Pokemon research question"),
):
    """Conduct deep research on a Pokemon query."""
    check_api_key()

    console.print(
        Panel.fit(
            "[bold blue]🔍 Deep Research Pokedex Agent[/bold blue]\n"
            "🔬Conducting deep research for Pokemon questions...",
            border_style="blue",
        )
    )

    asyncio.run(_conduct_research(query))


@app.command()
def interactive():
    """Start interactive mode for multiple queries."""
    check_api_key()

    console.print(
        Panel.fit(
            "[bold green]🎮 Interactive Pokedex Mode[/bold green]\n"
            "Ask multiple questions and explore Pokemon data!",
            border_style="green",
        )
    )

    while True:
        try:
            query = Prompt.ask(
                "\n[bold cyan]What would you like to know about Pokemon?[/bold cyan]"
            )

            if query.lower() in ["quit", "exit", "q"]:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if query.strip():
                console.print(f"\n[bold]🔬Researching:[/bold] {query}")
                asyncio.run(_conduct_research(query))

        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def demo():
    """Run demo queries to showcase the agent's capabilities."""
    check_api_key()

    demo_queries = [
        "What is an easy Pokemon to train that is strong in Pokemon Crystal?",
        "I want to find a unique but non-legendary Pokemon that lives by the sea in Saphire.",
        "Build a team of all bug type Pokemon in Pokemon Ruby.",
        "Recommend a cool team in Pokemon Red that isn't standard",        
    ]

    console.print(
        Panel.fit(
            "[bold magenta]🎯 Pokedex Agent Demo[/bold magenta]\n"
            "Running through example queries to showcase capabilities...",
            border_style="magenta",
        )
    )

    for i, query in enumerate(demo_queries, 1):
        console.print(f"\n[bold]Demo {i}/4:[/bold] {query}")
        console.print("-" * 60)

        try:
            asyncio.run(_conduct_research(query))
        except Exception as e:
            console.print(f"[red]Error in demo {i}: {e}[/red]")

        if i < len(demo_queries):
            console.print("\n[dim]Press Enter to continue to next demo...[/dim]")
            input()


async def _conduct_research(query: str):
    """Conduct research and display results."""
    reportPrinter = ReportPrinter()

    try:
        # Initialise agent
        agent = LLMAgent()

        # Display progress
        reportPrinter.display_progress("Initialising research agent...")
        
        # Conduct research
        reportPrinter.display_progress(
            "Conducting research..."
        )

        report = await agent.run(query)

        # Display results
        reportPrinter.display_research_report(report)

    except Exception as e:
        logger.error(f"Error during research: {e}")
        reportPrinter.display_error(f"Research failed: {e}")


@app.callback()
def main():
    """
    🎮 Pokedex Research Agent

    A sophisticated agent that conducts deep research for Pokemon questions.
    Uses multiple data sources including PokeAPI and web research to provide
    comprehensive, well-sourced answers.
    """
    pass


if __name__ == "__main__":
    app()
