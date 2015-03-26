__author__ = 'Ori'

import unittest
import os
from AUVSIairborne.services.system_control import ReflectionController
from AUVSIairborne.services.\
    directory_synchronization_ftp import FileSendingScheduler
from AUVSIairborne import UnknownCommand


class ReflectionControllerCase(unittest.TestCase):

    def setUp(self):
        class A(object):
            def hi(self):
                return "HI"

            def str_mul(self, x):
                return x*2

            def float_mul(self, x, y):
                return float(x)*float(y)

        self.a = A()
        self.a_controller = ReflectionController(self.a)

    def test_no_args(self):
        self.assertEqual(self.a_controller.apply_cmd("hi"), "HI")

    def test_some_args(self):
        self.assertEqual(self.a_controller.apply_cmd("str_mul x 3"), "33")
        self.assertNotEqual(self.a_controller.apply_cmd("str_mul x 3"), 6)

        self.assertEqual(self.a_controller.apply_cmd("float_mul x 3 y 5"), 15)
        self.assertRaises(UnknownCommand, self.a_controller.apply_cmd,
                          "float_mul x 3 y")

    def test_no_method(self):
        self.assertRaises(UnknownCommand,
                          self.a_controller.apply_cmd, "made_up")


class FileSendingSchedulerCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = "./tmp_file_sending_test"
        os.makedirs(self.test_dir)
        self.file_names = map(str, tuple(range(10)))

        for name in self.file_names:
            self._create_test_file(name)

        self.scheduler = FileSendingScheduler(self.test_dir)

    def tearDown(self):
        for name in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, name))

        os.rmdir(self.test_dir)

    def _create_test_file(self, name):
        open(os.path.join(self.test_dir, str(name)), 'w').close()

    def test_all_files(self):
        self.assertItemsEqual(self.scheduler, self.file_names)
        self.assertItemsEqual(self.scheduler, [])

    def test_file_addition(self):
        self.assertItemsEqual(self.scheduler, self.file_names)

        self._create_test_file("NewFile")
        self.assertItemsEqual(self.scheduler, ["NewFile"],
                              msg="Addition of file wasn't detected"
                                  "by scheduler")

    def test_restart(self):
        for i in range(4):
            self.scheduler.next()

        self.scheduler.reset()

        self.assertItemsEqual(self.scheduler, [])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ReflectionControllerCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
