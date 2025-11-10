# ChainBench
Real exploits often require chains (e.g., overflow -> pointer overwrite -> hijack). Benchmarks mostly test single CWEs. This dataset is designed in a way so that independent vulnerable units can be sequenced and composed into chains so tooling (static analysis, symbolic execution, fuzzing, LLM agents) can practice chain synthesis. The vulnerable programs are adapted from **juliet-test-suite-c**: https://github.com/arichardson/juliet-test-suite-c.

This dataset adds a tiny adapter per program that:

- Feeds inputs exactly as the program expects (ENV / STDIN / FILE).
- Publishes artifacts (bytes, tags) to a global state.

The global state is a deterministic “glue” that lets a later program observe what an earlier one produced enabling chains without entangling the programs.

