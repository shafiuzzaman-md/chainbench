# ChainBench

Real exploits often require chains (e.g., overflow -> pointer overwrite -> hijack), while most benchmarks test single CWEs. ChainBench adapts Juliet C testcases so independent vulnerable units can be sequenced and composed. 

Source testcases are from juliet-test-suite-c: https://github.com/arichardson/juliet-test-suite-c

## What ChainBench adds
- **Attacker input modeling**  
  One clear channel per item: `STDIN` / `ENV` / `FILE`.

- **Effect & region model**  
  Each item records exactly one abstract memory region and one effect:
  - Segment: `HEAP | STACK | DATA | CODE | PROTECTED`  
  - Effect:  `READ | WRITE | EXEC | CALL | TRIGGER`

- **Deterministic memory model**  
  Pin each item’s region to a fixed base and size so chains can share a global logical memory map and reason about cross-item interactions.

- **Clean entrypoint**  
  Generated `main_single.c` does:
  1) load `payload.bin` 
  2) expose via selected IO channel 
  3) create/log region+effect
  4) call `<stem>_bad()`.

- **Evaluation support**
  - Scenario chaining (`export/scenarios/<name>/scenario`) invoking multiple adapters.
  - Ground-truth `meta.yaml` for each item (segment/effect/io/entrypoints/memory settings).
  - Uniform logs: `[CB_LOG] ...` lines show region & effect decisions per run.



## Quick-start deterministic memory model
We use small, disjoint address pools so regions don’t collide accidentally. Slot size = 64 KiB (fixed). Each item gets one slot in its segment’s pool.

1) Address pools (logical)
```
DATA      base 0x40000000 (slot = 64 KiB)
HEAP      base 0x50000000 (slot = 64 KiB)
STACK     base 0x60000000 (slot = 64 KiB)
CODE      base 0x70000000 (slot = 64 KiB)
PROTECTED base 0x80000000 (slot = 64 KiB)

```
Each item gets a slot within its segment’s pool.

2) Miniature default region sizes (kept small, but fixed per family):

Defaults to keep runs small and consistent:
```
Buffer over/under-flows (121/122/124/126/127): 0x2000 (8 KiB)
Integer (190/191/194/197):                      0x1000 (4 KiB)
Leak/Double free/UAF (401/415/416):             0x2000 (8 KiB)
Command/Process control (78/114/272/273/321):   0x4000 (16 KiB)
Misc (367/369/476/481/484/526/457/467/587/562/364): 0x1000 (4 KiB)

```
- Address class is always FIXED in miniature mode.
- If two items should alias (e.g., “write-what-where -> hijack”), give them the same base slot intentionally.

3) assign fixed bases & sizes to everything
```
python3 tools/assign_memory.py \
  --in  manifests/selected_resolved.yaml \
  --out manifests/selected_resolved_mem.yaml
```
This fills each item with:
- addr_class: FIXED
- fixed_base: chosen from its segment pool (unique slot per item)
- region_size: from the miniature defaults above unless already set
- re-run assign_memory.py after you add/remove items so slots stay compact.

## Directory layout (generated)
Each selected Juliet testcase becomes a self-contained item bundle:
```
export/items/<STEM>/
├── source.c         # Juliet testcase (<stem>_bad / <stem>_good)
├── adapter.c        # shared-state glue + input seeding
├── main_single.c    # entry for single run
├── meta.yaml        # ground truth
└── Makefile        
```

Typical call flow:
```
main_single.c -> cb_region_addr(...); cb_effect_push(...); # record model + log
-> <stem>_bad(); # source.c from Juliet
```

---

## Memory model

To support **reproducible chaining**, ChainBench introduces a minimal, explicit memory model:

- **Region API:**  
  The generated code calls:

  ```c
  uint32_t cb_region_addr(enum cb_segment seg,
                          uint64_t        base,     // region base address (logical)
                          uint32_t        size,     // bytes
                          uint32_t        growth,   // 1 for now
                          enum cb_addr_class cls);  // FIXED | ARBITRARY | EXPANDABLE

### Address class:
- FIXED: region is placed at the provided base
- ARBITRARY: runtime chooses a stable but arbitrary base
- EXPANDABLE: like ARBITRARY but allows growth

### Environment overrides (per run):
- CB_ADDR_CLASS=FIXED|ARBITRARY|EXPANDABLE
- CB_FIXED_BASE=0xHEX_OR_DEC (used if class = FIXED)
- CB_REGION_SIZE=DEC_BYTES
These override whatever defaults were baked into meta.yaml/main_single.c.

### Logging:
```[CB_LOG] region rid=<id> seg=<SEG> base=0x<addr> size=<bytes> class=<CLASS> action=<ACT> off=0 len=0```
Use these to chain items by aligning regions (e.g., point an overflow item’s DATA region at the same base used by a follow-on EXEC item).

### Examples:
- Pin a single item to a known region:
```
make -C export/items/CWE190_Integer_Overflow__int_fscanf_multiply_01
CB_ADDR_CLASS=FIXED CB_FIXED_BASE=0x100000 CB_REGION_SIZE=4096 \
  ./export/items/CWE190_Integer_Overflow__int_fscanf_multiply_01/app
```

- Run with arbitrary base but fixed size:
```
CB_ADDR_CLASS=ARBITRARY CB_REGION_SIZE=8192 ./export/items/<STEM>/app
```

- Scenario with shared fixed base for all items (recommended when testing chains):
```
make -C export/scenarios/demo-chain
CB_ADDR_CLASS=FIXED CB_FIXED_BASE=0x400000 CB_REGION_SIZE=16384 \
  ./export/scenarios/demo-chain/scenario

```

## How to generate 
### Setup
```
python3 -m venv .venv && source .venv/bin/activate
pip install pyyaml
```

### Get Juliet
```
git clone --depth 1 https://github.com/arichardson/juliet-test-suite-c.git external/juliet-test-suite-c
```

### Resolve and generate
```
python3 tools/infer_manifest.py \
  --juliet-root external/juliet-test-suite-c \
  --in  manifests/selected.yaml \
  --out manifests/selected_resolved.yaml

python3 tools/cbgen.py \
  --juliet-root external/juliet-test-suite-c \
  --selected   manifests/selected_resolved.yaml

```
This writes:
- export/items/<STEM>/ (bundles)
- export/include and export/src (runtime headers/sources)
- export/index.json (index of items)

## How to test

### Independent vulnerabilities
```
# list
ls export/items

# build one
make -C export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01

# run with a payload
printf "12\n" > export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01/payload.bin

# pin memory and run (shows [CB_LOG] lines)
( cd export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01 \
  && CB_ADDR_CLASS=FIXED CB_FIXED_BASE=0x300000 CB_REGION_SIZE=4096 ./app )
```
### Run all vulnerabilities
```
chmod +x tools/run_all.py
python3 tools/run_all.py

```
### Chain (scenario)
```
python3 tools/cbgen.py \
  --juliet-root external/juliet-test-suite-c \
  --selected manifests/selected_resolved.yaml \
  --scenario manifests/scenario.yaml

make -C export/scenarios/demo-chain

# enforce a shared region across all items in the chain
CB_ADDR_CLASS=FIXED CB_FIXED_BASE=0x500000 CB_REGION_SIZE=32768 \
  ./export/scenarios/demo-chain/scenario
```

