__author__ = 'Ori'

import unittest
from AUVSIairborne.services.system_control import ReflectionController
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

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ReflectionControllerCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
