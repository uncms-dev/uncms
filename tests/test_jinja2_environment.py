from uncms.jinja2_environment.all import sensible_defaults


def test_jinja2_environment_sensible_defaults():
    for auto_reload in [True, False]:
        env = sensible_defaults(autoescape=True, auto_reload=auto_reload)

        # ensure options are preserved
        assert env.auto_reload is auto_reload
        # probably pointless test, but see if it's vaguely sane
        assert env.filters["striptags"]("<b>test</b>") == "test"
