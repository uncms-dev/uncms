from django.db import models
from django.utils.functional import Promise


def test_help_texts_are_translated():
    # Crappy test to ensure that there are no untranslated fields with
    # user (or admin)-visible values which are not translated.
    untranslated_fields = []
    checked_models = []
    for model in models.Model.__subclasses__():
        # obvs, don't bother to translate anything that isn't our own
        if 'uncms' not in str(model):
            continue
        checked_models.append(model)
        for field in model._meta.fields:
            # To expand to other fields that might have text in them.
            for attr in ['help_text']:
                field_option = getattr(field, attr)
                # allow field option to be empty
                if not field_option:
                    continue
                if not isinstance(field_option, Promise):
                    untranslated_fields.append(f'{model._meta.app_label}.{model._meta.model_name}.{field.name}')  # pragma: no cover

    # canary to ensure that our test hasn't gone bad
    assert len(checked_models) > 2
    assert not untranslated_fields, f'Possible untranslated field options: {untranslated_fields}'
