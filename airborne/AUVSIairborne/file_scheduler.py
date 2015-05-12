__author__ = 'Ori'

import os


class FileScheduler(object):
    def __init__(self, dir_path, reversed_order=False):
        self.dir_path = dir_path
        self.files_sent = []
        self.files_skipped = []
        self.reverse_order = reversed_order

    def __iter__(self):
        return self

    def next(self):
        result = self._next_file()
        if result is None:
            raise StopIteration()

        return result

    def _next_file(self):
        files = os.listdir(self.dir_path)
        files.sort(reverse=self.reverse_order)

        for file_name in files:
            if self._needs_to_be_listed(file_name):
                self.files_sent.append(file_name)
                return file_name
        return None

    def reset(self):
        skip_files = []
        for file_name in os.listdir(self.dir_path):
            if self._needs_to_be_listed(file_name):
                skip_files.append(file_name)

        # log.msg("FileScheduler was reset,"
        #         "skipping: {}".format(skip_files))

        self.files_skipped.extend(skip_files)

    def _needs_to_be_listed(self, file_name):
        file_path = os.path.join(self.dir_path, file_name)
        if not os.path.isfile(file_path):
            return False

        file_was_sent = file_name in self.files_sent
        file_was_skipped = file_name in self.files_skipped
        return (not file_was_sent) and (not file_was_skipped)
