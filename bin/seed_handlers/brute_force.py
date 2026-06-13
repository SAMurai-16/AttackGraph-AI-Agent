import time

def extract(row: dict, severity: str) -> dict:
    timestamp = row.get("_time") or row.get("time") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    user       = row.get("user", "unknown_user")
    dest_host  = row.get("dest", "unknown_host")
    fail_count = int(row.get("fail_count", 0))
    src_ips    = row.get("src_ips", "")
    if isinstance(src_ips, str):
        src_ips = src_ips.split("|") if src_ips else []
    elif not isinstance(src_ips, list):
        src_ips = [str(src_ips)]

    nodes = [
        {"id": f"user:{user}",       "type": "User",  "attrs": {"name": user}},
        {"id": f"host:{dest_host}",  "type": "Host",  "attrs": {"name": dest_host, "severity": severity}},
    ]
    edges = []

    for ip in src_ips:
        ip = ip.strip()
        if not ip:
            continue
        nodes.append({
            "id":    f"ip:{ip}",
            "type":  "IP",
            "attrs": {"address": ip}
        })
        edges.append({
            "src":   f"ip:{ip}",
            "dst":   f"host:{dest_host}",
            "rel":   "ATTEMPTED_LOGIN",
            "attrs": {
                "time":       timestamp,
                "fail_count": fail_count,
                "severity":   severity,
                "evidence":   "failed_logins"
            }
        })

    # Tag the alert on the user node
    edges.append({
        "src":   f"user:{user}",
        "dst":   f"host:{dest_host}",
        "rel":   "TARGETED_BY_BRUTE_FORCE",
        "attrs": {
            "time":       timestamp,
            "fail_count": fail_count,
            "evidence":   "failed_logins",
            "severity":   severity
        }
    })

    return {"nodes": nodes, "edges": edges}
