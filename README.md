# qubex-emulator

Pulse-level emulation helpers for Qubex experiments.

This package contains the local emulator implementation for Qubex: a
`FakeExperiment` with Qubex-like calibration and pulse APIs, plus qxsimulator
schedule materialization utilities.

## Quick Start

```python
from qubex_emulator import FakeExperiment

exp = FakeExperiment()
model = exp.model()

print(model["qubits"])
```

The package can be imported without qxsimulator. Methods that run calibration
or pulse simulation require `qubex`, `qutip`, `qxsimulator`, `numpy`, and
`pandas`.
