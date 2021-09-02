from gui.page_controller import OptionController, SettingController


#         Current controller hierarchy:
#
#                GuiController
#               /             \
#    OptionController      SettingController


class GuiController:
    def __init__(self, model, gui):
        """Access the individual pages by calling self._widget.pages["Options" | "Settings" | ...]."""
        self._widget = gui.page_widget
        self._model = model
        self._gui = gui

        self._create_controller()
    
    def _create_controller(self):
        """Creates the controllers of the individual pages."""
        self._page_controllers = {}
        self._page_controllers["Settings"] = SettingController(
            setting_widget=self._widget.pages["Settings"],
            model=self._model
        )
        self._page_controllers["Options"] = OptionController(
            option_widget=self._widget.pages["Options"],
            model=self._model,
            settings_check_callback=self._page_controllers["Settings"].check_inputs_validity,
            exit_callback=self._gui.close
        )