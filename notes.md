skills/ for individual roles

rules/ for setting boundariess and stufff like migrations

commands/ for server startup commands and testing commands we want agent to run

hooks/ 
- pre tool use
- post tool use


/mcps

agents/
isolated mutually exlucded tasks for saving up the context with memory so optimized for next run


agent teams (BETA) they are interconnected


-p for headless mode (not same as allowed edits, its hui less, permissions are needed)
claude -p 'craete a dummy. py file' --dangerously-skip-permissions


claude -p "if dummy. py exists" >> claude-tasks. log 2>&1

/loop for iteration, automatically