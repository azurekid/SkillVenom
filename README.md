<img width=70% height=70% alt="image" src="https://github.com/user-attachments/assets/1e90b1f2-92b0-4a9b-b40d-875758e333f5" />

# SkillVenom

SkillVenom is an educational collection of examples illustrating how instructions
embedded in agent skills or source files can try to hijack an agent's behavior.
Treat all examples as untrusted input; do not install or invoke them in a
production agent.

## Example: code-reviewer prompt injection

The [`examples/code-reviewer`](examples/code-reviewer) directory contains a
review skill and a deliberately vulnerable session-validation example. The
source comment demonstrates an instruction to skip tests and misrepresent the
result. Its command is a harmless placeholder: it does not read environment
variables, write secrets, or transmit data.
