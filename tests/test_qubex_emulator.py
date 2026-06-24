from qubex_emulator import FakeExperiment


def test_fake_experiment_exposes_qubex_like_pulse_service() -> None:
    exp = FakeExperiment()

    assert exp.qubit_labels[:2] == ("Q00", "Q01")
    assert exp.pulse is exp
    assert exp.session_service is exp
    assert exp.measurement_service is exp
    assert exp.calibration_service is exp


def test_fake_experiment_builds_internal_model() -> None:
    model = FakeExperiment().model()

    assert model["name"] == "fake-qubex-two-qubit-system"
    assert [qubit["label"] for qubit in model["qubits"]] == ["Q00", "Q01", "Q02", "Q03"]
    assert model["couplings"][0]["control"] == 0


def test_fake_experiment_session_and_metadata_api() -> None:
    exp = FakeExperiment()

    assert not exp.is_connected()
    assert exp.connect() is exp
    assert exp.is_connected()
    assert exp.get_qubit_label(1) == "Q01"
    assert exp.get_resonator_label(0) == "RQ00"
    assert exp.get_cr_label("Q00", "Q01") == "Q00-Q01"
    assert exp.cr_pair("Q00-Q01") == ("Q00", "Q01")
    assert exp.get_spectators("Q00") == ["Q01", "Q02", "Q03"]


def test_fake_experiment_measurement_api_returns_synthetic_result() -> None:
    exp = FakeExperiment()

    result = exp.execute(targets=["Q00"], shots=16)

    assert "Q00" in result.data
    assert len(result.data["Q00"].kerneled) == 1


def test_fake_measurement_plot_matches_iq_scatter_shape() -> None:
    exp = FakeExperiment()

    result = exp.measure(targets=["Q00", "Q01"], mode="single", n_shots=16)
    figure = result.plot(return_figure=True)

    assert len(figure.data) == 2
    assert figure.layout.title.text == "I/Q plane"
    assert figure.layout.width == 500
    assert figure.layout.height == 400
    assert figure.layout.margin.l == 120
    assert figure.layout.margin.r == 120
    assert figure.layout.xaxis.title.text == "In-phase (arb. units)"
    assert figure.layout.yaxis.title.text == "Quadrature (arb. units)"
    assert figure.layout.xaxis.tickformat == ".2g"
    assert figure.layout.yaxis.scaleanchor == "x"
    assert len(figure.data[0].x) == 16
    assert figure.data[0].marker.size == 4


def test_unsupported_experiment_api_is_explicit() -> None:
    exp = FakeExperiment()

    assert hasattr(exp, "ckp_experiment")
    try:
        exp.ckp_experiment()
    except NotImplementedError as exc:
        assert "not implemented" in str(exc)
    else:
        raise AssertionError("ckp_experiment should be unsupported")


def test_obtain_rabi_params_returns_experiment_result_shape() -> None:
    exp = FakeExperiment()

    result = exp.obtain_rabi_params(
        targets=["Q00"],
        time_range=[0.0, 12.0, 24.0],
        plot=False,
    )

    assert "Q00" in result.data
    assert "Q00" in result.rabi_params
    assert result.data["Q00"].rabi_param is result.rabi_params["Q00"]
    assert result.data["Q00"].time_range.tolist() == [0.0, 12.0, 24.0]
    assert result.rabi_params["Q00"].frequency == 1.0 / (2.0 * exp.pi_duration)
    assert exp.rabi_params["Q00"] is result.rabi_params["Q00"]


def test_sweep_plot_uses_qubex_iq_series_layout() -> None:
    exp = FakeExperiment()

    result = exp.sweep_parameter(
        sequence=lambda _: {},
        sweep_range=[0.0, 0.5, 1.0],
        targets=["Q00"],
        plot=False,
    )
    figure = result.data["Q00"].plot(return_figure=True)

    assert figure.layout.title.text == "Sweep result : Q00"
    assert figure.layout.xaxis.title.text == "Sweep value"
    assert figure.layout.yaxis.title.text == "Measured signal"
    assert [trace.name for trace in figure.data] == ["I", "Q"]
