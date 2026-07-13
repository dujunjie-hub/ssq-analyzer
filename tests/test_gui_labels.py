import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox

from app.gui.main_window import MainWindow


class GuiLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_choice_controls_display_chinese_but_keep_internal_values(self):
        window = MainWindow()

        command = window._controls["command"]
        strategy = window._controls["strategy"]

        self.assertIsInstance(command, QComboBox)
        self.assertEqual(command.itemText(command.findData("generate")), "生成推荐号码")
        self.assertEqual(command.findData("fetch"), -1)
        self.assertEqual(strategy.itemText(strategy.findData("balanced")), "均衡模型")
        self.assertEqual(window._refresh_button.text(), "刷新历史数据")
        self.assertEqual(window._params()["command"], "generate")
        self.assertEqual(window._params()["strategy"], "balanced")


if __name__ == "__main__":
    unittest.main()
