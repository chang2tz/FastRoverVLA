# Contributing

Please include the execution mode, dataset configuration, Python version and a minimal
reproduction with bug reports. Small fixes and new explicit planner adapters are welcome.
Keep backbone dependencies optional and avoid changing frozen paper configurations.

Before opening a pull request:

```bash
python -m unittest discover -s tests -v
python scripts/reproduce.py --verify
python scripts/check_site.py
```

Changes to action ordering, K+1 budget semantics, normalization precision or integration
must explain their effect on the archived trajectory parity check.
