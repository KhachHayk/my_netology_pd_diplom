from django.core.exceptions import ValidationError


def validate_password(value):
    if len(value) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not any(char.isdigit() for char in value):
        raise ValidationError('Password must contain at least one digit.')
    if not any(char.isalpha() for char in value):
        raise ValidationError('Password must contain at least one letter.')