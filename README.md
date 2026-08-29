# Conversation-ai-modules

## Overview
This monorepo is used to hold all the python modules used in the conversational chatbots. By consolidating all these projects under a single repository, we hope to reduce version conflicts and better manage the codebase.

## Code guidelines:
- Use poetry for all dependency management. If poetry is unable to add your depeendency, this means that your project will not work with the rest of packages. Poetry is meant to solve problems for you after you finish fighting with it.
- Add type annotations for all functions arguments and returns
- Add docstrings for all functions in Google format (use the plugin - `njpwerner.autodocstring`)
- Do not commit log files into the source tree and watch out what you commit, source tree should only include documentation, code and absolutely necessary resources that will prevent the code from running
- Linearize algorithm code into a `workflow` method where each step happens sequentially.
- The way to write algorithms is to : 1) Write the overall agorithm in comments 2) write down each of the steps 3) write the code (keep updating comments if you change the way you do things)
- Name variables properly so that we can keep track of whats going on in the algorithm
- Try to name functions as `<verb>_<subject>` as much as possible
- Name all the files in snake case
- Name all classes CamelCase with captials starts
- Avoid having `global` variables for libaries. Only applications are allowed to have them
  

## Exporting the Environemtn variables for the backend

```sh
set -o allexport; source .env; set +o allexport
```
