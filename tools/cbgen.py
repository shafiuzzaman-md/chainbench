#!/usr/bin/env python3
import argparse, yaml, shutil, json
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "src"
EXPO = ROOT / "export"

SEG_CHOICES = {
  "HEAP":"SEG_HEAP","STACK":"SEG_STACK","DATA":"SEG_DATA",
  "CODE":"SEG_CODE","PROTECTED":"SEG_PROTECTED"
}
ACT_CHOICES = {
  "READ":"ACT_READ","WRITE":"ACT_WRITE","EXEC":"ACT_EXEC",
  "CALL":"ACT_CALL","TRIGGER":"ACT_TRIGGER"
}

ADAPTER_TMPL = Template(r'''/* auto-generated adapter for ${stem} */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if defined(_WIN32)
  #include <io.h>
  #define dup2 _dup2
  #define fileno _fileno
#else
  #include <unistd.h>
#endif
#include "state.h"

/* Juliet entrypoints (from source.c) */
int ${stem}_bad(void);
#ifdef EMIT_GOOD
int ${stem}_good(void);
#endif

/* If payload.bin exists next to the app, mirror it to stdin and CB.plane */
static void cb_seed_stdin_from_payload(void){
  FILE* f = fopen("payload.bin","rb");
  if(!f) return;
  FILE* tmp = tmpfile();
  if(!tmp){ fclose(f); return; }

  unsigned char buf[4096]; size_t n;
  while((n=fread(buf,1,sizeof(buf),f))>0){ fwrite(buf,1,n,tmp); }
  fflush(tmp); fseek(tmp,0,SEEK_SET);
  dup2(fileno(tmp), fileno(stdin));

  fseek(tmp,0,SEEK_END); long L = ftell(tmp);
  fseek(tmp,0,SEEK_SET);
  if (L > 0) {
    if ((size_t)L > sizeof(CB.plane)) L = (long)sizeof(CB.plane);
    fread(CB.plane,1,(size_t)L,tmp);
    CB.plane_len = (unsigned)L;
  }
  fclose(f);
}

/* Run wrappers: create a region and log an abstract effect */
int chainbench_run_${stem}_bad(void){
  cb_reset();
  cb_seed_stdin_from_payload();
  uint32_t rid = cb_region_new($seg, $rsize, 1);
  cb_effect_push(rid, 0, 0, $act);
  (void)${stem}_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_${stem}_good(void){
  cb_reset();
  cb_seed_stdin_from_payload();
  uint32_t rid = cb_region_new($seg, $rsize, 1);
  cb_effect_push(rid, 0, 0, $act);
  (void)${stem}_good();
  return 0;
}
#endif
''')

MAIN_SINGLE_TMPL = Template(r'''#include <stdio.h>
#include "state.h"
int chainbench_run_${stem}_bad(void);
int main(void){
  (void)chainbench_run_${stem}_bad();
  printf("[CB] single_done effects=%u regions=%u payload_len=%u\n",
         CB.effect_count, CB.region_count, CB.plane_len);
  return 0;
}
''')

ITEM_MK = r'''CC ?= cc
CFLAGS ?= -O2 -g -std=c11 -Wall -Wextra
# POSIX prototypes for fileno(), etc.
CFLAGS += -D_POSIX_C_SOURCE=200809L

INCLUDE = -I ../../include -I ../../src
INCLUDE += -include ../../include/cb_interpose.h

SUPPORT_SRCS = $(wildcard ../../support/*.c)
SRCS = main_single.c source.c ../../src/state.c ../../src/cb_io.c adapter.c $(SUPPORT_SRCS)


all: app

app: $(SRCS)
	$(CC) $(CFLAGS) $(INCLUDE) $(SRCS) -o $@

clean:
	rm -f app
'''



SCEN_MAIN_TMPL = r'''#include <stdio.h>
#include "state.h"
{decls}
int main(void){
  cb_reset();
{calls}
  printf("[CB] scenario_done effects=%u regions=%u payload_len=%u\n",
         CB.effect_count, CB.region_count, CB.plane_len);
  return 0;
}
'''

SCEN_MK = r'''CC ?= cc
CFLAGS ?= -O2 -g -std=c11 -Wall -Wextra
INCLUDE = -I ../../src -I ../../include
SRCS = main.c ../../src/state.c {parts}
all: scenario
	$(CC) $(CFLAGS) $(INCLUDE) $(SRCS) -o scenario
clean:
	rm -f scenario
'''
def copy_support_assets(juliet_root: Path):
    """Copy all available Juliet testcasesupport headers and C files."""
    inc = EXPO / "include"; inc.mkdir(parents=True, exist_ok=True)
    sup = EXPO / "support"; sup.mkdir(parents=True, exist_ok=True)
    src_sup = juliet_root / "testcasesupport"

    # headers
    for h in src_sup.glob("*.h"):
        shutil.copy2(h, inc / h.name)

    # C sources (some repos don't have std_testcase.c; that's OK)
    c_files = list(src_sup.glob("*.c"))
    if not c_files:
        print("[warn] no .c files found under testcasesupport; "
              "ensure std_testcase_io.c exists in your Juliet checkout.")
    for c in c_files:
        shutil.copy2(c, sup / c.name)


def resolve_source(juliet_root: Path, item: dict) -> Path:
  if "path" in item:
    p = Path(item["path"])
    return (juliet_root / p) if not p.is_absolute() else p
  stem = item["stem"]
  hits = list((juliet_root/"testcases").glob(f"**/{stem}.c"))
  if not hits: raise FileNotFoundError(stem)
  return hits[0]

def gen_item_bundle(jroot: Path, item: dict, items_dir: Path):
  src = resolve_source(jroot, item)
  stem = src.stem
  out = items_dir / stem
  out.mkdir(parents=True, exist_ok=True)

  # 1) source.c (verbatim Juliet)
  shutil.copy2(src, out / "source.c")

  # 2) adapter.c
  seg = SEG_CHOICES[item["segment"].upper()]
  act = ACT_CHOICES[item["effect"].upper()]
  rsize = str(item.get("region_size", 0))
  emit_good = bool(item.get("good", False))
  adapter = ADAPTER_TMPL.substitute(stem=stem, seg=seg, act=act, rsize=rsize)
  if emit_good:
    adapter = "#define EMIT_GOOD 1\n" + adapter
  (out / "adapter.c").write_text(adapter)

  # 3) main_single.c + Makefile
  (out / "main_single.c").write_text(MAIN_SINGLE_TMPL.substitute(stem=stem))
  (out / "Makefile").write_text(ITEM_MK)

  # 4) metadata
  meta = {
    "stem": stem,
    "cwe": int(stem.split('_',1)[0].replace('CWE','')) if stem.startswith("CWE") else None,
    "segment": item["segment"].upper(),
    "effect": item["effect"].upper(),
    "entrypoints": {"bad": f"{stem}_bad", "good": f"{stem}_good" if emit_good else None}
  }
  (out / "meta.yaml").write_text(yaml.safe_dump(meta, sort_keys=False))

  return stem

def gen_state_copy():
  dst_src = EXPO / "src"; dst_src.mkdir(parents=True, exist_ok=True)
  shutil.copy2(SRC / "state.h", dst_src / "state.h")
  shutil.copy2(SRC / "state.c", dst_src / "state.c")

def copy_runtime(EXPORT: Path, ROOT: Path):
    """Copy ChainBench runtime into export/ so item Makefiles can reference ../../src and ../../include."""
    dst_src = EXPORT / "src"
    dst_inc = EXPORT / "include"
    dst_src.mkdir(parents=True, exist_ok=True)
    dst_inc.mkdir(parents=True, exist_ok=True)

    # runtime .c/.h
    for f in ["state.c", "state.h", "cb_io.c"]:
        shutil.copy2((ROOT / "src" / f), dst_src / f)

    # project headers used by items
    for h in ["cb_io.h", "cb_interpose.h"]:
        shutil.copy2((ROOT / "include" / h), dst_inc / h)

def gen_scenario(items_dir: Path, scen_yaml: Path, scen_root: Path):
  spec = yaml.safe_load(scen_yaml.read_text())
  name = spec.get("name","scenario")
  steps = spec.get("steps",[])
  stems = []
  for s in steps:
    if isinstance(s, str):
      stems.append(Path(s).stem)
    else:
      stems.append(Path(s.get("path", s.get("stem"))).stem)

  d = scen_root / name
  d.mkdir(parents=True, exist_ok=True)

  # compose main + Makefile
  decls = "\n".join([f"int chainbench_run_{s}_bad(void);" for s in stems])
  calls = "\n".join([f"  (void)chainbench_run_{s}_bad();" for s in stems])
  (d / "main.c").write_text(SCEN_MAIN_TMPL.format(decls=decls, calls=calls))
  parts = " ".join([f"../items/{s}/source.c ../items/{s}/adapter.c" for s in stems])
  (d / "Makefile").write_text(SCEN_MK.format(parts=parts))

  # convenience: copy each item as a single-project under scenarios/<name>/single/<stem>
  single = d / "single"; single.mkdir(exist_ok=True)
  for s in stems:
    dst = single / s; dst.mkdir(exist_ok=True)
    for f in ["source.c","adapter.c","main_single.c","Makefile","meta.yaml"]:
      shutil.copy2(items_dir / s / f, dst / f)

  # README
  (d / "README.md").write_text(
    f"# Scenario: {name}\n\nBuild chain:\n\n"
    "```bash\nmake -C .\n./scenario\n```\n\n"
    "Build singles:\n\n"
    "```bash\nfor d in single/*; do make -C \"$d\"; done\n```\n"
  )
  print(f"[ok] scenario → export/scenarios/{name}")

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--juliet-root", required=True, help="path to juliet repo root")
  ap.add_argument("--selected", required=True, help="manifests/selected.yaml")
  ap.add_argument("--scenario", default=None, help="manifests/scenario.yaml (optional)")
  args = ap.parse_args()
  
  copy_runtime(EXPO, ROOT)
  jroot = Path(args.juliet_root).resolve()
  selected = yaml.safe_load(Path(args.selected).read_text())
  items = selected.get("items", [])
  if not items:
    raise SystemExit("[err] selected.yaml has no items")

  # export/include headers once
  EXPO.mkdir(exist_ok=True)
  copy_support_assets(jroot)
  gen_state_copy()

  items_dir = EXPO / "items"; items_dir.mkdir(parents=True, exist_ok=True)
  stems = []
  for it in items:
    # sanity checks
    seg = it.get("segment","DATA").upper()
    act = it.get("effect","READ").upper()
    if seg not in SEG_CHOICES: raise SystemExit(f"[err] segment '{seg}' not in {list(SEG_CHOICES)}")
    if act not in ACT_CHOICES: raise SystemExit(f"[err] effect '{act}' not in {list(ACT_CHOICES)}")
    it["segment"] = seg; it["effect"] = act

    stem = gen_item_bundle(jroot, it, items_dir)
    stems.append(stem)

  # write export/index.json
  idx = [{"stem": s, "path": f"items/{s}"} for s in stems]
  (EXPO / "index.json").write_text(json.dumps(idx, indent=2))

  # optional scenario
  if args.scenario:
    scen_root = EXPO / "scenarios"
    scen_root.mkdir(parents=True, exist_ok=True)
    gen_scenario(items_dir, Path(args.scenario), scen_root)

  print(f"[ok] items → export/items (count={len(stems)})")
  print("[ok] include → export/include")
  print("[ok] state   → export/src")

if __name__ == "__main__":
  main()
