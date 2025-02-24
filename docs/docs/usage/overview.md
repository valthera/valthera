---
id: usage-overview
title: Usage Overview
slug: /usage
---

# Usage Overview

Valthera allows you to define and execute AI-driven workflows effortlessly. This section provides an overview of how to use Valthera to generate, execute, and manage AI workflows.

## How It Works

1. **Describe Your Workflow**  
   Simply provide a prompt in natural language describing what you want to achieve.

2. **Automatic Workflow Generation**  
   Valthera selects the best AI framework (LangGraph, CrewAI, AutoGen) and dynamically generates a structured workflow.

3. **Execute the Workflow**  
   The generated workflow runs immediately, providing structured results.

4. **Save and Reload**  
   You can save workflows for future executions and reload them as needed.

## Key Features

- **Intelligent Framework Selection**: Automatically picks the best AI framework based on your use case.
- **Dynamic Workflow Generation**: No manual setup—just describe your task, and Valthera builds the workflow.
- **Immediate Execution**: Workflows execute instantly with structured results.
- **Persistent Storage**: Save workflows to a file and reload them anytime.
- **Extensible & Modular**: Integrates with popular AI frameworks and supports custom AI agents.

## Example Usage

To run Valthera and describe your workflow:

```sh
python valthera.py
```

Then enter a prompt:

```plaintext
Retrieve news headlines from an API, summarize them, then validate the summary with a second agent.
```

Valthera will:

- Automatically select a framework (e.g., CrewAI)
- Generate the multi-step workflow
- Execute it immediately
- Return structured results
- Provide an option to save the workflow

## Saving and Loading Workflows

To save a workflow:

```sh
valthera save my_workflow.json
```

To load a previously saved workflow:

```sh
valthera load my_workflow.json
```

