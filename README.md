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

**Generated vulnerabilities**
export/items/
Program under analysis = the entire single-item bundle:

main_single.c (entry → calls chainbench_run_<stem}_bad)

adapter.c (seeds input/payload, records the effect, then calls Juliet)

source.c (the Juliet testcase with <stem>_bad() / <stem>_good())

../../src/state.c (shared-state runtime)
Control flow:
```
main_single.c → chainbench_run_<stem>_bad()  (adapter.c)
               → <stem>_bad()                (source.c, Juliet)

```


## How to generate vulerable files
Setup
```
sudo apt install python3.12-venv
python3 -m venv .venv && source .venv/bin/activate
pip install pyyaml
```

Juliet checkout
```
git clone --depth 1 https://github.com/arichardson/juliet-test-suite-c.git external/juliet-test-suite-c

```

Generate vulnerable files (apply adapters)
```
python3 tools/cbgen.py \
  --juliet-root external/juliet-test-suite-c \
  --selected manifests/selected.yaml
```


## Test the vulnerbaility and chain

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


