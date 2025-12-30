


from app.tests.scripts import validate_translations


def test_i18n_schema_has_no_errors():
    errs = validate_translations.validate_all()
    assert errs == [], "i18n schema validation failed:\n" + "\n".join(errs)
