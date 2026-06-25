import numpy as np

from qubex_emulator import FakeExperiment
import qubex_emulator.simulation as simulation_module


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


def test_sweep_plot_defaults_to_normalized_signal() -> None:
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
    assert figure.layout.yaxis.title.text == "Normalized signal"
    assert len(figure.data) == 1


def test_sweep_plot_can_show_iq_series() -> None:
    exp = FakeExperiment()

    result = exp.sweep_parameter(
        sequence=lambda _: {},
        sweep_range=[0.0, 0.5, 1.0],
        targets=["Q00"],
        plot=False,
    )
    figure = result.data["Q00"].plot(return_figure=True, normalize=False)

    assert figure.layout.yaxis.title.text == "Measured signal"
    assert [trace.name for trace in figure.data] == ["I", "Q"]


def test_sweep_plot_can_show_normalized_signal() -> None:
    exp = FakeExperiment()

    result = exp.sweep_parameter(
        sequence=lambda _: {},
        sweep_range=[0.0, 0.5, 1.0],
        targets=["Q00"],
        plot=False,
    )
    figure = result.data["Q00"].plot(return_figure=True, normalize=True)

    assert len(figure.data) == 1
    assert figure.layout.yaxis.title.text == "Normalized signal"
    assert figure.layout.yaxis.range == (-1.2, 1.2)


def test_sweep_result_plot_defaults_to_normalized_signal(monkeypatch) -> None:
    figures = []

    def fake_show(figure, **kwargs):
        figures.append(figure)

    monkeypatch.setattr(simulation_module, "_show_figure", fake_show)
    exp = FakeExperiment()

    result = exp.sweep_parameter(
        sequence=lambda _: {},
        sweep_range=[0.0, 0.5, 1.0],
        targets=["Q00"],
        plot=False,
    )
    result.plot()

    assert len(figures) == 1
    assert figures[0].layout.yaxis.title.text == "Normalized signal"
    assert len(figures[0].data) == 1


def test_rabi_plot_defaults_to_normalized_signal() -> None:
    exp = FakeExperiment()

    result = exp.rabi_experiment(
        targets=["Q00"],
        time_range=[0.0, 12.0, 24.0],
        plot=False,
    )
    figure = result.data["Q00"].plot(return_figure=True)

    assert len(figure.data) == 1
    assert figure.layout.title.text == "Rabi oscillation : Q00"
    assert figure.layout.xaxis.title.text == "Drive duration (ns)"
    assert figure.layout.yaxis.title.text == "Normalized signal"
    assert figure.layout.yaxis.range == (-1.2, 1.2)


def test_sweep_parameter_does_not_simulate_by_default() -> None:
    from qxpulse import PulseSchedule, Rect

    exp = FakeExperiment(qubit_labels=["Q00"])

    def fail_if_simulated(*args, **kwargs):
        raise AssertionError("sweep_parameter should not simulate by default")

    exp._simulate_measure_result = fail_if_simulated

    def sequence(duration):
        with PulseSchedule(["Q00"]) as schedule:
            schedule.set_frequency("Q00", exp.qubit_frequencies[0])
            schedule.add("Q00", Rect(duration=float(duration), amplitude=1.0))
        return schedule

    result = exp.sweep_parameter(
        sequence=sequence,
        sweep_range=[0.0, 24.0],
        plot=False,
    )

    assert result.data["Q00"].sweep_range.tolist() == [0.0, 24.0]


def test_chevron_pattern_returns_qubex_like_payload() -> None:
    exp = FakeExperiment()

    result = exp.chevron_pattern(
        targets=["Q00"],
        detuning_range=[-0.01, 0.0, 0.01],
        time_range=[0.0, 24.0, 48.0],
        plot=False,
    )

    assert result.data["time_range"].tolist() == [0.0, 24.0, 48.0]
    assert result.data["detuning_range"].tolist() == [-0.01, 0.0, 0.01]
    assert result.data["chevron_data"]["Q00"].shape == (3, 3)
    assert result.data["rabi_rates"]["Q00"].shape == (3,)
    assert result.data["resonant_frequencies"]["Q00"] in {
        exp.qubit_frequencies[0] - 0.01,
        exp.qubit_frequencies[0],
        exp.qubit_frequencies[0] + 0.01,
    }
    assert "Q00" in result.figures
    assert result.figures["Q00"].layout.title.text == "Chevron pattern : Q00"


def test_chevron_pattern_uses_simulated_sweep_values() -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])
    records: list[tuple[float, float]] = []

    def fake_simulator(schedule, **kwargs):
        frequency = float(schedule.get_frequency("Q00"))
        duration = float(schedule.duration)
        records.append((frequency, duration))
        result = exp._fake_measure_result(kwargs["targets"], shots=kwargs["shots"])
        phase = 2.0 * np.pi * (frequency - exp.qubit_frequencies[0]) * duration
        center = exp._population_to_iq(0.5 * (1.0 - np.cos(phase)))
        result.data["Q00"].kerneled = [center]
        result.data["Q00"].data[0].data = [center]
        return result

    exp._simulate_measure_result = fake_simulator

    result = exp.chevron_pattern(
        targets=["Q00"],
        detuning_range=[-0.01, 0.01],
        time_range=[0.0, 24.0],
        plot=False,
        use_simulator=True,
    )

    assert records == [
        (exp.qubit_frequencies[0] - 0.01, 0.0),
        (exp.qubit_frequencies[0] - 0.01, 24.0),
        (exp.qubit_frequencies[0] + 0.01, 0.0),
        (exp.qubit_frequencies[0] + 0.01, 24.0),
    ]
    assert result.data["chevron_data"]["Q00"].shape == (2, 2)
    assert result.data["chevron_data"]["Q00"][1, 0] != result.data["chevron_data"]["Q00"][0, 0]


def test_chevron_pattern_does_not_simulate_by_default() -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])

    def fail_if_simulated(*args, **kwargs):
        raise AssertionError("chevron_pattern should not simulate by default")

    exp._simulate_measure_result = fail_if_simulated

    result = exp.chevron_pattern(
        targets=["Q00"],
        detuning_range=[0.0],
        time_range=[0.0, 24.0],
        plot=False,
    )

    assert result.data["chevron_data"]["Q00"].shape == (2, 1)


def test_chevron_pattern_plots_by_default(monkeypatch) -> None:
    calls = []

    def fake_show(figure, **kwargs):
        calls.append((figure, kwargs))

    monkeypatch.setattr(simulation_module, "_show_figure", fake_show)

    FakeExperiment().chevron_pattern(
        targets=["Q00"],
        detuning_range=[0.0],
        time_range=[0.0],
    )

    assert len(calls) == 1
    assert calls[0][0].layout.title.text == "Chevron pattern : Q00"
    assert calls[0][1]["filename"] == "chevron_pattern_Q00"


def test_t1_t2_and_ramsey_return_experiment_result_data() -> None:
    exp = FakeExperiment(qubit_lifetime=(21.0, 17.0))

    t1 = exp.t1_experiment("Q00", time_range=[100.0, 1000.0], plot=False)
    t2 = exp.t2_experiment("Q00", time_range=[300.0, 1200.0], plot=False)
    ramsey = exp.ramsey_experiment("Q00", time_range=[0.0, 100.0, 200.0], plot=False)

    assert t1.data["Q00"].sweep_range.tolist() == [100.0, 1000.0]
    assert t1.data["Q00"].t1 == 21_000.0
    assert t1.data["Q00"].title == "T1 decay"
    assert t2.data["Q00"].sweep_range.tolist() == [300.0, 1200.0]
    assert t2.data["Q00"].t2 == 17_000.0
    assert t2.data["Q00"].title == "T2 echo"
    assert ramsey.data["Q00"].ramsey_freq == 0.001
    assert ramsey.data["Q00"].bare_freq == exp.qubit_frequencies[0]
    assert ramsey.data["Q00"].title == "Ramsey"


def test_coherence_plots_match_qubex_fit_layout() -> None:
    exp = FakeExperiment(qubit_lifetime=(21.0, 17.0))

    t1 = exp.t1_experiment("Q00", time_range=[100.0, 1000.0], plot=False)
    t2 = exp.t2_experiment("Q00", time_range=[300.0, 1200.0], plot=False)
    ramsey = exp.ramsey_experiment("Q00", time_range=[0.0, 100.0, 200.0], plot=False)

    t1_figure = t1.data["Q00"].plot(return_figure=True)
    t2_figure = t2.data["Q00"].plot(return_figure=True)
    ramsey_figure = ramsey.data["Q00"].plot(return_figure=True)

    assert [trace.name for trace in t1_figure.data] == ["Fit", "Data"]
    assert t1_figure.layout.title.text == "T1 : Q00"
    assert t1_figure.layout.xaxis.title.text == "Time (μs)"
    assert t1_figure.layout.yaxis.title.text == "Population"
    assert [trace.name for trace in t2_figure.data] == ["Fit", "Data"]
    assert t2_figure.layout.title.text == "T2 echo : Q00"
    assert ramsey_figure.layout.title.text == "Ramsey fringe : Q00"
    assert ramsey_figure.layout.yaxis.title.text == "Signal (arb. units)"


def test_coherence_experiments_can_use_simulator_path() -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])
    records = []

    def fake_simulator(schedule, **kwargs):
        records.append((schedule.duration, kwargs["targets"]))
        result = exp._fake_measure_result(kwargs["targets"], shots=kwargs["shots"])
        center = exp._population_to_iq(0.25)
        result.data["Q00"].kerneled = [center]
        result.data["Q00"].data[0].data = [center]
        return result

    exp._simulate_measure_result = fake_simulator

    result = exp.t1_experiment(
        "Q00",
        time_range=[100.0, 200.0],
        plot=False,
        use_simulator=True,
    )

    assert len(records) == 2
    assert records[0][1] == ["Q00"]
    assert result.data["Q00"].data.tolist() == [
        exp._population_to_iq(0.25),
        exp._population_to_iq(0.25),
    ]


def test_coherence_experiments_print_qubex_like_progress(capsys) -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])

    exp.t1_experiment("Q00", time_range=[100.0], plot=False)
    exp.t2_experiment("Q00", time_range=[300.0], plot=False)
    exp.ramsey_experiment("Q00", time_range=[0.0], plot=False)

    output = capsys.readouterr().out
    assert "Target qubits: ['Q00']" in output
    assert "Subgroups: [['Q00']]" in output
    assert "(1/1) Conducting T1 experiment for ['Q00']..." in output
    assert "(1/1) Conducting T2 experiment for ['Q00']..." in output
    assert "Spectator qubits: []" in output
    assert "Bare frequency with |0>:" in output
    assert "  Q00: 7.157231" in output


def test_repeat_sequence_uses_sweep_plot_shape() -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])
    exp.calibrate_drag_hpi_pulse(["Q00"], plot=False)

    result = exp.repeat_sequence(
        exp.drag_hpi_pulse,
        repetitions=2,
        plot=False,
        use_simulator=False,
    )
    figure = result.data["Q00"].plot(return_figure=True)

    assert result.data["Q00"].sweep_range.tolist() == [0, 1, 2]
    assert figure.layout.title.text == "Repeat sequence : Q00"
    assert figure.layout.xaxis.title.text == "Number of repetitions"
    assert figure.layout.yaxis.title.text == "Normalized signal"


def test_pulse_properties_provide_default_calibrated_dicts() -> None:
    exp = FakeExperiment(qubit_labels=["Q00", "Q01"])

    assert set(exp.hpi_pulse) == {"Q00", "Q01"}
    assert set(exp.pi_pulse) == {"Q00", "Q01"}
    assert exp.hpi_pulse is exp.drag_hpi_pulse
    assert exp.pi_pulse is exp.drag_pi_pulse


def test_repeat_sequence_can_use_default_hpi_pulse_dict() -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])

    result = exp.repeat_sequence(exp.hpi_pulse, repetitions=2, plot=False)

    assert result.data["Q00"].sweep_range.tolist() == [0, 1, 2]
    np.testing.assert_allclose(result.data["Q00"].normalized, [1.0, 0.0, -1.0], atol=1e-12)


def test_repeat_sequence_uses_pi_pulse_rotation_angle() -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])

    result = exp.repeat_sequence(exp.pi_pulse, repetitions=4, plot=False)

    np.testing.assert_allclose(
        result.data["Q00"].normalized,
        [1.0, -1.0, 1.0, -1.0, 1.0],
        atol=1e-12,
    )


def test_repeat_sequence_handles_zero_repetitions() -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])
    exp.calibrate_drag_hpi_pulse(["Q00"], plot=False)

    result = exp.repeat_sequence(
        exp.drag_hpi_pulse,
        repetitions=0,
        plot=False,
    )

    assert result.data["Q00"].sweep_range.tolist() == [0]
    assert len(result.data["Q00"].data) == 1


def test_repeat_sequence_rejects_empty_pulse_mapping() -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])

    try:
        exp.repeat_sequence({}, plot=False)
    except ValueError as exc:
        assert "calibrate_hpi_pulse" in str(exc)
    else:
        raise AssertionError("empty pulse mapping should be rejected")


def test_repeat_sequence_uses_simulator_when_explicit_simulator_is_supplied() -> None:
    exp = FakeExperiment(qubit_labels=["Q00"])
    exp.calibrate_drag_hpi_pulse(["Q00"], plot=False)
    calls = []

    def fake_execute(schedule, **kwargs):
        calls.append(kwargs.get("use_simulator"))
        return exp._fake_measure_result(kwargs["targets"], shots=kwargs["n_shots"] or 1024)

    exp.execute = fake_execute

    exp.repeat_sequence(
        exp.drag_hpi_pulse,
        repetitions=1,
        plot=False,
        _simulator=object(),
    )

    assert calls == [True, True]


def test_execute_can_return_probabilities_from_simulated_measurement_path() -> None:
    exp = FakeExperiment()

    def fake_simulator(schedule, **kwargs):
        assert schedule == "pulse-schedule"
        result = exp._fake_measure_result(kwargs["targets"], shots=kwargs["shots"])
        center = exp._population_to_iq(0.25)
        result.data["Q00"].kerneled = [center]
        result.data["Q00"].data[0].data = [center]
        return result

    exp._simulate_measure_result = fake_simulator

    result = exp.execute(
        "pulse-schedule",
        targets=["Q00"],
        shots=100,
        use_simulator=True,
        return_measure_result=False,
    )

    assert result.data["probabilities"]["Q00"] == {"0": 0.75, "1": 0.25}
    assert result.data["counts"] == {"0": 100}


def test_sweep_parameter_uses_simulated_measurement_values_when_available() -> None:
    exp = FakeExperiment()

    def fake_simulator(schedule, **kwargs):
        result = exp._fake_measure_result(kwargs["targets"], shots=kwargs["shots"])
        center = exp._population_to_iq(float(schedule))
        result.data["Q00"].kerneled = [center]
        result.data["Q00"].data[0].data = [center]
        return result

    exp._simulate_measure_result = fake_simulator

    result = exp.sweep_parameter(
        sequence=lambda value: value,
        sweep_range=[0.0, 0.25, 0.5],
        targets=["Q00"],
        shots=10,
        use_simulator=True,
        plot=False,
    )

    assert result.data["Q00"].sweep_range.tolist() == [0.0, 0.25, 0.5]
    assert result.data["Q00"].data.tolist() == [
        exp._population_to_iq(0.0),
        exp._population_to_iq(0.25),
        exp._population_to_iq(0.5),
    ]
