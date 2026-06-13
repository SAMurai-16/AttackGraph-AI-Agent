import time

def extract(row: dict, severity: str) -> dict:
    timestamp = row.get("_time") or row.get("time") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    dest_ip   = row.get("dest_ip", "unknown_target")
    pkt_count = int(row.get("pkt_count", 0))
    src_ips   = row.get("src_ips", "")
    if isinstance(src_ips, str):
        src_ips = src_ips.split("|")
    elif not isinstance(src_ips, list):
        src_ips = [str(src_ips)]

    nodes = [
        {"id": f"ip:{dest_ip}", "type": "IP", "attrs": {"address": dest_ip, "severity": severity, "type": "destination"}}
    ]
    edges = []

    for ip in src_ips:
        ip = ip.strip()
        if not ip:
            continue
        nodes.append({
            "id":    f"ip:{ip}",
            "type":  "IP",
            "attrs": {"address": ip, "type": "source"}
        })
        edges.append({
            "src":   f"ip:{ip}",
            "dst":   f"ip:{dest_ip}",
            "rel":   "FLOODED",
            "attrs": {
                "time":       timestamp,
                "pkt_count":  pkt_count,
                "severity":   severity,
                "evidence":   "ddos_traffic"
            }
        })

    return {"nodes": nodes, "edges": edges}
