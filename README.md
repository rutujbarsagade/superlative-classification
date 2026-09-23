# ResearchMind — Multi-Agent Research System

ResearchMind is a Python research pipeline that combines four LangChain components to search the web, read a relevant page, draft a structured report, and critically review the result. It includes both a Streamlit interface and a command-line entry point.

## Pipeline

1. **Search Agent** uses Tavily to gather recent sources.
2. **Reader Agent** safely scrapes public HTML or plain-text pages.
3. **Writer Chain** synthesizes the findings into a structured report.
4. **Critic Chain** scores the report and identifies improvements.

## Quick start

Python 3.12 is recommended.

```bash
git clone https://github.com/rutujbarsagade/Multi-agent-research-system.git
cd Multi-agent-research-system
python -m venv .venv
```

Activate the environment, then install the dependencies:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create your local environment file:

```bash
# macOS/Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Set these values in `.env`:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

Run the web application:

```bash
streamlit run app.py
```

Run the terminal pipeline:

```bash
python pipeline.py
```

The OpenAI and Tavily keys entered in the Streamlit sidebar are scoped to that browser session. For shared deployments, use server-side secrets instead.

## Tests

```bash
python -m unittest discover -s tests -v
python -m pip check
```

## Security design

- `.env`, virtual environments, credentials, logs, databases, and generated Python files are excluded by `.gitignore`.
- `.env.example` contains placeholders only. Never commit a real API key.
- API keys entered in the UI remain session-scoped instead of being written to the process-wide environment.
- URL scraping rejects credentials, non-HTTP schemes, non-standard ports, private/reserved addresses, unsafe redirects, unsupported content types, and oversized responses.
- Untrusted search and web content is treated as data rather than instructions.
- Untrusted raw output is HTML-escaped before rendering.
- CI runs tests, Gitleaks scans repository history, CodeQL analyzes Python code, and Dependabot monitors dependencies and Actions.

If a credential is ever exposed, revoke it first. Removing it from the latest commit is not enough because Git history and forks can retain it.

## Deployment safety

This project does not include authentication, authorization, or rate limiting. Before exposing an instance publicly, add authentication, request limits, API-key budgets, and appropriate operational logging at the gateway or hosting layer. Use restricted provider keys with spending limits.

Do not report vulnerabilities in a public issue. See [SECURITY.md](SECURITY.md) for the private reporting policy.
