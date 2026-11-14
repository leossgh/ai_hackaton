---
id: getting-started-gs-install-login
type: article
title: Install the CLIs and log in
gloss: Foundry has two clients and a set of agent skills.
examples:
- What are the two clients in Foundry and what does each one do?
- how do i log in to the registry client and set up docker?
- How do I install the Hub client?
- I want to submit runs to my Hub. Which CLI do I need and how do I authenticate?
- What are skills and how do I get them?
- What commands download the foundry-toolkit and apheris-workflow-predict skills?
- How can I see the newest available skills?
- Python version needed for apheris-foundry?
---
# Install the CLIs and log in

Foundry has two clients and a set of agent skills.

1. **Registry client `foundry-toolkit` (Go)** — lists and fetches modules, weights,
   skills and workflows, and runs workflows standalone. Build or use a release
   build, then log in and wire Docker:
   ```
   foundry-toolkit login
   foundry-toolkit docker configure
   ```
2. **Hub client `apheris-foundry` (Python 3.10+)** — submits and manages runs on
   a Hub:
   ```
   pip install apheris-foundry-cli
   apheris-foundry login --url https://hub.example.com
   ```
3. **Skills** — the instructions an agent/LLM uses to run a workflow. List and
   fetch them, or copy from a checkout:
   ```
   foundry-toolkit skill list --latest
   foundry-toolkit skill get --name foundry-toolkit --version <v> --to <skills-dir>
   foundry-toolkit skill get --name apheris-workflow-predict --version <v> --to <skills-dir>
   ```

Next: the shared get-and-run pattern ([[gs-run-a-workflow]]).
