claude.md loaded everytime, keep it conscise and global. use /init for cluade.md generation via claude itself.
(adds persistent context Claude sees every session)


skills/ for individual roles
(add reusable knowledge and invocable workflows)

rules/ for setting boundariess and stufff like migrations

commands/ for server startup commands and testing commands we want agent to run
(commands and skills are now similar)

hooks/ 
- pre tool use
- post tool use
- event based (when claude asks for prompt, session start, session end, file changed, permission request, )
- exit codes; 0,1,2


/mcps

agents/
isolated mutually exlucded tasks for saving up the context with memory so optimized for next run


agent teams (BETA) they are interconnected


-p for headless mode (not same as allowed edits, its hui less, permissions are needed)
claude -p 'craete a dummy. py file' --dangerously-skip-permissions


claude -p "if dummy. py exists" >> claude-tasks. log 2>&1

/loop for iteration, automatically


plugins and market place to ship these (.claude stuff)



Claude gets a convention or command wrong twice - Add it to CLAUDE.md
You keep asking Claude to be shorter, explain more, or answer in the same format - Set an output style
You keep typing the same prompt to start a task - Save it as a user-invocable skill
You paste the same playbook or multi-step procedure into chat for the third time - Capture it as a skill
You keep copying data from a browser tab Claude can’t see - Connect that system as an MCP server
Claude reads many files to find where a symbol is defined or used - Install a code intelligence plugin for your language
A side task floods your conversation with output you won’t reference again - Route it through a subagent
You want something to happen every time without asking - Write a hook
A second repository needs the same setup - Package it as a plugin