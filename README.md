# qubex-emulator

Pulse-level emulation helpers for Qubex experiments.

This package contains the local emulator implementation for Qubex: a
`FakeExperiment` with Qubex-like calibration and pulse APIs, plus qxsimulator
schedule materialization utilities.

The emulator is designed for examples, notebooks, and offline development. By
default, common calibration-style experiments use fast analytic responses that
match the shape of QUBEX results closely enough for documentation and workflow
testing. Pass `use_simulator=True` when you want to run the pulse schedule
through qxsimulator instead.

## Setup

Install the environment with uv:

```bash
uv sync
```

To install this emulator directly from GitHub with pip:

```bash
python -m pip install "qubex-emulator @ git+https://github.com/orangekame3/qubex-emulator.git"
```

If the upstream QUBEX packages are not available from your package index, install
them from GitHub with the `qubex-git` extra:

```bash
python -m pip install "qubex-emulator[qubex-git] @ git+https://github.com/orangekame3/qubex-emulator.git"
```

## Quick Start

```python
from qubex_emulator import FakeExperiment

exp = FakeExperiment()
model = exp.model()

print(model["qubits"])
```

Default calibrated pulse dictionaries are populated lazily, so QUBEX-like calls
can be used directly:

```python
repeat_result = exp.repeat_sequence(exp.hpi_pulse, repetitions=20)
pi_repeat = exp.repeat_sequence(exp.pi_pulse, repetitions=20)
```

Explicit calibration calls still update the same dictionaries:

```python
exp.calibrate_drag_hpi_pulse(plot=False)
exp.calibrate_drag_pi_pulse(plot=False)
```

## Supported Workflows

The examples under `docs/examples/experiment/` cover the main emulator surface:

- basic experiment usage
- spectroscopy and frequency calibration
- pulse calibration and repeated pulse checks
- Rabi, T1, T2 echo, and Ramsey experiments
- randomized benchmarking
- state tomography and state classification
- EF characterization
- CR calibration and chevron-style scans

Rabi, T1, T2, Ramsey, chevron, and repeat sequence plots use normalized
experiment-like signals by default rather than raw I/Q traces. For lower-level
inspection, individual sweep plots can still be shown as I/Q series with
`normalize=False`.

When re-running notebooks, clear old outputs first if plots still look like a
previous implementation.

## Development

Run the checks with:

```bash
uv run ruff check src tests
uv run pytest -q
```

The package can be imported without qxsimulator for lightweight use. Pulse-level
simulation requires the local `qubex` packages, `qutip`, `qxsimulator`, `numpy`,
and `pandas`.
