# Project Vision

**AttackGraph AI**

> An **AgenticOps** SOC investigator for the **Security Track** that transforms Splunk telemetry into a security knowledge graph. It autonomously loops to gather evidence, generates multiple attack hypotheses, scores them using deterministic graph analytics, and visualizes attack paths with explainable confidence.

---

# High-Level Architecture (The Agentic Loop)

```
                  Analyst
                     │
                     ▼
             Splunk UI / React
                     │
                     ▼
           Investigation Agent
      (Splunk AI Toolkit / Python SDK)
                     │
                     ▼
             Splunk MCP Server
       (Extended with Custom NetworkX Tools)
         ┌───────────┴───────────┐
         │                       │ (Iterative Loop)
         ▼                       ▼
    Splunk Data             Knowledge Graph
   (Query Logs)       (Graph Building & Scoring)
```

---

# Core Components

## 1. Autonomous Investigation Loop

Unlike a linear automation script, the agent acts iteratively:

1. **Trigger:** `Investigate Alert #4812`
2. **Observe:** Agent queries Splunk for initial context via Splunk MCP Server.
3. **Act:** Agent extracts entities and pushes them to the networkX graph.
4. **Reason:** Agent queries the graph for gaps (e.g., "I see a malicious IP, but how did the user get infected?").
5. **Loop:** Agent autonomously decides to run a new Splunk query for email or web proxy logs.
6. **Conclude:** Once evidence is sufficient, it maps to MITRE and presents the findings to reduce MTTR.

---

## 2. Knowledge Graph Builder (LLM ETL)

Splunk logs are semi-structured text. The Agent (LLM) acts as the ETL engine, using Named Entity Recognition (NER) to convert raw logs dynamically into structured Cypher queries.

### Nodes

```
User
Host
IP
Domain
Process
Alert
File
```

### Relationships (Time-Aware)

Temporal sequencing is critical. All edges must contain timestamps so the graph knows event order:

```
LOGGED_INTO {time: "10:05:00"}
SPAWNED {time: "10:06:12"}
CONNECTED_TO
DOWNLOADED
EXECUTED
TRIGGERED
```

Example Cypher execution by LLM:
```cypher
CREATE (u:User {name: 'alice'})-[:LOGGED_INTO {time: '10:05:00'}]->(h:Host {name: 'HR-LAPTOP'})
```

---

## Why networkX?

The graph lets you ask topological and temporal questions simultaneously:

```cypher
MATCH p=(u:User)-[*..5]->(ip:IP)
RETURN p
```

Questions like:
- What machines did Alice touch before the alert?
- Which hosts contacted this IP?
- What is patient zero (node with in-degree 0)?

become trivial.

---

# 3. Attack Pattern Library

Create attack templates in the graph.

Example:

```json
{
  "name":"Credential Theft",
  "evidence": [
    "failed_logins",
    "new_device",
    "impossible_travel",
    "suspicious_ip"
  ]
}
```

Store 10–20 common scenarios (Ransomware, Lateral Movement, Insider Threat, etc.).

---

# 4. Evidence Scoring Engine (Graph Analytics)

The Graph Database handles the deterministic math (not the LLM). Each evidence type contributes weight.

Example:
```json
weights = {
  "failed_logins": 15,
  "new_device": 20,
  "impossible_travel": 30,
  "malicious_ip": 25
}
```

The backend runs pattern-matching Cypher queries.
`score = Σ evidence_weights`
`probability = score / total_score`

---

# 5. Hypothesis Interpretation (LLM Role)

The LLM is NOT doing the math. The graph evaluates the rules and scores. The LLM's job is to interpret the graph's output and explain it to the human analyst.

Example graph output returned to Agent:
```json
[
  {"attack": "Credential Theft", "probability": 64, "evidence": ["impossible_travel", "new_device"]},
  {"attack": "Insider Threat", "probability": 22, "evidence": ["mass_file_modification"]}
]
```

Agent translates this into a human-readable investigation summary (e.g., "I am 64% confident this is Credential Theft because...").

---

# 6. MITRE ATT&CK Mapping

Map graph events.

```
PowerShell
→ T1059

Credential Dumping
→ T1003
```

Store as tags directly on the edges: `[:EXECUTED {technique: "T1059", confidence: 0.91}]`

---

# 7. Attack Path Generator

Build paths from graph traversals temporally.

```
Initial Access (10:00)
  ↓
Execution (10:05)
  ↓
Credential Access (10:15)
  ↓
Lateral Movement (10:30)
```

---

# 8. Frontend Visualization

Use the Splunk UI Framework (React-based) to build this as a native Splunk App, or a standalone React App using the Splunk Design System.

**Screens:**
1. **Investigation Chat:** Interact with the Splunk Agent.
2. **Attack Hypotheses:** See probabilities for different attacks.
3. **Attack Path:** Visual graph of the attack (using React Flow or Cytoscape.js).


# Hackathon Build Phases

Organised as milestones, not fixed days. Each phase ends with something runnable.

* **Phase 0 - Scaffold.** Project skeleton, config, .env.example, pytest smoke test.
* **Phase 1 - Data.** Sample-data generator emits graph-shaped, CIM-normalised events with 2-3 multi-stage, ground-truth-labelled scenarios.
* **Phase 2 - Graph.** Build the knowledge graph in NetworkX; add neighbours, shortest-path, and find_patient_zero traversals behind a clean interface.
* **Phase 3 - Patterns.** Config-driven attack template library (start with 5: Credential Theft, Ransomware, Lateral Movement, Data Exfiltration, Living-off-the-Land).
* **Phase 4 - Scoring.** Evidence detectors + deterministic per-hypothesis scoring, each weight with a rationale; full unit-test coverage.
* **Phase 5 - Explain.** MITRE technique/tactic mapping + attack-path generator from patient zero to impacted asset, every step cited.
* **Phase 6 - Agent.** Orchestrate tools (search_splunk, build_graph, find_patient_zero, score_hypotheses, map_mitre, generate_attack_path) in the ReAct loop; enforce read-only access and prompt-injection handling on log content.
* **Phase 7 - Report.** Structured incident report (JSON + Markdown), audit trail, verdict write-back to Splunk.
* **Phase 8 - Frontend (stretch).** React views: chat, hypotheses, evidence, attack graph.
* **Phase 9 - Evaluation.** 10 labelled scenarios + harness reporting precision/recall and top-hypothesis accuracy; optional Neo4j backend; hardening.
* **Phase 10 - Demo.** Scripted narrative, pre-seeded data, cached known-good run, slides.

### Minimum Shippable Core
If time runs short, ship Phases 1-7 plus Phase 9's evaluation harness. That is a graph-driven, explainable, MITRE-mapped investigator with a real incident report and a measured accuracy number, even without the React UI.