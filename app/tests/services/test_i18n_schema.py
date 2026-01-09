from app.tests.scripts import validate_translations

"""
Tests for i18n schema validation.
Decided to run that as tests to ensure i18n integrity on each run.
"""
def test_i18n_schema_has_no_errors():
    errs = validate_translations.validate_all()
    assert errs == [], "i18n schema validation failed:\n" + "\n".join(errs)
