# System Changes / Agent Permissions

IMPORTANT: the files you edit should only be in this local repo, NEVER anywhere else on the system.
I will use pyinfra or scripts to apply changes to the system.

You, the agent, should NEVER run commands on the system that would make permanent changes.  We
ALWAYS put our action plan into code or IAC before applying to the system.

You are ONLY ALLOWED to run READ-ONLY cli commands.

If you are ever confused about what you have permission to do, stop and ask.


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


# UV + mise for dependencies

This repo uses uv for managing Python and Python dependencies.

It uses mise for other dev dependencies and for discoverability and execution of cli tasks.

My command examples will always be from running in a shell that has mise active.  If your shells do
not have mise active, you will to use `mise exec ...` in this repo's base directory to get the same
results.


# Exception catching

Don't catch an exception just to catch it.  Unless it's somewhat expected and you can recover from
it, then just let it bubble up.  We'd rather have the original exception than a re-thrown or hidden
one.


# Subprocess Args & pathlib.Path

Subprocess handles pathlib.Path objects just fine.  Don't wrap in str().
