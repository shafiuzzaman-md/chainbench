#!/usr/bin/env python3
import os, sys, subprocess, json
from pathlib import Path

try:
    import yaml  # pip install pyyaml
except Exception as e:
    print("[!] Missing PyYAML. Run: pip install pyyaml", file=sys.stderr); sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "export" / "items"
DEFAULT_PAYLOAD = b"12\n"

def ensure_payload(item_dir: Path):
    p = item_dir / "payload.bin"
    if not p.exists():
        p.write_bytes(DEFAULT_PAYLOAD)

def run_item(item_dir: Path, base="0x300000", size="4096", addr_class="FIXED"):
    meta = item_dir / "meta.yaml"
    stem = item_dir.name
    log_out = item_dir / "run.out"
    log_err = item_dir / "run.err"

    if not (item_dir / "app").exists():
        print(f"[SKIP] no app: {stem}")
        return 0

    ensure_payload(item_dir)

    env = os.environ.copy()
    env["CB_ADDR_CLASS"] = addr_class
    env["CB_FIXED_BASE"] = str(base)
    env["CB_REGION_SIZE"] = str(size)

    # Note: main_single reads payload.bin and handles IO mode internally.
    cmd = ["./app"]
    print(f"[RUN] {stem} @ base={env['CB_FIXED_BASE']} size={env['CB_REGION_SIZE']} class={env['CB_ADDR_CLASS']}")
    with log_out.open("wb") as out, log_err.open("wb") as err:
        try:
            proc = subprocess.run(cmd, cwd=item_dir, env=env, stdout=out, stderr=err)
            rc = proc.returncode
        except Exception as e:
            rc = 127
            err.write(f"[runner] Exception: {e}\n".encode())
    if rc != 0:
        print(f"[WARN] exit={rc} → see {log_err}")
    return rc

def build_item(item_dir: Path):
    print(f"[BUILD] {item_dir.name}")
    proc = subprocess.run(["make", "-C", str(item_dir)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        sys.stdout.buffer.write(proc.stdout)
        print(f"[ERR] build failed: {item_dir.name}")
        return False
    return True

def main():
    if not ITEMS.exists():
        print("[!] export/items not found. Generate first with cbgen.py.", file=sys.stderr)
        sys.exit(1)

    # Build all
    built = []
    for item in sorted(ITEMS.iterdir()):
        if item.is_dir():
            ok = build_item(item)
            if ok: built.append(item)

    # Run all
    failures = []
    for item in built:
        rc = run_item(item, base="0x300000", size="4096", addr_class="FIXED")
        if rc != 0:
            failures.append(item.name)

    # Summary
    summary = {
        "built": [p.name for p in built],
        "failed": failures,
        "logs": {p.name: {"out": str((p/"run.out").as_posix()),
                          "err": str((p/"run.err").as_posix())} for p in built}
    }
    print(json.dumps(summary, indent=2))
    if failures:
        sys.exit(2)

if __name__ == "__main__":
    main()
