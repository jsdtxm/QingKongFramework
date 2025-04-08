import click


def parse_dict(ctx, param, value):
    """Parse a series of key-value pairs into a dictionary."""
    d = {}
    if value:
        for item in value:
            if "=" not in item:
                raise click.BadParameter(f"Expected format 'key=value', got '{item}'")
            k, v = item.split("=", 1)
            d[k] = v
    return d
