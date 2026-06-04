import pytest

from app.domain.aggregates.plugin import Plugin, PluginStatus


def test_plugin_lifecycle():
    plugin = Plugin.propose(
        plugin_id="shell-tools",
        version="1.0.0",
        capabilities=["shell"],
        manifest={"risk_level": "low"},
    )
    plugin.validate()
    plugin.install()
    plugin.activate()
    assert plugin.status == PluginStatus.ACTIVE
    assert len(plugin.get_uncommitted_events()) == 4


def test_cannot_install_before_validate():
    plugin = Plugin.propose("p1", "0.1.0", [])
    with pytest.raises(ValueError):
        plugin.install()
