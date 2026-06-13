import time

def extract(row: dict, severity: str) -> dict:
    timestamp = row.get("_time") or row.get("time") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    user       = row.get("user", "unknown_user")
    src_ip     = row.get("src", "unknown_src")
    hop_count  = int(row.get("hop_count", 0))
    
    hosts      = row.get("hosts", "")
    if isinstance(hosts, str):
        hosts = hosts.split("|") if hosts else []
    elif not isinstance(hosts, list):
        hosts = [str(hosts)]

    nodes = [
        {"id": f"user:{user}", "type": "User", "attrs": {"name": user, "severity": severity}},
        {"id": f"ip:{src_ip}", "type": "IP",   "attrs": {"address": src_ip}}
    ]
    edges = [
        {"src": f"user:{user}", "dst": f"ip:{src_ip}", "rel": "ORIGINATED_FROM", "attrs": {"time": timestamp}}
    ]

    for host in hosts:
        host = host.strip()
        if not host:
            continue
        nodes.append({
            "id":    f"host:{host}",
            "type":  "Host",
            "attrs": {"name": host}
        })
        edges.append({
            "src":   f"user:{user}",
            "dst":   f"host:{host}",
            "rel":   "LOGGED_INTO",
            "attrs": {
                "time":       timestamp,
                "evidence":   "lateral_movement",
                "severity":   severity,
                "hop_count":  hop_count
            }
        })

    return {"nodes": nodes, "edges": edges}
