# ChainBench

Real exploits often require **chains** (e.g., overflow -> pointer overwrite -> hijack), while most benchmarks test single CWEs. ChainBench lets independent vulnerable units be sequenced and composed.  
Vulnerable programs are adapted from **juliet-test-suite-c**: https://github.com/arichardson/juliet-test-suite-c

**What we add (per Juliet file):**
- An adapter that feeds inputs exactly as expected (ENV / STDIN / FILE).
- The adapter publishes effects into a shared state. The shared state is deterministic “glue”, later steps can observe what earlier steps produced.

Shared state:
- Regions:
  - `region_id` (opaque handle)  
  - `segment`: `HEAP | STACK | DATA | CODE | PROTECTED`  
  - `alive`: `1/0` (lifetime; supports leak/free/UAF reasoning)
- Effects: what the step did to a region  
  - `(region_id, offset, size, action=READ/WRITE/EXEC/CALL)`
- Addesss: fixed, arbitary, expandable

