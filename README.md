# Resume Editor with Claude & Overleaf

An AI-powered app that helps you edit your Overleaf resume using Claude. Simply give natural language instructions like "tailor my resume for a software engineer position at Google" and Claude will intelligently edit your resume.

## Features

- 🤖 Natural language editing using Claude AI
- 📝 Direct integration with Overleaf projects
- 🎯 Tailors resumes for specific job positions
- 💾 Automatic backup before edits
- 🔄 Interactive editing sessions

## Prerequisites

- Python 3.9+
- An Overleaf account with a resume project
- Anthropic API key (for Claude)
- Browser with Overleaf session (Chrome or Firefox)

## Installation

1. Clone or navigate to this directory:
```bash
cd resume-editor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Anthropic API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Configuration

Edit `config.yaml` to specify your Overleaf project:

```yaml
overleaf:
  project_name: "My Resume"  # Name of your Overleaf project
  resume_file: "resume.tex"  # Path to your resume file in the project

claude:
  model: "claude-sonnet-4-5-20250929"
  max_tokens: 4096
```

## Usage

### Interactive Mode

Start an interactive editing session:

```bash
python resume_editor.py
```

Then enter commands like:
- "Tailor my resume for a senior software engineer position at Google"
- "Add more emphasis on my Python skills"
- "Make the description of my first job more concise"
- "Highlight my leadership experience"

### Single Command Mode

Make a one-time edit:

```bash
python resume_editor.py --instruction "Tailor this resume for a data science position"
```

### List Projects

See all your Overleaf projects:

```bash
python resume_editor.py --list-projects
```

## How It Works

1. **Connects to Overleaf**: Uses your browser session to authenticate with Overleaf
2. **Reads Resume**: Downloads your current resume LaTeX file
3. **AI Processing**: Sends the resume to Claude with your instructions
4. **Smart Editing**: Claude intelligently edits the LaTeX while preserving formatting
5. **Updates Overleaf**: Uploads the edited resume back to your project

## Safety Features

- Creates automatic backups before any edits
- Shows a diff of changes before applying
- Requires confirmation for destructive operations
- Validates LaTeX syntax before uploading

## Troubleshooting

### Authentication Issues

If you get authentication errors:
1. Make sure you're logged into Overleaf in Chrome or Firefox
2. Try closing and reopening your browser
3. Clear browser cookies and log in again

### Project Not Found

If the app can't find your project:
1. Run with `--list-projects` to see all available projects
2. Check that the `project_name` in `config.yaml` matches exactly

## License

MIT License
