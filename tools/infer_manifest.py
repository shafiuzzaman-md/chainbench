#!/usr/bin/env python3
import re, argparse, yaml
from pathlib import Path

# Fallbacks by CWE id
SEG_DEFAULTS = {
    121:"STACK",122:"HEAP",124:"DATA",126:"DATA",127:"DATA",
    190:"DATA",191:"DATA",194:"DATA",197:"DATA",369:"DATA",
    401:"HEAP",415:"HEAP",416:"HEAP",78:"DATA",114:"DATA",
    226:"DATA",272:"DATA",273:"DATA",321:"DATA",367:"DATA",
    476:"DATA",590:"HEAP"
}
TRIGGER_CWES = {190,191,194,197,367,369}

IO_RE = {
    "ENV":   re.compile(r'\bgetenv\s*\('),
    "STDIN": re.compile(r'\b(fgets|gets|scanf|getchar)\s*\('),
    "FILE":  re.compile(r'\b(fopen|freopen|fread|fwrite)\s*\(')
}
HEAP_RE = re.compile(r'\b(malloc|calloc|realloc|free)\s*\(')
STACK_RE = re.compile(r'\balloca\s*\(|\b[a-zA-Z_]\w*\s+\w+\s*\[[^\]]+\]\s*;')  # crude local array
DATA_RE  = re.compile(r'\bstatic\s+[^;]+;')
EXEC_RE  = re.compile(r'\b(system|execl|execlp|execle|execv|execvp|popen)\s*\(')
CALLPTR_RE = re.compile(r'\(\s*\*\s*\w+\s*\)\s*\(')  # (*fp)(...)
WRITE_RE = re.compile(r'\b(memcpy|memmove|strcpy|strcat|sprintf|snprintf)\s*\('
                      r'|[\]\)]\s*=\s*' )
READ_RE  = re.compile(r'\b(memcmp|strcmp|strncmp|strchr|strnlen)\s*\(')
DIVZERO_RE = re.compile(r'/\s*0\b')

def cwe_from_path_or_stem(item):
    name = item.get("stem") or Path(item.get("path","")).stem
    m = re.match(r'CWE(\d+)', name or '')
    return int(m.group(1)) if m else None

def read_src(jroot: Path, item: dict) -> str:
    if "path" in item:
        p = Path(item["path"])
        src = (jroot / p) if not p.is_absolute() else p
    else:
        stem = item["stem"]
        hits = list((jroot/"testcases").glob(f"**/{stem}.c"))
        if not hits:
            return ""
        src = hits[0]
    try:
        return src.read_text(errors="ignore")
    except:
        return ""

def infer_io(txt: str) -> str:
    if IO_RE["ENV"].search(txt): return "ENV"
    if IO_RE["STDIN"].search(txt): return "STDIN"
    if IO_RE["FILE"].search(txt): return "FILE"
    return "STDIN"

def infer_segment(txt: str, cwe: int|None) -> str:
    if HEAP_RE.search(txt): return "HEAP"
    if STACK_RE.search(txt): return "STACK"
    if DATA_RE.search(txt):  return "DATA"
    return SEG_DEFAULTS.get(cwe, "DATA")

def infer_effect(txt: str, cwe: int|None) -> str:
    if EXEC_RE.search(txt):    return "EXEC"
    if CALLPTR_RE.search(txt): return "CALL"
    if WRITE_RE.search(txt):   return "WRITE"
    if READ_RE.search(txt):    return "READ"
    if cwe in TRIGGER_CWES:    return "TRIGGER"
    if DIVZERO_RE.search(txt): return "TRIGGER"
    return "READ"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--juliet-root", required=True)
    ap.add_argument("--in", dest="in_yaml", required=True)
    ap.add_argument("--out", dest="out_yaml", required=True)
    args = ap.parse_args()

    jroot = Path(args.juliet_root).resolve()
    spec  = yaml.safe_load(Path(args.in_yaml).read_text())
    items = spec.get("items", [])
    resolved = []

    for it in items:
        txt = read_src(jroot, it)
        cwe = cwe_from_path_or_stem(it)

        io      = it.get("io")      or infer_io(txt)
        segment = it.get("segment") or infer_segment(txt, cwe)
        effect  = it.get("effect")  or infer_effect(txt, cwe)

        out = dict(it)
        out["io"] = io
        out["segment"] = segment
        out["effect"] = effect
        resolved.append(out)

    Path(args.out_yaml).write_text(
        yaml.safe_dump({"items": resolved}, sort_keys=False)
    )
    print(f"[ok] wrote {args.out_yaml} (items={len(resolved)})")

if __name__ == "__main__":
    main()
