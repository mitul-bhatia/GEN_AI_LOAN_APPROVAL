# CreditSense Mermaid Diagram Pack

This folder contains the architecture diagrams for the Milestone 2 report and viva preparation.

## Diagram Files

- system-architecture.mmd
- dataflow-pipeline.mmd
- langgraph-control-flow.mmd
- deployment-view.mmd

## Export to PNG (for Viva upload fields)

1. Install Mermaid CLI:

npm install -g @mermaid-js/mermaid-cli

2. Run exports from repository root:

mmdc -i docs/diagrams/system-architecture.mmd -o docs/diagrams/exports/system-architecture.png
mmdc -i docs/diagrams/dataflow-pipeline.mmd -o docs/diagrams/exports/dataflow-pipeline.png
mmdc -i docs/diagrams/langgraph-control-flow.mmd -o docs/diagrams/exports/langgraph-control-flow.png
mmdc -i docs/diagrams/deployment-view.mmd -o docs/diagrams/exports/deployment-view.png

The generated PNG files can be directly uploaded to forms asking for architecture drawings/images under size limits.
