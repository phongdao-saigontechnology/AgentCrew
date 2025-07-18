from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QScrollArea,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal

from AgentCrew.modules.config import ConfigManagement
from AgentCrew.modules.agents import AgentManager

from AgentCrew.modules.gui.themes import StyleProvider


class MCPsConfigTab(QWidget):
    """Tab for configuring MCP servers."""

    # Add signal for configuration changes
    config_changed = Signal()

    def __init__(self, config_manager: ConfigManagement):
        super().__init__()
        self.config_manager = config_manager
        self.agent_manager = AgentManager.get_instance()
        self.is_dirty = False  # Track unsaved changes

        # Load MCP configuration
        self.mcps_config = self.config_manager.read_mcp_config()

        self.init_ui()
        self.load_mcps()

    def init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QHBoxLayout()

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - MCP server list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.mcps_list = QListWidget()
        self.mcps_list.currentItemChanged.connect(self.on_mcp_selected)

        # Buttons for MCP list management
        list_buttons_layout = QHBoxLayout()
        self.add_mcp_btn = QPushButton("Add")
        # Note: Need to access parent's style provider when the widget is parented
        # For now, use the main style constants
        style_provider = StyleProvider()
        self.add_mcp_btn.setStyleSheet(style_provider.get_button_style("primary"))
        self.add_mcp_btn.clicked.connect(self.add_new_mcp)
        self.remove_mcp_btn = QPushButton("Remove")
        self.remove_mcp_btn.setStyleSheet(style_provider.get_button_style("red"))
        self.remove_mcp_btn.clicked.connect(self.remove_mcp)
        self.remove_mcp_btn.setEnabled(False)  # Disable until selection

        list_buttons_layout.addWidget(self.add_mcp_btn)
        list_buttons_layout.addWidget(self.remove_mcp_btn)

        left_layout.addWidget(QLabel("MCP Servers:"))
        left_layout.addWidget(self.mcps_list)
        left_layout.addLayout(list_buttons_layout)

        # Right panel - MCP editor
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        # right_panel.setStyleSheet("background-color: #181825;") # Set by QDialog stylesheet

        self.editor_widget = QWidget()
        self.editor_widget.setStyleSheet(
            style_provider.get_editor_container_widget_style()
        )
        self.editor_layout = QVBoxLayout(self.editor_widget)

        # Form layout for MCP properties
        form_layout = QFormLayout()

        # Name field
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self._mark_dirty)
        form_layout.addRow("Name:", self.name_input)

        # Streaming server checkbox
        self.streaming_server_checkbox = QCheckBox("Streaming Server")
        self.streaming_server_checkbox.stateChanged.connect(
            self._on_streaming_server_changed
        )
        form_layout.addRow("", self.streaming_server_checkbox)

        # URL field (for streaming servers)
        self.url_input = QLineEdit()
        self.url_input.textChanged.connect(self._mark_dirty)
        self.url_input.setPlaceholderText("http://localhost:8080/mcp")
        self.url_label = QLabel("URL:")
        form_layout.addRow(self.url_label, self.url_input)

        # Command field
        self.command_input = QLineEdit()
        self.command_input.textChanged.connect(self._mark_dirty)
        self.command_label = QLabel("Command:")
        form_layout.addRow(self.command_label, self.command_input)

        # Arguments section
        args_group = QGroupBox("Arguments")
        self.args_group = args_group  # Store reference
        self.args_layout = QVBoxLayout()
        self.arg_inputs = []

        # Add button for arguments
        args_btn_layout = QHBoxLayout()
        self.add_arg_btn = QPushButton("Add Argument")
        self.add_arg_btn.setStyleSheet(style_provider.get_button_style("primary"))
        self.add_arg_btn.clicked.connect(lambda: self.add_argument_field(""))
        args_btn_layout.addWidget(self.add_arg_btn)
        args_btn_layout.addStretch()

        self.args_layout.addLayout(args_btn_layout)
        args_group.setLayout(self.args_layout)

        # Environment variables section
        env_group = QGroupBox("Environment Variables")
        self.env_group = env_group  # Store reference
        self.env_layout = QVBoxLayout()
        self.env_inputs = []

        # Add button for env vars
        env_btn_layout = QHBoxLayout()
        self.add_env_btn = QPushButton("Add Environment Variable")
        self.add_env_btn.setStyleSheet(style_provider.get_button_style("primary"))
        self.add_env_btn.clicked.connect(lambda: self.add_env_field("", ""))
        env_btn_layout.addWidget(self.add_env_btn)
        env_btn_layout.addStretch()

        self.env_layout.addLayout(env_btn_layout)
        env_group.setLayout(self.env_layout)

        # Enabled for agents section
        enabled_group = QGroupBox("Enabled For Agents")
        enabled_layout = QVBoxLayout()

        # Get available agents
        self.available_agents = list(self.agent_manager.agents.keys())

        self.agent_checkboxes = {}
        for agent in self.available_agents:
            checkbox = QCheckBox(agent)
            checkbox.stateChanged.connect(self._mark_dirty)
            self.agent_checkboxes[agent] = checkbox
            enabled_layout.addWidget(checkbox)

        enabled_group.setLayout(enabled_layout)

        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet(style_provider.get_button_style("primary"))
        self.save_btn.clicked.connect(self.save_mcp)
        self.save_btn.setEnabled(False)  # Disable until selection

        # Add all components to editor layout
        self.editor_layout.addLayout(form_layout)
        self.editor_layout.addWidget(args_group)
        self.editor_layout.addWidget(env_group)
        self.editor_layout.addWidget(enabled_group)
        self.editor_layout.addWidget(self.save_btn)
        self.editor_layout.addStretch()

        right_panel.setWidget(self.editor_widget)

        # Add panels to splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 600])  # Initial sizes

        # Add splitter to main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Disable editor initially
        self.set_editor_enabled(False)

    def _mark_dirty(self, *args, **kwargs):
        """Mark the current configuration as dirty and update save button state."""
        # Check if the editor is supposed to be active for the current item
        if self.mcps_list.currentItem() and self.name_input.isEnabled():
            self.is_dirty = True
            self._update_save_button_state()

    def _update_save_button_state(self):
        """Enable or disable the save button based on current item and dirty state."""
        current_item_selected = self.mcps_list.currentItem() is not None
        can_save = current_item_selected and self.is_dirty
        self.save_btn.setEnabled(can_save)

    def _on_streaming_server_changed(self, state):
        """Handle streaming server checkbox state change."""
        is_streaming = state == Qt.CheckState.Checked.value

        # Show/hide fields and labels based on streaming server state
        self._set_sse_fields_visisble(is_streaming)
        self._set_stdio_fields_visible(not is_streaming)

        self._mark_dirty()

    def load_mcps(self):
        """Load MCP servers from configuration."""
        self.mcps_list.clear()

        for server_id, server_config in self.mcps_config.items():
            item = QListWidgetItem(server_config.get("name", server_id))
            item.setData(Qt.ItemDataRole.UserRole, (server_id, server_config))
            self.mcps_list.addItem(item)

    def on_mcp_selected(self, current, previous):
        """Handle MCP server selection."""
        if current is None:
            self.set_editor_enabled(False)
            self.remove_mcp_btn.setEnabled(False)
            return

        # Enable editor and remove button
        self.set_editor_enabled(True)
        self.remove_mcp_btn.setEnabled(True)

        # Get MCP data
        server_id, server_config = current.data(Qt.ItemDataRole.UserRole)

        # Populate form
        self.name_input.setText(server_config.get("name", ""))
        self.streaming_server_checkbox.setChecked(
            server_config.get("streaming_server", False)
        )
        self.url_input.setText(server_config.get("url", ""))
        self.command_input.setText(server_config.get("command", ""))

        # Clear existing argument fields
        self.clear_argument_fields()

        # Add argument fields
        args = server_config.get("args", [])
        for arg in args:
            self.add_argument_field(arg, mark_dirty_on_add=False)

        # Clear existing env fields
        self.clear_env_fields()

        # Add env fields
        env = server_config.get("env", {})
        for key, value in env.items():
            self.add_env_field(key, value, mark_dirty_on_add=False)

        # Set agent checkboxes
        enabled_agents = server_config.get("enabledForAgents", [])
        for agent, checkbox in self.agent_checkboxes.items():
            checkbox.setChecked(agent in enabled_agents)

        # Update field states based on streaming server
        self._on_streaming_server_changed(
            Qt.CheckState.Checked.value
            if server_config.get("streaming_server", False)
            else Qt.CheckState.Unchecked.value
        )

        self.is_dirty = False
        self._update_save_button_state()

    def _set_sse_fields_visisble(self, visible: bool):
        self.url_input.setVisible(visible)
        self.url_label.setVisible(visible)

    def _set_stdio_fields_visible(self, visible: bool):
        self.command_input.setVisible(visible)
        self.command_label.setVisible(visible)
        self.add_arg_btn.setVisible(visible)
        self.add_env_btn.setVisible(visible)

        # Hide/show existing argument and env fields
        for arg_input in self.arg_inputs:
            arg_input["input"].setVisible(visible)
            arg_input["remove_btn"].setVisible(visible)

        for env_input in self.env_inputs:
            env_input["key_input"].setVisible(visible)
            env_input["value_input"].setVisible(visible)
            env_input["remove_btn"].setVisible(visible)

        if hasattr(self, "args_group"):
            self.args_group.setVisible(visible)
        if hasattr(self, "env_group"):
            self.env_group.setVisible(visible)

    def set_editor_enabled(self, enabled: bool):
        """Enable or disable the editor form."""
        self.name_input.setEnabled(enabled)
        self.streaming_server_checkbox.setEnabled(enabled)

        # For visibility-controlled fields, only disable them when editor is disabled
        # Their visibility is controlled by streaming_server state
        if enabled:
            is_streaming = self.streaming_server_checkbox.isChecked()
            self._set_stdio_fields_visible(not is_streaming)
            self._set_sse_fields_visisble(is_streaming)
        else:
            # When editor is disabled, hide all conditional fields and labels
            self.url_input.setVisible(False)
            self.url_label.setVisible(False)
            self.command_input.setVisible(False)
            self.command_label.setVisible(False)
            self.add_arg_btn.setVisible(False)
            self.add_env_btn.setVisible(False)
            if hasattr(self, "args_group"):
                self.args_group.setVisible(False)
            if hasattr(self, "env_group"):
                self.env_group.setVisible(False)

        # Always enable/disable these regardless of visibility
        self.url_input.setEnabled(enabled)
        self.command_input.setEnabled(enabled)
        self.add_arg_btn.setEnabled(enabled)
        self.add_env_btn.setEnabled(enabled)

        for checkbox in self.agent_checkboxes.values():
            checkbox.setEnabled(enabled)

        for arg_input in self.arg_inputs:
            arg_input["input"].setEnabled(enabled)
            arg_input["remove_btn"].setEnabled(enabled)
            if enabled:
                is_streaming = self.streaming_server_checkbox.isChecked()
                arg_input["input"].setVisible(not is_streaming)
                arg_input["remove_btn"].setVisible(not is_streaming)

        for env_input in self.env_inputs:
            env_input["key_input"].setEnabled(enabled)
            env_input["value_input"].setEnabled(enabled)
            env_input["remove_btn"].setEnabled(enabled)
            if enabled:
                is_streaming = self.streaming_server_checkbox.isChecked()
                env_input["key_input"].setVisible(not is_streaming)
                env_input["value_input"].setVisible(not is_streaming)
                env_input["remove_btn"].setVisible(not is_streaming)

        if not enabled:
            self.is_dirty = False
        self._update_save_button_state()

    def add_argument_field(self, value="", mark_dirty_on_add=True):
        """Add a field for an argument."""
        arg_layout = QHBoxLayout()

        arg_input = QLineEdit()
        arg_input.setText(str(value))
        arg_input.textChanged.connect(self._mark_dirty)

        remove_btn = QPushButton("Remove")
        remove_btn.setMaximumWidth(80)

        style_provider = StyleProvider()
        remove_btn.setStyleSheet(style_provider.get_button_style("red"))

        arg_layout.addWidget(arg_input)
        arg_layout.addWidget(remove_btn)

        # Insert before the add button
        self.args_layout.insertLayout(len(self.arg_inputs), arg_layout)

        # Store references
        arg_data = {"layout": arg_layout, "input": arg_input, "remove_btn": remove_btn}
        self.arg_inputs.append(arg_data)

        # Connect remove button
        remove_btn.clicked.connect(lambda: self.remove_argument_field(arg_data))

        if mark_dirty_on_add:
            self._mark_dirty()
        return arg_data

    def remove_argument_field(self, arg_data):
        """Remove an argument field."""
        # Remove from layout
        self.args_layout.removeItem(arg_data["layout"])

        # Delete widgets
        arg_data["input"].deleteLater()
        arg_data["remove_btn"].deleteLater()

        # Remove from list
        self.arg_inputs.remove(arg_data)
        self._mark_dirty()

    def clear_argument_fields(self):
        """Clear all argument fields."""
        while self.arg_inputs:
            self.remove_argument_field(self.arg_inputs[0])

    def add_env_field(self, key="", value="", mark_dirty_on_add=True):
        """Add a field for an environment variable."""
        env_layout = QHBoxLayout()

        key_input = QLineEdit()
        key_input.setText(str(key))
        key_input.setPlaceholderText("Key")
        key_input.textChanged.connect(self._mark_dirty)

        value_input = QLineEdit()
        value_input.setText(str(value))
        value_input.setPlaceholderText("Value")
        value_input.textChanged.connect(self._mark_dirty)

        remove_btn = QPushButton("Remove")
        remove_btn.setMaximumWidth(80)

        style_provider = StyleProvider()
        remove_btn.setStyleSheet(style_provider.get_button_style("red"))

        env_layout.addWidget(key_input)
        env_layout.addWidget(value_input)
        env_layout.addWidget(remove_btn)

        # Insert before the add button
        self.env_layout.insertLayout(len(self.env_inputs), env_layout)

        # Store references
        env_data = {
            "layout": env_layout,
            "key_input": key_input,
            "value_input": value_input,
            "remove_btn": remove_btn,
        }
        self.env_inputs.append(env_data)

        # Connect remove button
        remove_btn.clicked.connect(lambda: self.remove_env_field(env_data))

        if mark_dirty_on_add:
            self._mark_dirty()
        return env_data

    def remove_env_field(self, env_data):
        """Remove an environment variable field."""
        # Remove from layout
        self.env_layout.removeItem(env_data["layout"])

        # Delete widgets
        env_data["key_input"].deleteLater()
        env_data["value_input"].deleteLater()
        env_data["remove_btn"].deleteLater()

        # Remove from list
        self.env_inputs.remove(env_data)
        self._mark_dirty()

    def clear_env_fields(self):
        """Clear all environment variable fields."""
        while self.env_inputs:
            self.remove_env_field(self.env_inputs[0])

    def add_new_mcp(self):
        """Add a new MCP server to the configuration."""
        # Create a new server with default values
        server_id = f"new_server_{len(self.mcps_config) + 1}"
        new_server = {
            "name": "New Server",
            "command": "docker",
            "args": ["run", "-i", "--rm"],
            "env": {},
            "enabledForAgents": [],
            "streaming_server": False,
            "url": "",
        }

        # Add to list
        item = QListWidgetItem(new_server["name"])
        item.setData(Qt.ItemDataRole.UserRole, (server_id, new_server))
        self.mcps_list.addItem(item)
        self.mcps_list.setCurrentItem(item)

        # Mark as dirty since this is a new item that needs to be saved
        self.is_dirty = True
        self._update_save_button_state()

        # Focus on name field for immediate editing
        self.name_input.setFocus()
        self.name_input.selectAll()

    def remove_mcp(self):
        """Remove the selected MCP server."""
        current_item = self.mcps_list.currentItem()
        if not current_item:
            return

        server_id, server_config = current_item.data(Qt.ItemDataRole.UserRole)
        server_name = server_config.get("name", server_id)

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the MCP server '{server_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from list
            row = self.mcps_list.row(current_item)
            self.mcps_list.takeItem(row)

            # Clear editor
            self.set_editor_enabled(False)
            self.name_input.clear()
            self.command_input.clear()
            self.clear_argument_fields()
            self.clear_env_fields()
            for checkbox in self.agent_checkboxes.values():
                checkbox.setChecked(False)
            self.save_all_mcps()

    def save_mcp(self):
        """Save the current MCP server configuration."""
        current_item = self.mcps_list.currentItem()
        if not current_item:
            return

        server_id, old_config = current_item.data(Qt.ItemDataRole.UserRole)

        # Get values from form
        name = self.name_input.text().strip()
        streaming_server = self.streaming_server_checkbox.isChecked()
        url = self.url_input.text().strip()
        command = self.command_input.text().strip()

        # Validate
        if not name:
            QMessageBox.warning(
                self, "Validation Error", "Server name cannot be empty."
            )
            return

        if streaming_server:
            if not url:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "URL cannot be empty for streaming servers.",
                )
                return
        else:
            if not command:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Command cannot be empty for stdio servers.",
                )
                return

        # Get arguments
        args = []
        for arg_data in self.arg_inputs:
            arg_value = arg_data["input"].text().strip()
            if arg_value:
                args.append(arg_value)

        # Get environment variables
        env = {}
        for env_data in self.env_inputs:
            key = env_data["key_input"].text().strip()
            value = env_data["value_input"].text().strip()
            if key:
                env[key] = value

        # Get enabled agents
        enabled_agents = [
            agent
            for agent, checkbox in self.agent_checkboxes.items()
            if checkbox.isChecked()
        ]

        # Update server data
        server_config = {
            "name": name,
            "command": command,
            "args": args,
            "env": env,
            "enabledForAgents": enabled_agents,
            "streaming_server": streaming_server,
            "url": url,
        }

        # Update item in list
        current_item.setText(name)
        current_item.setData(Qt.ItemDataRole.UserRole, (server_id, server_config))

        # Mark as clean since we just saved
        self.is_dirty = False
        self._update_save_button_state()

        # Save all servers to config
        self.save_all_mcps()

    def save_all_mcps(self):
        """Save all MCP servers to the configuration file."""
        mcps_config = {}

        for i in range(self.mcps_list.count()):
            item = self.mcps_list.item(i)
            server_id, server_config = item.data(Qt.ItemDataRole.UserRole)
            mcps_config[server_id] = server_config

        # Save to file
        self.config_manager.write_mcp_config(mcps_config)

        # Update local copy
        self.mcps_config = mcps_config

        # Emit signal that configuration changed
        self.config_changed.emit()
