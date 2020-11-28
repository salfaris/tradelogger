def myr(value):
    """Format value as MYR."""
    return f"RM{value:,.2f}"

def round_pl(value):
    return round(value/100., 2)