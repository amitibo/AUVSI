__author__ = 'Ori'
import os

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


class FileSelector(object):
    '''
    A class that creates a list of the files in a given path.
    returns the next file or previous file in the list
    and update the given file to be set as the current file for future calls
    '''
    def __init__(self, dir_path, extension):
        self.dir_path = dir_path
        self.extension = extension
        self.current_file = None

    def _get_file_list(self):
        files = os.listdir(self.dir_path)
        return sorted([f for f in files if f.endswith('.' + self.extension)])

    def next_file(self):
        file_list = self._get_file_list()

        if not self.current_file:
            try:
                self.current_file = file_list[0]
            except IndexError:
                raise NoFiles()

            return self.current_file

        current_file_index = file_list.index(self.current_file)
        try:
            self.current_file = file_list[current_file_index + 1]
        except IndexError:
            pass
        return self.current_file

    def prev_file(self):
        file_list = self._get_file_list()

        if not self.current_file:
            try:
                self.current_file = file_list[0]
            except IndexError:
                raise NoFiles()

            return self.current_file

        current_file_index = file_list.index(self.current_file)

        self.current_file = file_list[max(current_file_index - 1, 0)]
        return self.current_file

