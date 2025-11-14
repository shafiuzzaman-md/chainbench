#!/usr/bin/env python3
import argparse, yaml, shutil, json, sys
from pathlib import Path
from string import Template

ROOT    = Path(__file__).resolve().parents[1]
EXPO    = ROOT / "export"
SRC_DIR = ROOT / "src"
INC_DIR = ROOT / "include"

SEG_CHOICES = {
  "HEAP":"SEG_HEAP","STACK":"SEG_STACK","DATA":"SEG_DATA",
  "CODE":"SEG_CODE","PROTECTED":"SEG_PROTECTED"
}
ACT_CHOICES = {
  "READ":"ACT_READ","WRITE":"ACT_WRITE","EXEC":"ACT_EXEC",
  "CALL":"ACT_CALL","TRIGGER":"ACT_TRIGGER"
}
IO_CHOICES  = {"STDIN","ENV","FILE"}

# ===================== TEMPLATES (Linux-only) =====================

# main_single.c — single place for input + abstract effect/region + call
MAIN_SINGLE_TMPL = Template(r'''/* main_single.c for ${stem}
 *
 * This is the ONLY entrypoint tools need.
 * It models:
 *   (1) Attacker input: CB.plane[0..plane_len) loaded from payload model
 *   (2) Exposure channel (STDIN / ENV / FILE)
 *   (3) ONE abstract region + ONE abstract effect
 *   (4) Call Juliet's ${stem}_bad()
 *
 * To run:
 *   - STDIN mode: put bytes in "payload.bin" next to the app (REQUIRED).
 *   - ENV  mode:  set the content in your launcher, or place payload.bin and
 *                 we will copy it into ENV["${env_key}"] as a C-string.
 *   - FILE mode:  same; we write "${file_name}" with payload bytes.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>  
#include <errno.h>
#include "state.h"

/* Juliet entrypoint (provided by source.c) */
int ${stem}_bad(void);

/* ------------------ payload helpers ------------------ */

/* Load bytes from "payload.bin" if present; return length, or -1 if missing. */
static long read_payload_file(unsigned char* buf, size_t cap){
  FILE* f = fopen("payload.bin","rb");
  if (!f) return -1;
  size_t n = fread(buf,1,cap ? cap-1 : 0,f);
  fclose(f);
  if (cap) buf[n] = '\0'; /* C-string friendly for ENV/FILE users */
  return (long)n;
}

/* Load into CB.plane; caller decides what to do on missing file. */
static int load_payload_into_plane(void){
  memset(CB.plane, 0, sizeof(CB.plane));
  CB.plane_len = 0;
  long n = read_payload_file(CB.plane, sizeof(CB.plane));
  if (n < 0) return 0;            /* not found */
  CB.plane_len = (unsigned)n;
  return 1;                       /* loaded */
}

/* Expose CB.plane -> STDIN (dup2 temp file to stdin). */
static void expose_stdin(void){
  FILE* tmp = tmpfile(); if(!tmp) return;
  if (CB.plane_len) fwrite(CB.plane, 1, CB.plane_len, tmp);
  fflush(tmp); fseek(tmp, 0, SEEK_SET);
  dup2(fileno(tmp), fileno(stdin));
}

/* Expose CB.plane -> ENV["${env_key}"] */
static void expose_env(void){
  if (CB.plane_len == 0) { CB.plane[0] = '\0'; CB.plane_len = 1; }
  else CB.plane[CB.plane_len-1] = '\0';
  setenv("${env_key}", (const char*)CB.plane, 1);
}

/* Expose CB.plane -> file "${file_name}" */
static void expose_file(void){
  FILE* f = fopen("${file_name}", "wb"); if (!f) return;
  if (CB.plane_len) fwrite(CB.plane, 1, CB.plane_len, f);
  fclose(f);
}

/* ------------------ main: input + effect + call ------------------ */

int main(void){
  cb_reset();

  /* (1) attacker input */
  int have_payload = load_payload_into_plane();

  /* (2) exposure channel (from YAML "io") */
#if ${is_stdin}
  if (!have_payload) {
    fprintf(stderr, "[CB] ERROR: STDIN mode requires payload.bin next to the app.\n");
    return 2;
  }
  expose_stdin();
#endif

#if ${is_env}
  if (!have_payload) {
    /* ENV mode: missing payload.bin is allowed; ENV becomes empty string */
    CB.plane[0] = '\0'; CB.plane_len = 1;
  }
  expose_env();
#endif

#if ${is_file}
  if (!have_payload) {
    /* FILE mode: missing payload.bin → empty file */
    CB.plane_len = 0;
  }
  expose_file();
#endif

  /* (3) abstract region + effect (from YAML) */
  uint32_t rid = cb_region(${seg}, ${rsize}, 1);
  cb_effect_push(rid, 0, 0, ${act});

  /* (4) run the vulnerable path */
  (void)${stem}_bad();

  printf("[CB] single_done effects=%u regions=%u payload_len=%u\n",
         CB.effect_count, CB.region_count, CB.plane_len);
  return 0;
}
''')

# adapter.c — used only by scenarios; tools can ignore it.
ADAPTER_TMPL = Template(r'''/* adapter.c for ${stem} (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int ${stem}_bad(void);
#ifdef EMIT_GOOD
int ${stem}_good(void);
#endif

int chainbench_run_${stem}_bad(void){
  uint32_t rid = cb_region(${seg}, ${rsize}, 1);
  cb_effect_push(rid, 0, 0, ${act});
  (void)${stem}_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_${stem}_good(void){
  uint32_t rid = cb_region(${seg}, ${rsize}, 1);
  cb_effect_push(rid, 0, 0, ${act});
  (void)${stem}_good();
  return 0;
}
#endif
''')

ITEM_MK = r'''# Per-item Makefile (Linux)
CC ?= cc
CFLAGS ?= -O2 -g -std=c11 -Wall -Wextra
CFLAGS += -D_POSIX_C_SOURCE=200809L

INCLUDE = -I ../../include -I ../../src
# Optional: interpose libc I/O with tiny loggers (getenv/fgets/fread)
INCLUDE += -include ../../include/cb_interpose.h

SUPPORT_SRCS = $(wildcard ../../support/*.c)
SRCS = main_single.c source.c ../../src/state.c ../../src/cb_io.c $(SUPPORT_SRCS)

all: app
app: $(SRCS)
	$(CC) $(CFLAGS) $(INCLUDE) $(SRCS) -o $@

clean:
	rm -f app
'''

SCEN_MAIN_TMPL = Template(r'''/* Scenario main: execute selected items in order (Linux) */
#include <stdio.h>
#include "state.h"
$decls
int main(void){
  cb_reset();
$calls
  printf("[CB] scenario_done effects=%u regions=%u payload_len=%u\n",
         CB.effect_count, CB.region_count, CB.plane_len);
  return 0;
}
''')

SCEN_MK = r'''# Scenario Makefile (Linux)
CC ?= cc
CFLAGS ?= -O2 -g -std=c11 -Wall -Wextra
CFLAGS += -D_POSIX_C_SOURCE=200809L

INCLUDE = -I ../../include -I ../../src
INCLUDE += -include ../../include/cb_interpose.h

SUPPORT_SRCS = $(wildcard ../../support/*.c)
SRCS = main.c ../../src/state.c ../../src/cb_io.c $(SUPPORT_SRCS) {parts}

all: scenario
scenario:
	$(CC) $(CFLAGS) $(INCLUDE) $(SRCS) -o scenario

clean:
	rm -f scenario
'''

# ===================== HELPERS =====================

def copy_support_assets(juliet_root: Path):
    inc = EXPO / "include"; inc.mkdir(parents=True, exist_ok=True)
    sup = EXPO / "support"; sup.mkdir(parents=True, exist_ok=True)
    src_sup = juliet_root / "testcasesupport"
    for h in src_sup.glob("*.h"):
        shutil.copy2(h, inc / h.name)
    for c in src_sup.glob("*.c"):
        shutil.copy2(c, sup / c.name)

def resolve_source(juliet_root: Path, item: dict) -> Path:
  if "path" in item:
    p = Path(item["path"])
    return (juliet_root / p) if not p.is_absolute() else p
  stem = item["stem"]
  hits = list((juliet_root/"testcases").glob(f"**/{stem}.c"))
  if not hits: raise FileNotFoundError(stem)
  return hits[0]

def _io_flags(io_mode: str):
  return {
    "is_stdin": "1" if io_mode=="STDIN" else "0",
    "is_env":   "1" if io_mode=="ENV"   else "0",
    "is_file":  "1" if io_mode=="FILE"  else "0",
  }

def gen_item_bundle(jroot: Path, item: dict, items_dir: Path):
  src  = resolve_source(jroot, item)
  stem = src.stem
  out  = items_dir / stem
  out.mkdir(parents=True, exist_ok=True)

  # Juliet file
  shutil.copy2(src, out / "source.c")

  seg = SEG_CHOICES[item["segment"].upper()]
  act = ACT_CHOICES[item["effect"].upper()]
  rsz = str(item.get("region_size", 0))
  io_mode   = item.get("io","STDIN").upper()
  env_key   = item.get("env_key","ADD")
  file_name = item.get("file_name","input.bin")

  flags = _io_flags(io_mode)
  main_c = MAIN_SINGLE_TMPL.substitute(
      stem=stem, seg=seg, rsize=rsz, act=act,
      env_key=env_key, file_name=file_name,
      is_stdin=flags["is_stdin"], is_env=flags["is_env"], is_file=flags["is_file"]
  )
  (out / "main_single.c").write_text(main_c)

  emit_good = bool(item.get("good", False))
  adapter = ADAPTER_TMPL.substitute(stem=stem, seg=seg, rsize=rsz, act=act)
  if emit_good:
    adapter = "#define EMIT_GOOD 1\n" + adapter
  (out / "adapter.c").write_text(adapter)

  (out / "Makefile").write_text(ITEM_MK)

  meta = {
    "stem": stem,
    "cwe": int(stem.split('_',1)[0].replace('CWE','')) if stem.startswith("CWE") else None,
    "segment": item["segment"].upper(),
    "effect": item["effect"].upper(),
    "io": io_mode,
    "env_key": env_key if io_mode=="ENV" else None,
    "file_name": file_name if io_mode=="FILE" else None,
    "entrypoints": {"bad": f"{stem}_bad", "good": f"{stem}_good" if emit_good else None}
  }
  (out / "meta.yaml").write_text(yaml.safe_dump(meta, sort_keys=False))
  return stem

def copy_runtime():
  # export/src
  dst_src = EXPO / "src"; dst_src.mkdir(parents=True, exist_ok=True)
  for f in ["state.c", "state.h", "cb_io.c"]:
    shutil.copy2(SRC_DIR / f, dst_src / f)
  # export/include
  dst_inc = EXPO / "include"; dst_inc.mkdir(parents=True, exist_ok=True)
  for h in ["cb_io.h", "cb_interpose.h"]:
    shutil.copy2(INC_DIR / h, dst_inc / h)

def gen_scenario(items_dir: Path, scen_yaml: Path, scen_root: Path):
  spec  = yaml.safe_load(scen_yaml.read_text())
  name  = spec.get("name","scenario")
  steps = spec.get("steps",[])
  stems = []
  for s in steps:
    if isinstance(s, str):
      stems.append(Path(s).stem)
    else:
      stems.append(Path(s.get("path", s.get("stem"))).stem)

  d = scen_root / name
  d.mkdir(parents=True, exist_ok=True)

  decls = "\n".join([f"int chainbench_run_{s}_bad(void);" for s in stems])
  calls = "\n".join([f"  (void)chainbench_run_{s}_bad();" for s in stems])
  (d / "main.c").write_text(SCEN_MAIN_TMPL.substitute(decls=decls, calls=calls))

  parts = " ".join([f"../../items/{s}/adapter.c ../../items/{s}/source.c" for s in stems])
  (d / "Makefile").write_text(SCEN_MK.format(parts=parts))

  # convenience copies
  single = d / "single"; single.mkdir(exist_ok=True)
  for s in stems:
    dst = single / s; dst.mkdir(exist_ok=True)
    for f in ["source.c","adapter.c","main_single.c","Makefile","meta.yaml"]:
      shutil.copy2(items_dir / s / f, dst / f)

  (d / "README.md").write_text(
    f"# Scenario: {name}\n\nBuild chain:\n\n"
    "```bash\nmake -C .\n./scenario\n```\n\n"
    "Build singles:\n\n"
    "```bash\nfor d in single/*; do make -C \"$d\"; done\n```\n"
  )
  print(f"[ok] scenario → export/scenarios/{name}")

# ===================== DRIVER =====================

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--juliet-root", required=True, help="path to juliet repo root")
  ap.add_argument("--selected",    required=True, help="manifests/selected.yaml")
  ap.add_argument("--scenario",    default=None,  help="manifests/scenario.yaml (optional)")
  args = ap.parse_args()

  EXPO.mkdir(exist_ok=True)
  copy_runtime()

  jroot    = Path(args.juliet_root).resolve()
  selected = yaml.safe_load(Path(args.selected).read_text())
  items    = selected.get("items", [])
  if not items:
    raise SystemExit("[err] selected.yaml has no items")

  # Juliet testcasesupport headers/libs
  copy_support_assets(jroot)

  items_dir = EXPO / "items"; items_dir.mkdir(parents=True, exist_ok=True)
  stems = []
  for it in items:
    seg = it.get("segment","DATA").upper()
    act = it.get("effect","READ").upper()
    io  = it.get("io","STDIN").upper()
    if seg not in SEG_CHOICES: raise SystemExit(f"[err] segment '{seg}' not in {list(SEG_CHOICES)}")
    if act not in ACT_CHOICES: raise SystemExit(f"[err] effect '{act}' not in {list(ACT_CHOICES)}")
    if io  not in IO_CHOICES:  raise SystemExit(f"[err] io '{io}' not in {sorted(IO_CHOICES)}")
    it["segment"]=seg; it["effect"]=act; it["io"]=io

    stems.append(gen_item_bundle(jroot, it, items_dir))

  (EXPO / "index.json").write_text(json.dumps(
    [{"stem": s, "path": f"items/{s}"} for s in stems], indent=2))

  if args.scenario:
    scen_root = EXPO / "scenarios"; scen_root.mkdir(parents=True, exist_ok=True)
    gen_scenario(items_dir, Path(args.scenario), scen_root)

  print(f"[ok] items → export/items (count={len(stems)})")
  print("[ok] include → export/include")
  print("[ok] state   → export/src")

if __name__ == "__main__":
  main()
