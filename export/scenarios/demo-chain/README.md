# Scenario: demo-chain

Build chain:

```bash
make -C .
./scenario
```

Build singles:

```bash
for d in single/*; do make -C "$d"; done
```
