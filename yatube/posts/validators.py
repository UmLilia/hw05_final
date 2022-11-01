from django import forms


def validate_not_empty(value):
    if value == '':
        raise forms.ValidationError(
            'не заполнено поле "текст"',
            params={'value': value},
        )
