# YNAB API Docs

YNAB REST API docs are at ./docs/ynab-api-1.yaml


# System Changes / Agent Permissions

IMPORTANT: the files you edit should only be in this local repo, NEVER anywhere else on the system.
I will use pyinfra or scripts to apply changes to the system.

You, the agent, should NEVER run commands on the system that would make permanent changes.  We
ALWAYS put our action plan into code or IAC before applying to the system.

You are ONLY ALLOWED to run READ-ONLY cli commands.

If you are ever confused about what you have permission to do, stop and ask.


# UV + mise for dependencies

This repo uses uv for managing Python and Python dependencies.

It uses mise for other dev dependencies and for discoverability and execution of cli tasks.

My command examples will always be from running in a shell that has mise active.  If your shells do
not have mise active, you will to use `mise exec ...` in this repos base directory to get the same
results.


# Specs & Execution Plans

The agent will usually be given a file in the ./specs folder for each project it is asked to work
on.  This will be referenced by me, the user and operator, to communicate with the agent.

You should keep it updated as we progress so it serves as a record of our findings, decisions, and
actions taken.

You will be given the command "read spec" and will find the spec file in your context.
When that happens, you should:

- Read the spec file
- Respond to the user with "Spec file {name of spec file} found."
- Add any questions you have to the spec file.  Don't force questions, if there aren't any, skip
  this step.  If you've added questions, prompt the user to answer them.
- If no questions or when the questions are answered, ask the user for permission to execute working
  on the spec.

## Markdown Formatting

- Limit your line width to 100 chars


## Creating/Running Tests

Don't create or run tests unless you've been asked to.  They may not be reliable in this project.


## Test Execution

- Run tests normally by default.
- Do not disable Python bytecode writing or pytest cache creation unless there is a specific
  troubleshooting need or the user asks for it.


## Legacy vs Current

This project is in transition from a legacy API implementation to a current one.  The current files
are `libs/api.py` and `libs/api_schema.py`.  The legacy api is in `ynabapi.py`.

Unless told otherwise, model any code you write on the current API and code that uses it.  Ignore
the legacy API and code that uses it unless explicitly instructed to use it as a reference.
