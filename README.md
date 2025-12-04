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
  You can pin each item’s region to a **fixed base address and size** so that chains can share a single global “map” of abstract memory and reason about cross-item interactions.

- **Clean entrypoint**  
  Generated `main_single.c` does:
  1) load `payload.bin` → 2) expose via requested IO channel → 3) create/log region+effect → 4) call `<stem>_bad()`.

- **Evaluation support**
  - Scenario chaining (`export/scenarios/<name>/scenario`) invoking multiple adapters.
  - Ground-truth `meta.yaml` for each item (segment/effect/io/entrypoints/memory settings).
  - Uniform logs: `[CB_LOG] ...` lines show region & effect decisions per run.


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
[CB_LOG] region rid=<id> seg=<SEG> base=0x<addr> size=<bytes> class=<CLASS> action=<ACT> off=0 len=0
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
CB_ADDR_CLASS=FIXED CB_FIXED_BASE=0x300000 CB_REGION_SIZE=4096 \
  ./export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01/app
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

