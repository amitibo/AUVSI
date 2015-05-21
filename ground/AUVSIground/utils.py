__author__ = 'Ori'

def decimal_to_minsec(*decimal):
    """
    Converts a number from decimal representation to minute-second
    representation
    :param decimal: the number in decimal (can be ether string or float)
    :return: string
    """
    res = list()
    for num in decimal:
        num = float(num)
        deg = int(num)
        residue = num - deg

        minutes = residue*60
        residue = minutes - int(minutes)
        minutes = int(minutes)

        seconds = round(residue*60, 3)

        deg_symbol = 'd'
        degmin = '''{deg}{deg_sym} {minutes}' {sec}"'''.format(deg=deg,
                                                       deg_sym=deg_symbol,
                                                       minutes=minutes,
                                                       sec=seconds)

        res.append(degmin)

    return res
