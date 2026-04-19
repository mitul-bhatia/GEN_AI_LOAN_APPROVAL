# Milestone 2 Master Documentation Prompt (Code-Grounded)

Use this prompt when you want an exhaustive, implementation-faithful documentation rewrite for this repository.

## Prompt

You are a senior software architect and technical writer. Your job is to produce a complete, code-grounded Milestone 2 documentation suite.

### Non-Negotiable Rules

1. Read the code first, then write docs. Do not infer features that are not present in code.
2. Every major claim must map to concrete files/functions/endpoints in `MILESTONE_2/creditsense`.
3. If docs and code conflict, code is the source of truth.
4. Mark unknowns explicitly instead of guessing.
5. Keep architecture and flow explanations visual and operationally precise.

### Scope to Audit

Read all of these before writing:

- `MILESTONE_2/creditsense/api.py`
- `MILESTONE_2/creditsense/app.py`
- `MILESTONE_2/creditsense/agent/graph.py`
- `MILESTONE_2/creditsense/agent/nodes.py`
- `MILESTONE_2/creditsense/agent/state.py`
- `MILESTONE_2/creditsense/agent/prompts.py`
- `MILESTONE_2/creditsense/services/*.py`
- `MILESTONE_2/creditsense/scripts/*.py`
- `MILESTONE_2/creditsense/requirements.txt`
- `MILESTONE_2/creditsense/.env.example`
- `MILESTONE_2/creditsense/Procfile`
- `MILESTONE_2/creditsense/render.yaml`
- `MILESTONE_2/creditsense/runtime.txt`
- all files in `docs/*.md`

### Required Deliverables

1. **Architecture-first explanation**
   - Component architecture
   - Turn-level control flow
   - Data flow from user input to decision output
   - Retrieval path and citation generation path
   - Decision path: ML + policy + report + translation

2. **Implementation-backed docs refresh**
   - Update all docs in `docs/` to current code reality
   - Fix stale dependency/model references
   - Fix stale endpoint/request schema references
   - Update line counts and file map metadata where relevant

3. **Visual quality improvements**
   - Add/refresh Mermaid diagrams for:
     - System architecture
     - Input-to-output sequence
     - LangGraph control flow
     - Deployment/runtime view
   - Ensure diagram labels match code naming

4. **Viva-ready material**
   - Add concise oral-defense Q&A
   - Add “Why this design” and “trade-off” justification
   - Add “Challenges faced + how solved in code”
   - Add “Code ownership and integrity declaration” checklist

5. **Strict accuracy checks before final output**
   - Verify docs mention the actual embedding implementation currently used
   - Verify startup ports and script defaults from shell scripts
   - Verify API contracts against request/response models in `api.py`
   - Verify fallback behavior (LLM, ML, translation/report) from code

### Output Format

Return the result in this order:

1. `Findings`: exact drift items discovered (docs vs code)
2. `Applied changes`: file-by-file what you changed
3. `Validation`: commands run and what they confirmed
4. `Residual gaps`: items still pending or requiring future work

### Style

- Clear, technical, evidence-based
- No marketing fluff
- Use short sections, tables, and bullet points for readability
- Prefer concrete values and function names over generic statements

### Quality Bar

The final docs should be sufficient for:

- full viva preparation
- architecture defense
- report/PPT generation
- onboarding a new engineer without reading the whole codebase first
