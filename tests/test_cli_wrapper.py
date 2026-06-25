import unittest

from cli.main import main


class CliWrapperTests(unittest.TestCase):
    def test_cli_wrapper_delegates_to_existing_cli(self):
        self.assertEqual(main(["generate", "--strategy", "random", "--count", "1", "--seed", "3"]), 0)


if __name__ == "__main__":
    unittest.main()
