# Installation

The execution core uses the Python standard library. Python 3.10 or newer on Linux,
macOS or Windows is sufficient for the demo, numerical replay and tests.

```bash
git clone https://github.com/ADEPT-ORG/FastRoverVLA.git
cd FastRoverVLA
python -m pip install --no-deps -e .
python -m fastrovervla demo --steps 24
python scripts/reproduce.py --verify
```

No PyTorch, CUDA, dataset images or checkpoint downloads are needed for these commands.
Installation uses setuptools; an offline environment also needs its build dependencies
already installed (`pip install --no-build-isolation --no-deps -e .`).

To connect an actual VLA, install that backbone's own environment separately and wrap
its decoded output in the callback shown in [integration.md](integration.md). The
interface has no trainable weights and does not ship backbone checkpoints. Tested
paper settings cover Qwen3-VL-2B, Qwen2.5-VL-3B, MiniCPM-V-2.6 and InternVL2.5-2B;
their inference environments differ. The CPU replay is independent of those environments.
