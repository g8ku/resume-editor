#!/usr/bin/env python3
"""
Resume Editor with Claude & Overleaf
Intelligently edit your Overleaf resume using Claude AI
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
import pyoverleaf
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax

console = Console()


class ResumeEditor:
    """Main application class for editing resumes with Claude and Overleaf"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the resume editor with configuration"""
        self.config = self._load_config(config_path)
        self.api = None
        self.project_io = None
        self.anthropic_client = None
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            console.print(f"[red]Error: Configuration file '{config_path}' not found[/red]")
            console.print("Please create a config.yaml file. See README.md for instructions.")
            sys.exit(1)
    
    def connect(self):
        """Connect to Overleaf and Claude APIs"""
        console.print("[cyan]Connecting to Overleaf...[/cyan]")
        
        # Initialize Overleaf API
        self.api = pyoverleaf.Api()
        host = self.config['overleaf'].get('host')
        if host:
            self.api.host = host
        
        try:
            # Authenticate using browser cookies
            self.api.login_from_browser()
            console.print("[green]✓ Connected to Overleaf[/green]")
        except Exception as e:
            console.print(f"[red]Failed to authenticate with Overleaf: {e}[/red]")
            console.print("Make sure you're logged into Overleaf in Chrome or Firefox.")
            sys.exit(1)
        
        # Initialize Claude API
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
            console.print("Set it with: export ANTHROPIC_API_KEY='your-api-key'")
            sys.exit(1)
        
        self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        console.print("[green]✓ Connected to Claude API[/green]")
    
    def list_projects(self):
        """List all available Overleaf projects"""
        console.print("\n[cyan]Available Overleaf Projects:[/cyan]\n")
        try:
            projects = self.api.get_projects()
            for i, project in enumerate(projects, 1):
                console.print(f"{i}. {project.name} (ID: {project.id})")
        except Exception as e:
            console.print(f"[red]Error listing projects: {e}[/red]")
            sys.exit(1)
    
    def find_project(self, project_name: str):
        """Find a project by name"""
        projects = self.api.get_projects()
        for project in projects:
            if project.name == project_name:
                return project
        return None
    
    def setup_project(self):
        """Setup connection to the specified project"""
        project_name = self.config['overleaf']['project_name']
        console.print(f"\n[cyan]Looking for project: {project_name}[/cyan]")
        
        project = self.find_project(project_name)
        if not project:
            console.print(f"[red]Project '{project_name}' not found[/red]")
            console.print("\nRun with --list-projects to see all available projects.")
            sys.exit(1)
        
        console.print(f"[green]✓ Found project: {project.name}[/green]")
        self.project_io = pyoverleaf.ProjectIO(self.api, project.id)
    
    def read_resume(self) -> str:
        """Read the resume file from Overleaf"""
        resume_path = self.config['overleaf']['resume_file']
        console.print(f"[cyan]Reading {resume_path}...[/cyan]")
        
        try:
            with self.project_io.open(resume_path, 'r') as f:
                content = f.read()
            console.print(f"[green]✓ Read {len(content)} characters[/green]")
            return content
        except Exception as e:
            console.print(f"[red]Error reading resume: {e}[/red]")
            sys.exit(1)
    
    def write_resume(self, content: str):
        """Write the edited resume back to Overleaf"""
        resume_path = self.config['overleaf']['resume_file']
        console.print(f"[cyan]Uploading to {resume_path}...[/cyan]")
        
        try:
            with self.project_io.open(resume_path, 'w') as f:
                f.write(content)
            console.print("[green]✓ Resume updated successfully[/green]")
        except Exception as e:
            console.print(f"[red]Error writing resume: {e}[/red]")
            sys.exit(1)
    
    def create_backup(self, content: str):
        """Create a local backup of the resume"""
        if not self.config['editor']['create_backup']:
            return
        
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"resume_{timestamp}.tex"
        
        with open(backup_path, 'w') as f:
            f.write(content)
        
        console.print(f"[dim]Backup saved to {backup_path}[/dim]")
    
    def edit_with_claude(self, resume_content: str, instruction: str) -> str:
        """Use Claude to edit the resume based on instructions"""
        console.print("\n[cyan]Sending to Claude for editing...[/cyan]")
        
        system_prompt = """You are an expert resume editor and career advisor. Your task is to edit LaTeX resume files according to user instructions.

IMPORTANT RULES:
1. Preserve all LaTeX formatting, commands, and structure
2. Only modify the content as requested by the user
3. Do not add comments or explanations in the LaTeX
4. Return ONLY the complete edited LaTeX document
5. Maintain consistent formatting and style
6. Ensure all LaTeX syntax remains valid

When tailoring for a position:
- Emphasize relevant skills and experience
- Use industry-specific keywords
- Adjust descriptions to match job requirements
- Keep formatting professional and consistent"""

        user_prompt = f"""Here is a resume in LaTeX format:

{resume_content}

Please edit this resume according to the following instruction:
{instruction}

Return the complete edited resume in LaTeX format, with no additional commentary."""

        try:
            response = self.anthropic_client.messages.create(
                model=self.config['claude']['model'],
                max_tokens=self.config['claude']['max_tokens'],
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            edited_content = response.content[0].text
            console.print("[green]✓ Claude finished editing[/green]")
            return edited_content
            
        except Exception as e:
            console.print(f"[red]Error calling Claude API: {e}[/red]")
            sys.exit(1)
    
    def show_diff(self, original: str, edited: str):
        """Display a visual diff of changes"""
        if not self.config['editor']['show_diff']:
            return
        
        # Simple diff display - show the edited version
        console.print("\n[cyan]═══ Edited Resume ═══[/cyan]")
        syntax = Syntax(edited, "latex", theme="monokai", line_numbers=True)
        console.print(syntax)
        console.print("[cyan]═══════════════════[/cyan]\n")
    
    def apply_edit(self, instruction: str):
        """Apply an edit instruction to the resume"""
        # Read current resume
        original_content = self.read_resume()
        
        # Create backup
        self.create_backup(original_content)
        
        # Edit with Claude
        edited_content = self.edit_with_claude(original_content, instruction)
        
        # Show diff
        self.show_diff(original_content, edited_content)
        
        # Confirm before uploading
        if self.config['editor']['require_confirmation']:
            if not Confirm.ask("\n[yellow]Apply these changes to Overleaf?[/yellow]"):
                console.print("[dim]Edit cancelled[/dim]")
                return False
        
        # Upload to Overleaf
        self.write_resume(edited_content)
        return True
    
    def interactive_mode(self):
        """Run in interactive mode with multiple edits"""
        console.print(Panel.fit(
            "[bold cyan]Resume Editor - Interactive Mode[/bold cyan]\n"
            "Enter editing instructions, or 'quit' to exit",
            border_style="cyan"
        ))
        
        while True:
            instruction = Prompt.ask("\n[cyan]What would you like to do?[/cyan]")
            
            if instruction.lower() in ['quit', 'exit', 'q']:
                console.print("[green]Goodbye![/green]")
                break
            
            if not instruction.strip():
                continue
            
            self.apply_edit(instruction)
            console.print("\n[green]✓ Edit complete![/green]")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Edit your Overleaf resume using Claude AI"
    )
    parser.add_argument(
        "--list-projects",
        action="store_true",
        help="List all available Overleaf projects"
    )
    parser.add_argument(
        "--instruction",
        "-i",
        type=str,
        help="Single editing instruction (non-interactive mode)"
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Print banner
    console.print("\n[bold cyan]Resume Editor with Claude & Overleaf[/bold cyan]\n")
    
    # Initialize editor
    editor = ResumeEditor(config_path=args.config)
    editor.connect()
    
    # List projects mode
    if args.list_projects:
        editor.list_projects()
        return
    
    # Setup project
    editor.setup_project()
    
    # Single instruction mode
    if args.instruction:
        editor.apply_edit(args.instruction)
        console.print("\n[green]✓ Done![/green]")
    else:
        # Interactive mode
        editor.interactive_mode()


if __name__ == "__main__":
    main()
