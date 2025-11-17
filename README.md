# ChainBench

Real exploits often require chains (e.g., overflow -> pointer overwrite -> hijack), while most benchmarks test single CWEs. ChainBench adapts Juliet C testcases so independent vulnerable units can be sequenced and composed. 
Source testcases are from juliet-test-suite-c: https://github.com/arichardson/juliet-test-suite-c

**What we add:**
- Attacker input modeling: one clear channel per item `STDIN / ENV / FILE`. 

- Effect model: one abstract region (segment = `HEAP|STACK|DATA|CODE|PROTECTED`) and one effect (`READ|WRITE|EXEC|CALL|TRIGGER`) for each item.

- Entrypoint: `main_single.c` that loads 1) payload → 2) exposes it → 3) records region/effect → 4) calls <stem>_bad().

- Evaluation support:
    - Scenario chaining: a main that invokes multiple adapters to emulate exploit chains.
    - Ground-truth manifest: `selected_resolved.yam`l (from `infer_manifest.py`) encodes the resolved source path and configuration (segment/effect/io/entrypoints).

**Generated outputs**
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
main_single.c
  -> chainbench_run_<stem>_bad()  [adapter.c]
       -> <stem>_bad()            [source.c from Juliet]
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
python3 tools/infer_manifest.py \
  --juliet-root external/juliet-test-suite-c \
  --in manifests/selected.yaml \
  --out manifests/selected_resolved.yaml

python3 tools/cbgen.py \
  --juliet-root external/juliet-test-suite-c \
  --selected manifests/selected_resolved.yaml
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


