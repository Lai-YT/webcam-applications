from gui.page_controller import PageController


#         Current controller hierarchy:
#
#               GuiController
#             (action buttons)
#                    |
#              PageController
#            (check among pages)
#         /                   \
#    OptionController     SettingController
#     (options only)       (settings only)


class GuiController:
    """The GuiController controls the actions of the main GUI,
    but it doesn't directly deal with the PageWidget. A PageController will be used to handle that.
    """
    def __init__(self, model, gui):
        self._model = model
        self._gui = gui
        self._page_controller = PageController(self._gui.page_widget)

        self._enable_buttons()
        self._connect_actions()

    def _enable_buttons(self):
        """Set states of the action buttons."""
        # `Stop` is unabled at the beginning.
        self._gui.action_buttons["Stop"].setEnabled(False)
        # After being clicked, `Stop` is unables and `Start` is enabled.
        self._gui.action_buttons["Stop"].clicked.connect(
            lambda: self._gui.action_buttons["Stop"].setEnabled(False)
        )
        self._gui.action_buttons["Stop"].clicked.connect(
            lambda: self._gui.action_buttons["Start"].setEnabled(True)
        )

    def _connect_actions(self):
        """Connect the actions of the action buttons."""
        # Wiil do some verifications in click_start() before a real start.
        self._gui.action_buttons["Start"].clicked.connect(self._click_start)
        # `Stop` closes the application window.
        self._gui.action_buttons["Stop"].clicked.connect(self._model.close)
        # `Exit` closes both the application windows and GUI.
        self._gui.action_buttons["Exit"].clicked.connect(self._model.close)
        self._gui.action_buttons["Exit"].clicked.connect(self._gui.close)
        # Also stores the GUI states back to the configuration file.
        self._gui.action_buttons["Exit"].clicked.connect(self._page_controller.store_configs)

    def _click_start(self):
        """The Model starts if verifications are passed.
        Since the information that verifications need is in PageWidget,
        communications and delegations with PageController is necessary.
        """
        # To be able to do some verifications before a real start,
        # put all connections in another method instead of directly
        # connecting them.
        # After all verifications are passed, the start() method of Model is called.

        # If `Distance Measure` is selected, check if all parameters are valid.
        valid = self._page_controller.check_inputs_validity()
        if not valid:
             return

        # Now, all verifications are passed, the application is about to start.
        # Unable `Start` and enable `Stop`.
        self._gui.action_buttons["Start"].setEnabled(False)
        self._gui.action_buttons["Stop"].setEnabled(True)
        # Starts the application window.
        self._page_controller.set_model_parameters(self._model)
        self._model.start()
