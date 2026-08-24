from decimal import Decimal


def json_safe(value):
    """Converte Decimal recursivamente para números JSON sem alterar o cálculo interno."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value
