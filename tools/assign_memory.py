#!/usr/bin/env python3
"""
assign_memory.py
Stamp deterministic fixed bases & sane region sizes into a resolved manifest.

Usage:
  python3 tools/assign_memory.py \
    --in  manifests/selected_resolved.yaml \
    --out manifests/selected_resolved_mem.yaml

Options:
  --start-slot N   Offset the first slot per segment (default 0)
  --dry-run        Print mapping to stdout; do not write file
"""
from __future__ import annotations
import argparse, sys, yaml
from pathlib import Path

# -------------------- Pools (segment -> base, stride) --------------------
POOLS = {
    "DATA":      (0x40000000, 0x00010000),
    "HEAP":      (0x50000000, 0x00010000),
    "STACK":     (0x60000000, 0x00010000),
    "CODE":      (0x70000000, 0x00010000),
    "PROTECTED": (0x80000000, 0x00010000),
}

# -------------------- Region size defaults by CWE family -----------------
BUF_CWES   = {121,122,124,126,127}
INT_CWES   = {190,191,194,197}
UAF_DF_LEAK= {415,416,401}
CMD_PROC   = {78,114,272,273,321}
MISC_CWES  = {367,369,476,481,484,526,457,467,587,562,364}

def default_region_size(cwe: int | None) -> int:
    if cwe in BUF_CWES:    return 0x2000
    if cwe in INT_CWES:    return 0x1000
    if cwe in UAF_DF_LEAK: return 0x2000
    if cwe in CMD_PROC:    return 0x4000
    if cwe in MISC_CWES:   return 0x1000
    return 0x1000

# -------------------- Helpers --------------------
def get_stem(item: dict) -> str:
    if "stem" in item and item["stem"]:
        return item["stem"]
    if "path" in item and item["path"]:
        return Path(item["path"]).stem
    return ""

def parse_cwe_from_stem(stem: str) -> int | None:
    # Expect "CWE123_..." -> 123
    if stem.startswith("CWE"):
        try:
            return int(stem[3:].split("_", 1)[0])
        except Exception:
            return None
    return None

def normalize_segment(seg: str | None) -> str:
    seg = (seg or "DATA").upper()
    if seg not in POOLS:
        return "DATA"
    return seg

# -------------------- Main logic --------------------
def assign_memory(items: list[dict], start_slot: int) -> tuple[list[dict], list[tuple]]:
    """
    Returns (updated_items, mapping_rows) where mapping_rows are
    (stem, seg, slot, base, size, addr_class).
    """
    # Deterministic order by stem so slot assignment is stable
    sorted_items = sorted(items, key=lambda it: get_stem(it))

    # Allocate slots per segment
    next_slot = {seg: start_slot for seg in POOLS.keys()}
    mapping = []
    updated = []

    for it in sorted_items:
        stem = get_stem(it)
        seg  = normalize_segment(it.get("segment"))
        cwe  = it.get("cwe") or parse_cwe_from_stem(stem)
        size = int(it.get("region_size", 0)) or default_region_size(cwe)

        base0, stride = POOLS[seg]
        slot = next_slot[seg]
        fixed_base = base0 + stride * slot
        next_slot[seg] += 1

        # Respect pre-existing fixed_base/addr_class if already set
        fixed_base = it.get("fixed_base", fixed_base)
        addr_class = (it.get("addr_class") or "FIXED").upper()

        # Update manifest item in-place
        out = dict(it)
        out["segment"]     = seg
        out["addr_class"]  = addr_class
        out["fixed_base"]  = fixed_base
        out["region_size"] = size
        updated.append(out)

        mapping.append((stem, seg, slot, fixed_base, size, addr_class))

    # Preserve original order in output (nice for diffs)
    by_stem = {get_stem(u): u for u in updated}
    result_items = [by_stem.get(get_stem(it), it) for it in items]
    return result_items, mapping

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="in_yaml",  required=True)
    ap.add_argument("--out", dest="out_yaml", required=True)
    ap.add_argument("--start-slot", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    spec = yaml.safe_load(Path(args.in_yaml).read_text())
    items = spec.get("items", [])
    if not items:
        print("[err] input manifest has no items", file=sys.stderr)
        sys.exit(1)

    new_items, mapping = assign_memory(items, args.start_slot)

    if args.dry_run:
        print("stem,segment,slot,fixed_base,region_size,addr_class")
        for row in mapping:
            stem, seg, slot, base, size, cls = row
            print(f"{stem},{seg},{slot},0x{base:08x},{size},{cls}")
        return

    out_spec = dict(spec)
    out_spec["items"] = new_items
    Path(args.out_yaml).write_text(yaml.safe_dump(out_spec, sort_keys=False))
    print(f"[ok] wrote {args.out_yaml} (items={len(new_items)})")

if __name__ == "__main__":
    main()
