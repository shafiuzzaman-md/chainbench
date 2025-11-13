# ChainBench

Real exploits often require chains (e.g., overflow -> pointer overwrite -> hijack), while most benchmarks test single CWEs. ChainBench adapts Juliet C testcases so independent vulnerable units can be sequenced and composed. 
Source testcases are from juliet-test-suite-c: https://github.com/arichardson/juliet-test-suite-c

**What we add (per Juliet file):**
- An adapter that feeds inputs exactly as expected (ENV / STDIN / FILE).
- The adapter records effects into a shared state. The shared state is deterministic “glue”, later steps can observe what earlier steps produced.

Shared state:
- Segment: `HEAP | STACK | DATA | CODE | PROTECTED`  
- Effects: `READ | WRITE | EXEC | CALL | TRIGGER`
- Addesss: `fixed | arbitrary | expandable`

**Generated outputs**
Each selected Juliet testcase becomes a self-contained item bundle:
```
export/items/<STEM>/
├── source.c         # Juliet testcase (<stem>_bad / <stem>_good)
├── adapter.c        # shared-state glue + input seeding
├── main_single.c    # entry for single run
├── Makefile         # builds ./app
└── meta.yaml        # effect/segment metadata
```

Typical call flow:
```
main_single.c  ->  chainbench_run_<stem>_bad()   (adapter.c) ->  <stem>_bad() (source.c, Juliet)
```
## How to generate 
Setup
```
python3 -m venv .venv && source .venv/bin/activate
pip install pyyaml
```

Get Juliet
```
git clone --depth 1 https://github.com/arichardson/juliet-test-suite-c.git external/juliet-test-suite-c
```

Generate vulnerable files (apply adapters)
```
python3 tools/cbgen.py \
  --juliet-root external/juliet-test-suite-c \
  --selected manifests/selected.yaml
```


## How to test

### Independent vulnerabilities

List available vulnerabilities
```
ls export/items
```

Build & run a single item (Example)
```
make -C export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01

# Example run 1:
./export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01/app < inputs/num_12.txt

# Example run 2:
printf "12\n" > export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01/payload.bin
./export/items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01/app

```
### Chains
Generate a chain from scenario.yaml:
```
python3 tools/cbgen.py \
  --juliet-root external/juliet-test-suite-c \
  --selected manifests/selected.yaml \
  --scenario manifests/scenario.yaml  
```

Build & run the chain:
```
make -C export/scenarios/demo-chain
./export/scenarios/demo-chain/scenario
```


