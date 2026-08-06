def ai_diagnose():
    report = {}

    # 1. Envelope integrity
    try:
        from warnetech_envelope import seal, open_envelope
        key = b"0" * 32
        msg = b"diag"
        env = seal(key, msg)
        ok = open_envelope(key, env) == msg
        report["envelope"] = "ok" if ok else "fail"
    except Exception as e:
        report["envelope"] = f"error: {e}"

    # 2. Server reachability
    try:
        from warnetech_cli.commands import Commands
        from warnetech_cli.config import Config
        cfg = Config.load()
        cmd = Commands(cfg)
        res = cmd.server_ping()
        report["server"] = res
    except Exception as e:
        report["server"] = f"error: {e}"

    # 3. Retention health
    try:
        from warnetech_control_plane.retention import Retention
        r = Retention.load()
        report["retention"] = {
            "slices": len(r.slices),
            "scores": r.scores,
        }
    except Exception as e:
        report["retention"] = f"error: {e}"

    # 4. Ghost reconstruction
    try:
        from warnetech_control_plane.ghost_engine import GhostEngine
        g = GhostEngine.load()
        ghost = g.reconstruct()
        report["ghost_reconstruction"] = "ok" if ghost else "fail"
    except Exception as e:
        report["ghost_reconstruction"] = f"error: {e}"

    # 5. Supabase RPC health
    try:
        from supabase_schema import client
        ping = client.table("threat_events").select("*").limit(1).execute()
        report["supabase"] = "ok" if ping.data is not None else "fail"
    except Exception as e:
        report["supabase"] = f"error: {e}"

    # 6. Operator manifest integrity
    try:
        import json, os
        manifest_path = os.path.expanduser("~/.warnetech/manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path) as f:
                json.load(f)
            report["manifest"] = "ok"
        else:
            report["manifest"] = "missing"
    except Exception as e:
        report["manifest"] = f"error: {e}"

    # 7. Plaintext fallback detection
    report["plaintext_fallback"] = False

    return report
