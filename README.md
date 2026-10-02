# SQL Agent

An **Agentic AI SQL Assistant** that converts natural-language questions into SQL queries, executes them against a PostgreSQL database, and returns the results in a human-readable format.

## Features

* Natural-language → SQL generation
* PostgreSQL database integration
* Automatic schema-aware SQL generation
* Query execution and result interpretation
* LLM-based reasoning and error handling
* Multi-model LLM selection based on query complexity
* Supports **Cloudflare GPT-OSS 120B**, **Groq GPT-OSS 120B**, and **Gemini 3.8 Flash**
* Environment-based API key and database configuration

## Architecture

```text
User Question
      ↓
Query / Complexity Analysis
      ↓
LLM Selection
      ↓
Schema Inspection
      ↓
SQL Generation
      ↓
PostgreSQL Execution
      ↓
Result Analysis
      ↓
Natural-Language Response
```

## Tech Stack

**Python · LangChain · LangGraph · PostgreSQL · Psycopg2 · Cloudflare Workers AI · Groq · Google Gemini · uv**

## Example

```text
User:
"Which 10 users have spent the most money?"

Agent:
→ Inspects database schema
→ Generates SQL
→ Executes query on PostgreSQL
→ Analyzes the result
→ Returns the top 10 users
```

## Configuration

Create a `.env` file containing your database credentials and LLM API keys:

```env
DATABASE=your_database
HOST=localhost
USER=postgres
PASSWORD=your_password
PORT=5432

CLOUDFLARE_API_TOKEN=your_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
GROQ_API_KEY=your_api_key
GEMINI_API_KEY=your_api_key
```

> Keep `.env` out of version control and never commit API keys or database credentials.
