----------------------------
SPLUNKAGENT — TEXT DESCRIPTION
----------------------------

[+] **SplunkAgent** is a Splunk app that turns Splunk Enterprise into an autonomous SOC (Security Operations Center) investigator. When a security alert fires, the app converts the raw alert telemetry into an in-memory attack graph and then lets an LLM-powered AI agent traverse that graph to find patient zero, score competing attack hypotheses, map the campaign to MITRE ATT&CK, and publish a human-readable incident report — all inside Splunk's own UI.
[+] The agent is exposed to any LLM client through the **Model Context Protocol (MCP)**. The Splunk MCP Server proxies the LLM's tool calls down to a custom Splunk REST endpoint shipped with this app, so Splunk itself becomes the tool provider. No external graph database is required; everything lives in NetworkX.

----x----x----x----x----x----

----------------------------
WHAT PROBLEM IT SOLVES
----------------------------

[+] SOC analysts get buried under alert noise. Each alert is a fragment — a failed login here, a suspicious process there — and the analyst has to mentally stitch them into a story, attribute them to a known attack pattern, and write up a verdict. SplunkAgent automates that stitching.
[+] **Deterministic scoring, LLM interpretation.** The scoring math is fixed in code (weights per attack pattern). The LLM only *interprets* the scored output and writes the narrative. This avoids the failure mode where an LLM hallucinates probabilities or invents evidence.
[+] **Explainable.** Every verdict is backed by named evidence edges in the graph and mapped to MITRE tactics/techniques, so an analyst can audit *why* the agent reached its conclusion.

----x----x----x----x----x----

----------------------------
HOW IT WORKS (END-TO-END)
----------------------------

[+] **1. Alert fires.** Scheduled Splunk searches in [default/savedsearches.conf](default/savedsearches.conf) detect activity matching one of five attack types (DDoS, cloud identity anomaly, brute-force credentials, malware/ransomware, lateral movement) and trigger the custom `seed_graph` alert action ([default/alert_actions.conf](default/alert_actions.conf)).
[+] **2. Telemetry → graph.** The alert action runs [bin/seed_graph.py](bin/seed_graph.py), which reads the alert JSON from stdin, routes by `attack_type` to a handler in [bin/seed_handlers/](bin/seed_handlers/), and POSTs the extracted nodes (Users, Hosts, IPs) and evidence-tagged edges into the in-memory graph.
[+] **3. Agent investigates.** The LLM client (Claude, Splunk AI Assistant, etc.) connects to the Splunk MCP Server, discovers the 14 SplunkAgent tools, and follows the 7-step Standard Operating Procedure returned by `graph_get_system_prompt`.
[+] **4. Report published.** The final tool call writes a JSON + Markdown incident report into [appserver/static/reports/](appserver/static/reports/) and appends a one-line verdict to verdicts.log. A Dashboard Studio page in Splunk reads these and renders the investigation feed.

----x----x----x----x----x----

----------------------------
THE 7-STEP AGENT SOP
----------------------------

[+] **Step 1 — Historical Context.** `graph_get_historical_investigations` checks if the entity (e.g. `user:alice`) has been convicted before. Avoids redundant work and links repeat offenders.
[+] **Step 2 — Patient Zero.** `graph_get_patient_zero` finds compromised nodes with in-degree 0 (no inbound edges), sorted by most recent activity. This is the root of the attack.
[+] **Step 3 — Traversal + Live Hunt.** `graph_generate_attack_path` walks the graph from patient zero, building a time-ordered chain of evidence edges. If evidence is sparse, the agent is instructed to write fresh SPL queries against Splunk, find additional logs, and inject them back as new nodes/edges using `graph_add_node` / `graph_add_edge` before re-scoring.
[+] **Step 4 — MITRE Mapping.** `graph_map_mitre` translates the top-scoring attack hypothesis into official MITRE tactics and technique IDs (e.g. T1110 Brute Force, T1486 Data Encrypted for Impact).
[+] **Step 5 — Executive Summary.** The LLM synthesises a concise two-sentence summary from the path, evidence, and MITRE mapping.
[+] **Step 6 — Publish Report.** `graph_generate_incident_report` writes the verdict, timeline, MITRE block, and all hypothesis scores to JSON + Markdown files and appends to verdicts.log.
[+] **Step 7 — Reset.** `graph_reset` wipes the in-memory graph so the next alert investigation starts clean.

----x----x----x----x----x----

----------------------------
FEATURE SUMMARY
----------------------------

[+] **In-memory NetworkX attack graph.** A `MultiDiGraph` persisted to `bin/tools/graph.json` between MCP calls. Nodes are Users/Hosts/IPs; edges carry `time`, `evidence`, `severity`, and `edge_type`.
[+] **14 MCP graph tools.** add_node, add_edge, get_patient_zero, get_shortest_path, get_neighbours, get_graph_summary, get_investigation_playbook, score_hypotheses, map_mitre, generate_attack_path, get_historical_investigations, get_system_prompt, generate_incident_report, reset.
[+] **5 attack-pattern templates** with deterministic evidence weights (DDoS, cloud identity, brute-force, malware/ransomware, lateral movement) — see PATTERNS dict in [bin/tools/tools.py](bin/tools/tools.py).
[+] **MITRE ATT&CK mapping** for each attack type, tactic + technique IDs encoded in MITRE_MAP.
[+] **Hypothesis scoring engine.** For every pattern, scans graph edges for matching `evidence` tags, sums their weights, normalises to a 0–100 % probability, and ranks all hypotheses.
[+] **Time-aware attack-path generator.** BFS from patient zero, filtered by evidence-tagged edges, sorted by timestamp, with per-path subgraph re-scoring.
[+] **Live evidence hunting.** Agent can dynamically inject new nodes/edges mid-investigation when graph evidence is insufficient.
[+] **Historical memory.** Past verdicts in `verdicts.log` are queried by patient-zero ID so the agent recognises repeat offenders across investigations.
[+] **Auto-generated incident reports** (JSON + Markdown) plus a verdicts log, all served from the Splunk app's static directory.
[+] **Single-endpoint MCP dispatch.** All 14 tools route through one Splunk REST endpoint (`services/graph_execute_operation`) that dispatches on an `action` field, so adding a new tool needs no new endpoint and no Splunk restart.
[+] **Alert ingestion pipeline.** Scheduled saved searches → `seed_graph` alert action → attack-type-specific extraction handler → graph endpoint. Five attack types wired end-to-end out of the box.

----x----x----x----x----x----

----------------------------
TECH STACK
----------------------------

[+] **Splunk Enterprise 10.x** — host platform, scheduled searches, alert actions, REST endpoints, KV store.
[+] **Splunk_MCP_Server** (vendor app) — the MCP transport that the LLM talks to; SplunkAgent registers its tools into this server's KV-backed tool registry.
[+] **Python 3.13** (Splunk's bundled interpreter) — handlers and tools.
[+] **NetworkX** (vendored under bin/networkx/) — graph engine. No Neo4j, no Cypher.
[+] **MCP (Model Context Protocol)** — tool discovery + invocation contract used by the LLM client.
[+] **httpx / requests / python-dotenv** — for credentialed REST calls and `.env` loading.
[+] **Splunk Dashboard Studio** — renders the verdict feed and report links inside Splunk UI.

----x----x----x----x----x----

----------------------------
SECURITY MODEL
----------------------------

[+] All MCP calls hit Splunk over HTTPS on port 8089 and are authenticated with a Splunk bearer token (minted via `/services/authorization/tokens`).
[+] Credentials for local scripts live in a `.env` at the app root (loaded via python-dotenv); `.env` is gitignored.
[+] Each registered tool is gated by Splunk's RBAC capability system; the MCP server requires the `mcp_tool_admin` capability for registration and per-tool enable.
[+] The scoring math is server-side and deterministic — an LLM cannot inflate a probability or invent evidence; it can only call tools and interpret their JSON output.

----x----x----x----x----x----

----------------------------
EXTENSIBILITY
----------------------------

[+] **New attack type:** add an entry to PATTERNS and MITRE_MAP in [bin/tools/tools.py](bin/tools/tools.py), drop a seed handler in [bin/seed_handlers/](bin/seed_handlers/), and add a saved search in [default/savedsearches.conf](default/savedsearches.conf).
[+] **New graph tool:** write a `<name>_tool(...)` function in tools.py, add an `elif action == '<name>':` branch in [bin/mcp_handler.py](bin/mcp_handler.py), append a tool schema in [bin/register_tools.py](bin/register_tools.py), and re-run that script. No Splunk restart needed.
[+] **Different LLM client:** any MCP-compliant client works — just point it at `https://<splunk-host>:8089/services/mcp` with a bearer token.

----x----x----x----x----x----

----------------------------
WHY THIS APPROACH IS DIFFERENT
----------------------------

[+] **Graph-native, not log-native.** Most SOC tooling operates on flat log searches. SplunkAgent reasons over a typed graph, so questions like "what hosts did Alice touch before the alert?" or "who is patient zero?" become single graph traversals instead of multi-stage SPL.
[+] **Splunk *is* the MCP tool provider.** The agent doesn't pull data out of Splunk to reason elsewhere — Splunk itself exposes the investigation tools, so authentication, RBAC, audit, and TLS are inherited from Splunk's existing controls.
[+] **Determinism boundary is explicit.** The LLM is sandboxed to interpretation; the graph + scoring engine handle all numeric judgement. This makes the system auditable and resistant to prompt-injection attempts in log content.
[+] **Closed loop.** Investigations end with a written report and a verdict appended to a log that *future* investigations consult — the agent builds institutional memory automatically.

----x----x----x----x----x----
