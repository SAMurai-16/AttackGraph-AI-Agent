import time

def extract(row: dict, severity: str) -> dict:
    timestamp = row.get("_time") or row.get("time") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    user_id   = row.get("UserId", "unknown_user")
    fail_count= int(row.get("fail_count", 0))
    ip_count  = int(row.get("ip_count", 0))
    
    # We might only get summary counts from the alert, so we add the user node.
    nodes = [
        {"id": f"user:{user_id}", "type": "User", "attrs": {"name": user_id, "severity": severity}}
    ]
    edges = []

    # If src_ip is present (even though the query did a dc()), we extract if available
    src_ips = row.get("src_ip", "")
    if isinstance(src_ips, str):
        src_ips = src_ips.split("|") if src_ips else []
    elif not isinstance(src_ips, list):
        src_ips = [str(src_ips)]

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
            "src":   f"user:{user_id}",
            "dst":   f"ip:{ip}",
            "rel":   "AUTH_ANOMALY",
            "attrs": {
                "time":       timestamp,
                "fail_count": fail_count,
                "ip_count":   ip_count,
                "severity":   severity,
                "evidence":   "cloud_identity_anomaly"
            }
        })

    return {"nodes": nodes, "edges": edges}
