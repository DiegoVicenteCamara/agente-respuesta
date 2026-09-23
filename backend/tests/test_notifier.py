from backend.voice import notifier


def test_silent_no_speech():
    out = notifier.build_spoken_update({"message": "Guardado", "priority": "silent"})
    assert out is None


def test_info_builds_message():
    out = notifier.build_spoken_update({"message": "Búsqueda terminada", "priority": "info"})
    assert out is not None
    assert "Búsqueda terminada" in out
    assert out.startswith("Disculpa que te interrumpa")


def test_urgent_uses_attention_prefix():
    out = notifier.build_spoken_update({"message": "Elige la opción A o B", "priority": "urgent"})
    assert out is not None
    assert out.startswith("Necesito tu atención")


def test_missing_message_returns_none():
    assert notifier.build_spoken_update({}) is None
    assert notifier.build_spoken_update({"priority": "info", "message": "   "}) is None


def test_default_priority_is_info():
    assert notifier.classify({"message": "x"}) == "info"
    assert notifier.classify({"message": "x", "priority": "urgent"}) == "urgent"


def test_task_cancelled_is_not_spoken():
    # La tool cancel_task ya confirma por ctx.update: el evento solo va al panel.
    out = notifier.build_spoken_update(
        {"type": "task_cancelled", "message": "Tarea cancelada", "priority": "info"}
    )
    assert out is None