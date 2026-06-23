from qubex_emulator import FakeExperiment


def test_fake_experiment_exposes_qubex_like_pulse_service() -> None:
    exp = FakeExperiment()

    assert exp.qubit_labels == ("Q00", "Q01")
    assert exp.pulse is exp


def test_fake_experiment_builds_internal_model() -> None:
    model = FakeExperiment().model()

    assert model["name"] == "fake-qubex-two-qubit-system"
    assert [qubit["label"] for qubit in model["qubits"]] == ["Q00", "Q01"]
    assert model["couplings"][0]["control"] == 0
