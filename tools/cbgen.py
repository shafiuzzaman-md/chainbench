#!/usr/bin/env python3
# tools/cbgen.py
import argparse, yaml, shutil, json
from pathlib import Path
from string import Template

ROOT    = Path(__file__).resolve().parents[1]
EXPO    = ROOT / "export"
SRC_DIR = ROOT / "src"
INC_DIR = ROOT / "include"

# Symbol names used from runtime
REGION_FN_ADDR = "cb_region_addr"   # API with base+addr_class
REGION_FN_SHIM = "cb_region"        # legacy wrapper (not used by default)

SEG_CHOICES = {
  "HEAP":"SEG_HEAP","STACK":"SEG_STACK","DATA":"SEG_DATA",
  "CODE":"SEG_CODE","PROTECTED":"SEG_PROTECTED"
}
ACT_CHOICES = {
  "READ":"ACT_READ","WRITE":"ACT_WRITE","EXEC":"ACT_EXEC",
  "CALL":"ACT_CALL","TRIGGER":"ACT_TRIGGER"
}
ADDR_CHOICES = {
  "FIXED":"ADDR_FIXED","ARBITRARY":"ADDR_ARBITRARY","EXPANDABLE":"ADDR_EXPANDABLE"
}
IO_CHOICES  = {"STDIN","ENV","FILE"}

MAIN_SINGLE_TMPL = Template(r'''/* main_single.c for ${stem}
 *
 * Minimal memory model for chaining:
 *   region = ${seg_str}, base=${base_str}, size=${rsize}B, class=${addr_str}, growth=1
 *   effect = ${act_str}
 * Values can be overridden at runtime via env:
 *   CB_ADDR_CLASS   = FIXED|ARBITRARY|EXPANDABLE
 *   CB_FIXED_BASE   = 0xHEX or DEC (only used if class=FIXED)
 *   CB_REGION_SIZE  = DEC bytes
 *
 * See logs: [CB_LOG] ...
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include "state.h"

/* Juliet entrypoint (provided by source.c) */
int ${stem}_bad(void);

/* ---------------- payload helpers ---------------- */
static long read_payload_file(unsigned char* buf, size_t cap){
  FILE* f = fopen("payload.bin","rb");
  if (!f) return -1;
  size_t n = fread(buf,1,cap ? cap-1 : 0,f);
  fclose(f);
  if (cap) buf[n] = '\0';
  return (long)n;
}

static int load_payload_into_plane(void){
  memset(CB.plane, 0, sizeof(CB.plane));
  CB.plane_len = 0;
  long n = read_payload_file(CB.plane, sizeof(CB.plane));
  if (n < 0) return 0;
  CB.plane_len = (unsigned)n;
  return 1;
}

static void expose_stdin(void){
  FILE* tmp = tmpfile(); if(!tmp) return;
  if (CB.plane_len) fwrite(CB.plane, 1, CB.plane_len, tmp);
  fflush(tmp); fseek(tmp, 0, SEEK_SET);
  dup2(fileno(tmp), fileno(stdin));
}
static void expose_env(void){
  if (CB.plane_len == 0) { CB.plane[0] = '\0'; CB.plane_len = 1; }
  else CB.plane[CB.plane_len-1] = '\0';
  setenv("${env_key}", (const char*)CB.plane, 1);
}
static void expose_file(void){
  FILE* f = fopen("${file_name}", "wb"); if (!f) return;
  if (CB.plane_len) fwrite(CB.plane, 1, CB.plane_len, f);
  fclose(f);
}

/* -------- configuration overrides (env) ---------- */
static unsigned long long parse_u64(const char* s){
  if (!s || !*s) return 0ull;
  if (!strncmp(s,"0x",2) || !strncmp(s,"0X",2)) return strtoull(s, NULL, 16);
  return strtoull(s, NULL, 10);
}
static enum cb_addr_class parse_addr_class(const char* s, enum cb_addr_class dflt){
  if (!s) return dflt;
  if (!strcmp(s,"FIXED")) return ADDR_FIXED;
  if (!strcmp(s,"ARBITRARY")) return ADDR_ARBITRARY;
  if (!strcmp(s,"EXPANDABLE")) return ADDR_EXPANDABLE;
  return dflt;
}

static const char* addr_class_str(enum cb_addr_class c){
  switch(c){
    case ADDR_FIXED: return "FIXED";
    case ADDR_ARBITRARY: return "ARBITRARY";
    case ADDR_EXPANDABLE: return "EXPANDABLE";
    default: return "UNKNOWN";
  }
}

/* --------- pretty logs ---------- */
static void cb_log_header(void){
  printf("[CB_LOG] stem=%s io=%s payload_len=%u\n", "${stem}", "${io_str}", CB.plane_len);
}
static void cb_log_effect(unsigned rid, unsigned long long base, unsigned size, enum cb_addr_class cls){
  printf("[CB_LOG] region rid=%u seg=%s base=0x%llx size=%u class=%s action=%s off=%u len=%u\n",
         rid, "${seg_str}", (unsigned long long)base, (unsigned)size,
         addr_class_str(cls), "${act_str}", 0u, 0u);
}

/* ----------------- main ----------------- */
int main(void){
  cb_reset();
  int have_payload = load_payload_into_plane();
  cb_log_header();

#if ${is_stdin}
  if (!have_payload) {
    fprintf(stderr, "[CB] ERROR: STDIN mode requires payload.bin next to the app.\n");
    return 2;
  }
  expose_stdin();
#endif
#if ${is_env}
  if (!have_payload) { CB.plane[0] = '\0'; CB.plane_len = 1; }
  expose_env();
#endif
#if ${is_file}
  if (!have_payload) { CB.plane_len = 0; }
  expose_file();
#endif

  /* region/effect with overrides */
  unsigned long long base   = ${fixed_base};
  unsigned            rsize = ${rsize};
  enum cb_addr_class  cls   = ${addr_class};

  const char* e_cls  = getenv("CB_ADDR_CLASS");
  const char* e_base = getenv("CB_FIXED_BASE");
  const char* e_rsz  = getenv("CB_REGION_SIZE");
  if (e_cls)  cls   = parse_addr_class(e_cls, cls);
  if (e_base) base  = parse_u64(e_base);
  if (e_rsz)  rsize = (unsigned)parse_u64(e_rsz);

  uint32_t rid = ${region_fn}( ${seg}, base, rsize, 1, cls );
  cb_effect_push(rid, 0, 0, ${act});
  cb_log_effect(rid, base, rsize, cls);

  (void)${stem}_bad();

  printf("[CB] single_done effects=%u regions=%u payload_len=%u\n",
         CB.effect_count, CB.region_count, CB.plane_len);
  return 0;
}
''')

ADAPTER_TMPL = Template(r'''/* adapter.c for ${stem} */
#include <stdio.h>
#include <stdlib.h>
#include "state.h"

int ${stem}_bad(void);
#ifdef EMIT_GOOD
int ${stem}_good(void);
#endif

static const char* addr_class_str(enum cb_addr_class c){
  switch(c){
    case ADDR_FIXED: return "FIXED";
    case ADDR_ARBITRARY: return "ARBITRARY";
    case ADDR_EXPANDABLE: return "EXPANDABLE";
    default: return "UNKNOWN";
  }
}

int chainbench_run_${stem}_bad(void){
  uint64_t base = ${fixed_base};
  uint32_t rsz  = ${rsize};
  enum cb_addr_class cls = ${addr_class};
  uint32_t rid = ${region_fn}( ${seg}, base, rsz, 1, cls );
  cb_effect_push(rid, 0, 0, ${act});
  printf("[CB_LOG] region rid=%u seg=%s base=0x%llx size=%u class=%s action=%s off=%u len=%u\n",
         rid, "${seg_str}", (unsigned long long)base, (unsigned)rsz,
         addr_class_str(cls), "${act_str}", 0u, 0u);
  (void)${stem}_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_${stem}_good(void){
  uint64_t base = ${fixed_base};
  uint32_t rsz  = ${rsize};
  enum cb_addr_class cls = ${addr_class};
  uint32_t rid = ${region_fn}( ${seg}, base, rsz, 1, cls );
  cb_effect_push(rid, 0, 0, ${act});
  printf("[CB_LOG] region rid=%u seg=%s base=0x%llx size=%u class=%s action=%s off=%u len=%u\n",
         rid, "${seg_str}", (unsigned long long)base, (unsigned)rsz,
         addr_class_str(cls), "${act_str}", 0u, 0u);
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

  shutil.copy2(src, out / "source.c")

  seg_sym = SEG_CHOICES[item["segment"].upper()]
  act_sym = ACT_CHOICES[item["effect"].upper()]
  addr_sym= ADDR_CHOICES[item.get("addr_class","ARBITRARY").upper()]
  rsz     = str(item.get("region_size", 0))
  base    = item.get("fixed_base", 0)
  base_s  = hex(base) if isinstance(base, int) else str(base)

  io_mode   = item.get("io","STDIN").upper()
  env_key   = item.get("env_key","ADD")
  file_name = item.get("file_name","input.bin")
  flags = _io_flags(io_mode)

  main_c = MAIN_SINGLE_TMPL.substitute(
      stem=stem,
      seg=seg_sym, rsize=rsz, act=act_sym,
      addr_class=addr_sym, fixed_base=base if isinstance(base,int) else 0,
      base_str=base_s, seg_str=item["segment"].upper(),
      act_str=item["effect"].upper(), addr_str=item.get("addr_class","ARBITRARY").upper(),
      env_key=env_key, file_name=file_name,
      is_stdin=flags["is_stdin"], is_env=flags["is_env"], is_file=flags["is_file"],
      io_str=io_mode, region_fn=REGION_FN_ADDR
  )
  (out / "main_single.c").write_text(main_c)

  adapter = ADAPTER_TMPL.substitute(
      stem=stem,
      seg=seg_sym, rsize=rsz, act=act_sym,
      seg_str=item["segment"].upper(), act_str=item["effect"].upper(),
      addr_class=addr_sym, fixed_base=base if isinstance(base,int) else 0,
      region_fn=REGION_FN_ADDR
  )
  (out / "adapter.c").write_text(adapter)

  (out / "Makefile").write_text(ITEM_MK)

  meta = {
    "stem": stem,
    "cwe": int(stem.split('_',1)[0].replace('CWE','')) if stem.startswith("CWE") else None,
    "segment": item["segment"].upper(),
    "effect": item["effect"].upper(),
    "io": io_mode,
    "addr_class": item.get("addr_class","ARBITRARY").upper(),
    "fixed_base": base if isinstance(base,int) else None,
    "region_size": int(rsz),
    "env_key": env_key if io_mode=="ENV" else None,
    "file_name": file_name if io_mode=="FILE" else None,
    "entrypoints": {"bad": f"{stem}_bad"}
  }
  (out / "meta.yaml").write_text(yaml.safe_dump(meta, sort_keys=False))
  return stem

def copy_runtime():
  dst_src = EXPO / "src"; dst_src.mkdir(parents=True, exist_ok=True)
  for f in ["state.c", "state.h", "cb_io.c"]:
    shutil.copy2(SRC_DIR / f, dst_src / f)
  dst_inc = EXPO / "include"; dst_inc.mkdir(parents=True, exist_ok=True)
  for h in ["cb_io.h", "cb_interpose.h"]:
    shutil.copy2(INC_DIR / h, dst_inc / h)

def gen_scenario(items_dir: Path, scen_yaml: Path, scen_root: Path):
  spec  = yaml.safe_load(scen_yaml.read_text())
  name  = spec.get("name","scenario"); steps = spec.get("steps",[])
  stems = []
  for s in steps:
    stems.append(Path(s if isinstance(s,str) else s.get("path", s.get("stem"))).stem)

  d = scen_root / name
  d.mkdir(parents=True, exist_ok=True)
  decls = "\n".join([f"int chainbench_run_{s}_bad(void);" for s in stems])
  calls = "\n".join([f"  (void)chainbench_run_{s}_bad();" for s in stems])
  (d / "main.c").write_text(SCEN_MAIN_TMPL.substitute(decls=decls, calls=calls))
  parts = " ".join([f"../../items/{s}/adapter.c ../../items/{s}/source.c" for s in stems])
  (d / "Makefile").write_text(SCEN_MK.format(parts=parts))

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

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--juliet-root", required=True)
  ap.add_argument("--selected",    required=True)
  ap.add_argument("--scenario",    default=None)
  args = ap.parse_args()

  EXPO.mkdir(exist_ok=True)
  copy_runtime()

  jroot    = Path(args.juliet_root).resolve()
  selected = yaml.safe_load(Path(args.selected).read_text())
  items    = selected.get("items", [])
  if not items: raise SystemExit("[err] selected.yaml has no items")

  copy_support_assets(jroot)

  items_dir = EXPO / "items"; items_dir.mkdir(parents=True, exist_ok=True)
  stems = []
  for it in items:
    seg = it.get("segment","DATA").upper()
    act = it.get("effect","READ").upper()
    io  = it.get("io","STDIN").upper()
    addr= it.get("addr_class","ARBITRARY").upper()
    if seg not in SEG_CHOICES:   raise SystemExit(f"[err] segment '{seg}' not in {list(SEG_CHOICES)}")
    if act not in ACT_CHOICES:   raise SystemExit(f"[err] effect '{act}' not in {list(ACT_CHOICES)}")
    if io  not in IO_CHOICES:    raise SystemExit(f"[err] io '{io}' not in {sorted(IO_CHOICES)}")
    if addr not in ADDR_CHOICES: raise SystemExit(f"[err] addr_class '{addr}' not in {list(ADDR_CHOICES)}")
    it["segment"]=seg; it["effect"]=act; it["io"]=io; it["addr_class"]=addr
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
