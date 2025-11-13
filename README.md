# ChainBench

Real exploits often require chains (e.g., overflow -> pointer overwrite -> hijack), while most benchmarks test single CWEs. ChainBench lets independent vulnerable units be sequenced and composed.  
Vulnerable programs are adapted from **juliet-test-suite-c**: https://github.com/arichardson/juliet-test-suite-c

**What we add (per Juliet file):**
- An adapter that feeds inputs exactly as expected (ENV / STDIN / FILE).
- The adapter publishes effects into a shared state. The shared state is deterministic “glue”, later steps can observe what earlier steps produced.

Shared state:
- Segment: `HEAP | STACK | DATA | CODE | PROTECTED`  
- Effects: `READ | WRITE | EXEC | CALL | TRIGGER`
- Addesss: `fixed | arbitrary | expandable`



## How to use
Setup
```
python3 -m venv .venv && source .venv/bin/activate
pip install pyyaml
```

Prepare Juliet
```
git clone --depth 1 https://github.com/arichardson/juliet-test-suite-c.git external/juliet-test-suite-c

```

Generate vulnerable files (apply adapters)
```
python3 tools/cbgen.py \
  --juliet-root external/juliet-test-suite-c \
  --selected manifests/selected.yaml
```

List available vulnerabilities
```
ls export/items
```

Run individual vulerabilities
```
make -C export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01

./export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01/app < inputs/num_12.txt
```

Generate a chain from scenario.yaml
```
python3 tools/cbgen.py \
  --juliet-root external/juliet-test-suite-c \
  --selected manifests/selected.yaml \
  --scenario manifests/scenario.yaml  
```

Run the chain (scenario)
```
make -C export/scenarios/demo-chain
./export/scenarios/demo-chain/scenario

```


```
chainbench/
├── external/
│   └── juliet-test-suite-c/              # your Juliet checkout
├── manifests/
│   ├── selected.yaml                     # which Juliet files to adapt
│   └── scenario.yaml                     # optional chain definition
├── export/
│   ├── include/                          # Juliet testcasesupport headers
│   ├── src/                              # shared state runtime (state.c/h)
│   ├── items/                            # one folder per selected testcase
│   │   └── <STEM>/
│   │       ├── source.c                  # copied Juliet file
│   │       ├── adapter.c                 # generated adapter (shared-state glue)
│   │       ├── main_single.c             # single-binary entry
│   │       ├── Makefile                  # builds ./app
│   │       └── meta.yaml                 # effect/segment metadata
│   ├── scenarios/
│   │   └── <NAME>/
│   │       ├── main.c                    # calls chainbench_run_<stem>_bad()
│   │       ├── Makefile                  # builds ./scenario
│   │       └── single/                   # convenience copies of item bundles
│   │           └── <STEM>/...
│   └── index.json
├── src/                                  # source of the shared state runtime
│   ├── state.h
│   └── state.c
└── tools/
    └── cbgen.py                          # generator (this pipeline)
```