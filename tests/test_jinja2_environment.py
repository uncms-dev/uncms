from uncms.jinja2_environment.all import sensible_defaults


def test_jinja2_environment_sensible_defaults():
    env = sensible_defaults(autoescape=True, auto_reload=True)
    # ensure options are preserved
    assert env.auto_reload is True
    assert env.filters['striptags']('<b>test</b>') == 'test'
