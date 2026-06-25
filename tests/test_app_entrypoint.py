import unittest

from app.main import main
from app.scripts.registry import create_default_registry


class AppEntrypointTests(unittest.TestCase):
    def test_check_mode_validates_default_script_registry_without_gui_dependency(self):
        self.assertEqual(main(["--check"]), 0)
        registry = create_default_registry()
        self.assertEqual(registry.list()[0].script_id, "ssq")


if __name__ == "__main__":
    unittest.main()
