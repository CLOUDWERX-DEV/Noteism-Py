# Standard Library Imports
import os
import sys
import shutil
import re

# Markdown and Syntax Highlighting
import markdown
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

# PyQt5 Core Imports
from PyQt5.QtCore import (
    Qt, pyqtSignal, QTimer, QDir, QModelIndex, QSize, QUrl, QSettings
)

# PyQt5 Widgets Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTextEdit, QAction, QMenuBar, QMenu, QToolBar, 
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox, 
    QInputDialog, QLabel, QStatusBar, QListWidget, QListWidgetItem, 
    QDialog, QFormLayout, QDialogButtonBox, QLineEdit, QPushButton, 
    QFileSystemModel, QAbstractItemView, QFileDialog, QToolButton,
    QActionGroup, QComboBox, QSpinBox
)

# PyQt5 Web Engine Imports
from PyQt5.QtWebEngineWidgets import QWebEngineView

# PyQt5 GUI Imports
from PyQt5.QtGui import (
    QTextCharFormat, QTextDocument, QPalette, QKeySequence, 
    QTextBlockFormat, QStandardItemModel, QStandardItem, QFont, 
    QSyntaxHighlighter, QTextCursor, QIcon, QColor
)

# Typing
from typing import List, Optional

# QDarkStyle
import qdarkstyle

class NeonPalette:
    # Dark Theme Color Palette
    BACKGROUND_DARKEST = '#121420'  # Deep dark blue-black
    BACKGROUND_DARK = '#1A1E2E'     # Dark blue-gray
    BACKGROUND_SECONDARY = '#252836'  # Slightly lighter dark blue-gray
    
    # Text Colors
    TEXT_COLOR = '#FFFFFF'          # Pure white
    TEXT_MUTED = '#8C94A6'          # Soft muted blue-gray
    
    # Neon Accent Colors
    NEON_BLUE = '#3498db'           # Bright neon blue
    NEON_GREEN = '#2ecc71'          # Neon green
    NEON_PURPLE = '#9b59b6'         # Neon purple
    
    # Highlight and Interaction Colors
    ACCENT_BLUE = '#5DADE2'         # Softer accent blue
    HIGHLIGHT_BLUE = 'rgba(52, 152, 219, 0.3)'  # Translucent highlight

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Heading formats
        heading_format = QTextCharFormat()
        heading_format.setForeground(QColor(NeonPalette.NEON_BLUE))
        heading_format.setFontWeight(QFont.Bold)
        
        # Rule for headings
        self.highlighting_rules.append((re.compile(r'^#+\s.*$', re.MULTILINE), heading_format))
        
        # Code block format
        code_format = QTextCharFormat()
        code_format.setForeground(QColor(NeonPalette.NEON_GREEN))
        code_format.setFontFamily("Fira Code")
        
        # Rule for code blocks
        self.highlighting_rules.append((re.compile(r'`{1,3}.*?`{1,3}', re.DOTALL), code_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class MarkdownToolbar:
    @staticmethod
    def apply_format(text_edit, format_func):
        """Apply a formatting function to selected or current text"""
        cursor = text_edit.textCursor()
        
        # If no text is selected, select the current word
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
        
        selected_text = cursor.selectedText()
        formatted_text = format_func(selected_text)
        
        cursor.insertText(formatted_text)
        text_edit.setTextCursor(cursor)
        text_edit.setFocus()

    @classmethod
    def bold(cls, text_edit):
        def bold_format(text):
            return f"**{text}**"
        cls.apply_format(text_edit, bold_format)

    @classmethod
    def italic(cls, text_edit):
        def italic_format(text):
            return f"*{text}*"
        cls.apply_format(text_edit, italic_format)

    @classmethod
    def strikethrough(cls, text_edit):
        def strikethrough_format(text):
            return f"~~{text}~~"
        cls.apply_format(text_edit, strikethrough_format)

    @classmethod
    def code_inline(cls, text_edit):
        def code_format(text):
            return f"`{text}`"
        cls.apply_format(text_edit, code_format)

    @classmethod
    def insert_link(cls, text_edit):
        # Open a dialog to get link details
        link_dialog = QDialog()
        link_dialog.setWindowTitle("Insert Link")
        
        layout = QFormLayout()
        text_input = QLineEdit()
        url_input = QLineEdit()
        
        layout.addRow("Link Text:", text_input)
        layout.addRow("URL:", url_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addRow(buttons)
        
        link_dialog.setLayout(layout)
        
        def on_accept():
            link_text = text_input.text()
            url = url_input.text()
            
            if link_text and url:
                cursor = text_edit.textCursor()
                cursor.insertText(f"[{link_text}]({url})")
            
            link_dialog.accept()
        
        buttons.accepted.connect(on_accept)
        buttons.rejected.connect(link_dialog.reject)
        
        link_dialog.exec_()
    
    @classmethod
    def insert_code_block(cls, text_edit):
        # Open a dialog to select language
        language, ok = QInputDialog.getText(
            None, 
            "Code Block", 
            "Enter programming language (optional):"
        )
        
        if ok:
            cursor = text_edit.textCursor()
            language_prefix = f"{language}\n" if language else ""
            cursor.insertText(f"```{language_prefix}\n\n```")
            
            # Move cursor inside the code block
            cursor.movePosition(QTextCursor.Up)
            text_edit.setTextCursor(cursor)

    @classmethod
    def insert_heading(cls, text_edit, level):
        def heading_format(text):
            return f"{'#' * level} {text}"
        cls.apply_format(text_edit, heading_format)

    @classmethod
    def insert_list(cls, text_edit, ordered=False):
        cursor = text_edit.textCursor()
        prefix = "1. " if ordered else "- "
        cursor.insertText(f"{prefix}List item\n{prefix}")
        text_edit.setTextCursor(cursor)

    @classmethod
    def insert_table(cls, text_edit):
        """Insert a markdown table"""
        dialog = QDialog()
        dialog.setWindowTitle("Insert Markdown Table")
        layout = QFormLayout()
        
        rows_input = QLineEdit()
        rows_input.setPlaceholderText("Number of rows")
        columns_input = QLineEdit()
        columns_input.setPlaceholderText("Number of columns")
        
        layout.addRow("Rows:", rows_input)
        layout.addRow("Columns:", columns_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        def generate_table():
            try:
                num_rows = int(rows_input.text())
                num_cols = int(columns_input.text())
                
                # Create table header
                header = "| " + " | ".join(["Header"] * num_cols) + " |"
                separator = "| " + " | ".join(["---"] * num_cols) + " |"
                
                # Create rows
                rows = []
                for _ in range(num_rows):
                    row = "| " + " | ".join([""] * num_cols) + " |"
                    rows.append(row)
                
                # Combine all parts
                table = "\n".join([header, separator] + rows)
                
                # Insert table at cursor
                cursor = text_edit.textCursor()
                cursor.insertText(table)
                text_edit.setTextCursor(cursor)
                
                dialog.accept()
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Please enter valid numbers for rows and columns.")
        
        buttons.accepted.connect(generate_table)
        buttons.rejected.connect(dialog.reject)
        
        dialog.exec_()
    
    @classmethod
    def insert_task_list(cls, text_edit):
        """Insert a markdown task list"""
        dialog = QDialog()
        dialog.setWindowTitle("Insert Task List")
        layout = QFormLayout()
        
        tasks_input = QLineEdit()
        tasks_input.setPlaceholderText("Enter tasks separated by commas")
        
        layout.addRow("Tasks:", tasks_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        def generate_task_list():
            tasks = tasks_input.text().split(',')
            task_list = "\n".join([f"- [ ] {task.strip()}" for task in tasks])
            
            # Insert task list at cursor
            cursor = text_edit.textCursor()
            cursor.insertText(task_list)
            text_edit.setTextCursor(cursor)
            
            dialog.accept()
        
        buttons.accepted.connect(generate_task_list)
        buttons.rejected.connect(dialog.reject)
        
        dialog.exec_()
    
    @classmethod
    def insert_footnote(cls, text_edit):
        """Insert a markdown footnote"""
        dialog = QDialog()
        dialog.setWindowTitle("Insert Footnote")
        layout = QFormLayout()
        
        text_input = QLineEdit()
        text_input.setPlaceholderText("Footnote text")
        
        layout.addRow("Footnote Text:", text_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        def insert_footnote():
            footnote_text = text_input.text()
            if footnote_text:
                # Generate a unique footnote reference
                footnote_ref = f"[^{len(text_edit.toPlainText().split('[^'))}]"
                
                # Insert footnote reference in text
                cursor = text_edit.textCursor()
                cursor.insertText(f"{footnote_ref}")
                text_edit.setTextCursor(cursor)
                
                # Add footnote at the end of the document
                cursor.movePosition(QTextCursor.End)
                cursor.insertText(f"\n\n{footnote_ref}: {footnote_text}")
                
                dialog.accept()
        
        buttons.accepted.connect(insert_footnote)
        buttons.rejected.connect(dialog.reject)
        
        dialog.exec_()
    
    @classmethod
    def insert_horizontal_rule(cls, text_edit):
        """Insert a horizontal rule"""
        cursor = text_edit.textCursor()
        cursor.insertText("\n\n---\n\n")
        text_edit.setTextCursor(cursor)
    
    @classmethod
    def insert_blockquote(cls, text_edit):
        """Insert a blockquote"""
        dialog = QDialog()
        dialog.setWindowTitle("Insert Blockquote")
        layout = QFormLayout()
        
        quote_input = QTextEdit()
        quote_input.setPlaceholderText("Enter blockquote text")
        
        layout.addRow("Blockquote:", quote_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        def insert_blockquote():
            quote_text = quote_input.toPlainText()
            if quote_text:
                # Prefix each line with '>'
                blockquote = "\n".join([f"> {line}" for line in quote_text.split('\n')])
                
                # Insert blockquote
                cursor = text_edit.textCursor()
                cursor.insertText(f"\n\n{blockquote}\n\n")
                text_edit.setTextCursor(cursor)
                
                dialog.accept()
        
        buttons.accepted.connect(insert_blockquote)
        buttons.rejected.connect(dialog.reject)
        
        dialog.exec_()

class MarkdownFileExplorer(QTreeWidget):
    file_opened = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Set dark theme styling for file explorer
        self.setStyleSheet(f"""
        QTreeWidget {{
            background-color: {NeonPalette.BACKGROUND_DARK};
            color: #FFFFFF;  /* Pure white for all text */
            border: 1px solid {NeonPalette.NEON_BLUE};
            font-family: 'Inter UI', Arial, sans-serif;
        }}
        QTreeWidget::item {{
            background-color: {NeonPalette.BACKGROUND_DARK};
            color: #FFFFFF;  /* Pure white for all items */
            padding: 5px;
            margin: 2px;
        }}
        QTreeWidget::item:hover {{
            background-color: {NeonPalette.BACKGROUND_SECONDARY};
            color: {NeonPalette.NEON_BLUE};
        }}
        QTreeWidget::item:selected {{
            background-color: {NeonPalette.NEON_BLUE};
            color: #FFFFFF;  /* White text on selection */
        }}
        QHeaderView::section {{
            background-color: {NeonPalette.BACKGROUND_SECONDARY};
            color: #FFFFFF;  /* White header text */
            padding: 5px;
            border: 1px solid {NeonPalette.NEON_BLUE};
            font-weight: bold;
        }}
        QScrollBar:vertical {{
            background-color: {NeonPalette.BACKGROUND_SECONDARY};
            width: 10px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {NeonPalette.NEON_BLUE};
            border-radius: 5px;
        }}
        """)
        
        # Configure tree widget
        self.setHeaderLabels(["Name", "Type"])
        self.setColumnCount(2)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Set specific root path for markdown files
        self.current_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'md')
        
        # Ensure the directory exists safely
        try:
            os.makedirs(self.current_root, exist_ok=True)
        except Exception as e:
            print(f"Error creating markdown directory: {e}")
        
        # Populate tree
        self.populate_tree(self.current_root)
        
        # Connect signals
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def populate_tree(self, root_path):
        """Populate the tree with markdown files and directories"""
        self.clear()
        
        # Create root item
        root_item = QTreeWidgetItem([os.path.basename(root_path), "Directory"])
        self.addTopLevelItem(root_item)
        
        # Recursively add markdown files and directories
        self._add_markdown_children(root_item, root_path)
        
        # Expand root
        root_item.setExpanded(True)
    
    def _add_markdown_children(self, parent_item, path):
        """Recursively add markdown files and directories"""
        try:
            for entry in os.scandir(path):
                # Create tree widget item
                item = QTreeWidgetItem(parent_item)
                
                # Set name and type
                item.setText(0, entry.name)
                
                if entry.is_dir():
                    item.setText(1, "Directory")
                    # Recursively add children for directories
                    self._add_markdown_children(item, entry.path)
                elif entry.is_file() and entry.name.lower().endswith('.md'):
                    item.setText(1, "Markdown")
        except Exception as e:
            print(f"Error populating markdown tree: {e}")
    
    def on_item_double_clicked(self, item, column):
        """Handle double-click on file or directory"""
        file_path = os.path.join(self.current_root, item.text(0))
        
        # Construct full path, traversing up the tree if needed
        current_item = item
        path_parts = [item.text(0)]
        while current_item.parent():
            current_item = current_item.parent()
            if current_item.text(0) != os.path.basename(self.current_root):
                path_parts.insert(0, current_item.text(0))
        
        full_path = os.path.join(self.current_root, *path_parts)
        
        if os.path.isdir(full_path):
            # If it's a directory, expand/collapse
            item.setExpanded(not item.isExpanded())
        
        elif os.path.isfile(full_path) and full_path.lower().endswith('.md'):
            # Emit signal to open markdown file
            self.file_opened.emit(full_path)
    
    def show_context_menu(self, pos):
        """Show context menu for file/directory operations"""
        item = self.itemAt(pos)
        
        context_menu = QMenu(self)
        
        # Always allow creating new markdown file or folder in the root
        new_file_action = context_menu.addAction("New Markdown File")
        new_folder_action = context_menu.addAction("New Folder")
        
        # If an item is selected, add rename and delete options
        if item:
            # Construct full path, traversing up the tree if needed
            current_item = item
            path_parts = [item.text(0)]
            while current_item.parent():
                current_item = current_item.parent()
                if current_item.text(0) != os.path.basename(self.current_root):
                    path_parts.insert(0, current_item.text(0))
            
            full_path = os.path.join(self.current_root, *path_parts)
            
            if os.path.exists(full_path):
                rename_action = context_menu.addAction("Rename")
                delete_action = context_menu.addAction("Delete")
        
        # Execute menu
        action = context_menu.exec_(self.mapToGlobal(pos))
        
        # Handle actions
        if action:
            if action.text() == "New Markdown File":
                self.create_new_markdown_file(self.current_root)
            elif action.text() == "New Folder":
                self.create_new_folder(self.current_root)
            elif action and item and action.text() == "Rename":
                self.rename_file(full_path)
            elif action and item and action.text() == "Delete":
                self.delete_file(full_path)
    
    def create_new_markdown_file(self, directory):
        """Create a new markdown file in the specified directory"""
        file_name, ok = QInputDialog.getText(
            self, 
            "New Markdown File", 
            "Enter file name (include .md extension):"
        )
        
        if ok and file_name:
            if not file_name.lower().endswith('.md'):
                file_name += '.md'
            
            full_path = os.path.join(directory, file_name)
            
            try:
                with open(full_path, 'w') as f:
                    f.write("# New Markdown File\n")
                
                # Refresh tree and open file
                self.populate_tree(self.current_root)
                self.file_opened.emit(full_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create file: {str(e)}")
    
    def create_new_folder(self, parent_directory):
        """Create a new folder in the specified directory"""
        folder_name, ok = QInputDialog.getText(
            self, 
            "New Folder", 
            "Enter folder name:"
        )
        
        if ok and folder_name:
            full_path = os.path.join(parent_directory, folder_name)
            
            try:
                os.makedirs(full_path)
                
                # Refresh tree
                self.populate_tree(self.current_root)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not create folder: {str(e)}")
    
    def rename_file(self, file_path):
        """Rename a file or folder"""
        current_name = os.path.basename(file_path)
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename", 
            "Enter new name:", 
            text=current_name
        )
        
        if ok and new_name:
            directory = os.path.dirname(file_path)
            new_path = os.path.join(directory, new_name)
            
            try:
                os.rename(file_path, new_path)
                
                # Refresh tree
                self.populate_tree(self.current_root)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not rename: {str(e)}")
    
    def delete_file(self, file_path):
        """Delete a file or folder with confirmation"""
        confirm = QMessageBox.question(
            self, 
            "Delete", 
            f"Are you sure you want to delete {os.path.basename(file_path)}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                
                # Refresh tree
                self.populate_tree(self.current_root)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete: {str(e)}")

class ThemeManager:
    """Manages application themes and styling"""
    
    THEMES = {
        'Neon Dark': {
            'background': NeonPalette.BACKGROUND_DARK,
            'text_color': '#FFFFFF',
            'accent_color': NeonPalette.NEON_BLUE,
            'secondary_background': NeonPalette.BACKGROUND_SECONDARY
        },
        'Classic Light': {
            'background': '#FFFFFF',
            'text_color': '#000000',
            'accent_color': '#3498db',
            'secondary_background': '#f0f0f0'
        },
        'Solarized': {
            'background': '#002b36',  # Solarized Dark base
            'text_color': '#839496',
            'accent_color': '#268bd2',
            'secondary_background': '#073642'
        },
        'Dracula': {
            'background': '#282a36',
            'text_color': '#f8f8f2',
            'accent_color': '#bd93f9',
            'secondary_background': '#44475a'
        }
    }
    
    def __init__(self, main_window):
        """Initialize theme manager"""
        self.main_window = main_window
        self.current_theme = 'Neon Dark'
    
    def apply_theme(self, theme_name):
        """Apply selected theme to the entire application"""
        if theme_name not in self.THEMES:
            print(f"Theme {theme_name} not found. Defaulting to Neon Dark.")
            theme_name = 'Neon Dark'
        
        theme = self.THEMES[theme_name]
        
        # Update global palette
        NeonPalette.BACKGROUND_DARK = theme['background']
        NeonPalette.TEXT_COLOR = theme['text_color']
        NeonPalette.NEON_BLUE = theme['accent_color']
        NeonPalette.BACKGROUND_SECONDARY = theme['secondary_background']
        
        # Reapply stylesheet to all components
        self._update_file_explorer()
        self._update_markdown_editors()
        self._update_toolbars()
        self._update_menus()
        
        # Store current theme
        self.current_theme = theme_name
    
    def _update_file_explorer(self):
        """Update file explorer styling"""
        for explorer in self.main_window.findChildren(MarkdownFileExplorer):
            explorer.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {NeonPalette.BACKGROUND_DARK};
                color: {NeonPalette.TEXT_COLOR};
                border: 1px solid {NeonPalette.NEON_BLUE};
                font-family: 'Inter UI', Arial, sans-serif;
            }}
            QTreeWidget::item {{
                background-color: {NeonPalette.BACKGROUND_DARK};
                color: {NeonPalette.TEXT_COLOR};
                padding: 5px;
                margin: 2px;
            }}
            QTreeWidget::item:hover {{
                background-color: {NeonPalette.BACKGROUND_SECONDARY};
                color: {NeonPalette.NEON_BLUE};
            }}
            QTreeWidget::item:selected {{
                background-color: {NeonPalette.NEON_BLUE};
                color: {NeonPalette.TEXT_COLOR};
            }}
            """)
    
    def _update_markdown_editors(self):
        """Update markdown editor styling"""
        for editor in self.main_window.findChildren(QTextEdit):
            editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {NeonPalette.BACKGROUND_DARK};
                color: {NeonPalette.TEXT_COLOR};
                border: 1px solid {NeonPalette.NEON_BLUE};
                font-family: 'Fira Code';
                selection-background-color: {NeonPalette.NEON_BLUE};
                padding: 10px;
            }}
            """)
    
    def _update_toolbars(self):
        """Update toolbar styling"""
        for toolbar in self.main_window.findChildren(QToolBar):
            toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {NeonPalette.BACKGROUND_SECONDARY};
                color: {NeonPalette.TEXT_COLOR};
                border: none;
            }}
            QToolButton {{
                background-color: {NeonPalette.BACKGROUND_SECONDARY};
                color: {NeonPalette.TEXT_COLOR};
                border: none;
                padding: 5px;
            }}
            QToolButton:hover {{
                background-color: {NeonPalette.NEON_BLUE};
                color: {NeonPalette.TEXT_COLOR};
            }}
            """)
    
    def _update_menus(self):
        """Update menu styling"""
        for menu in self.main_window.findChildren(QMenu):
            menu.setStyleSheet(f"""
            QMenu {{
                background-color: {NeonPalette.BACKGROUND_DARK};
                color: {NeonPalette.TEXT_COLOR};
                border: 1px solid {NeonPalette.NEON_BLUE};
            }}
            QMenu::item {{
                background-color: {NeonPalette.BACKGROUND_DARK};
                color: {NeonPalette.TEXT_COLOR};
                padding: 5px;
            }}
            QMenu::item:selected {{
                background-color: {NeonPalette.NEON_BLUE};
                color: {NeonPalette.TEXT_COLOR};
            }}
            """)

class NoteismMarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Noteism - Markdown Editor")
        self.resize(1600, 900)
        
        # Set current root directory
        self.current_root = os.path.join(
            os.path.expanduser('~'), 
            'Documents', 
            'Noteism'
        )
        
        # Create documents directory if it doesn't exist
        os.makedirs(self.current_root, exist_ok=True)
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(self)
        
        # Set global dark theme and styling
        self.setStyleSheet(f"""
        /* Global Application Styling */
        QMainWindow {{
            background-color: {NeonPalette.BACKGROUND_DARKEST};
            color: {NeonPalette.TEXT_COLOR};
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {NeonPalette.BACKGROUND_DARK};
            color: {NeonPalette.TEXT_COLOR};
            border: none;
        }}
        QMenuBar::item {{
            background-color: {NeonPalette.BACKGROUND_DARK};
            color: {NeonPalette.TEXT_COLOR};
            spacing: 10px;
            padding: 5px 10px;
        }}
        QMenuBar::item:selected {{
            background-color: {NeonPalette.HIGHLIGHT_BLUE};
            color: {NeonPalette.NEON_BLUE};
        }}
        
        /* Text Edit / Markdown Editor */
        QTextEdit {{
            background-color: {NeonPalette.BACKGROUND_DARK};
            color: {NeonPalette.TEXT_COLOR};
            border: 1px solid {NeonPalette.NEON_BLUE};
            font-family: 'Fira Code';
            selection-background-color: {NeonPalette.HIGHLIGHT_BLUE};
            padding: 10px;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            background-color: {NeonPalette.BACKGROUND_SECONDARY};
            border: 1px solid {NeonPalette.NEON_BLUE};
        }}
        QTabBar::tab {{
            background-color: {NeonPalette.BACKGROUND_DARK};
            color: {NeonPalette.TEXT_COLOR};
            padding: 8px 15px;
            margin-right: 5px;
            border: 1px solid {NeonPalette.NEON_BLUE};
        }}
        QTabBar::tab:selected {{
            background-color: {NeonPalette.NEON_BLUE};
            color: {NeonPalette.BACKGROUND_DARKEST};
        }}
        
        /* Web Engine View / Preview Pane */
        QWebEngineView {{
            background-color: {NeonPalette.BACKGROUND_DARK};
            border: 1px solid {NeonPalette.NEON_BLUE};
        }}
        
        /* Toolbar */
        QToolBar {{
            background-color: {NeonPalette.BACKGROUND_DARK};
            border: none;
            spacing: 5px;
            padding: 5px;
        }}
        QToolBar QToolButton {{
            background-color: {NeonPalette.BACKGROUND_SECONDARY};
            color: {NeonPalette.TEXT_COLOR};
            border: 1px solid {NeonPalette.NEON_BLUE};
            border-radius: 3px;
            padding: 5px;
            margin: 2px;
        }}
        QToolBar QToolButton:hover {{
            background-color: {NeonPalette.HIGHLIGHT_BLUE};
            color: {NeonPalette.NEON_BLUE};
        }}
        
        /* Splitter */
        QSplitter {{
            background-color: {NeonPalette.BACKGROUND_DARKEST};
        }}
        QSplitter::handle {{
            background-color: {NeonPalette.NEON_BLUE};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {NeonPalette.BACKGROUND_DARK};
            color: {NeonPalette.TEXT_COLOR};
            border-top: 1px solid {NeonPalette.NEON_BLUE};
        }}
        QStatusBar QLabel {{
            color: {NeonPalette.TEXT_MUTED};
            margin-right: 10px;
        }}
        """)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create splitter for three-pane layout
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Pane: File Explorer
        self.file_explorer = MarkdownFileExplorer()
        
        # Middle Pane: Markdown Editor with Tabs
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        
        # Create initial tab
        self.create_new_tab()
        
        # Right Pane: Markdown Preview
        self.preview_view = QWebEngineView()
        
        # Set initial dark theme HTML for preview pane
        self.preview_view.setHtml(f"""
        <html>
        <head>
            <style>
                html, body {{ 
                    background-color: {NeonPalette.BACKGROUND_DARK} !important; 
                    color: {NeonPalette.TEXT_COLOR} !important; 
                    font-family: 'Inter UI', Arial, sans-serif; 
                    padding: 20px;
                    margin: 0;
                }}
                p {{ 
                    color: {NeonPalette.TEXT_COLOR} !important; 
                }}
            </style>
        </head>
        <body>
            <p>Markdown Preview</p>
        </body>
        </html>
        """)
        
        # Add widgets to splitter
        splitter.addWidget(self.file_explorer)
        splitter.addWidget(self.editor_tabs)
        splitter.addWidget(self.preview_view)
        
        # Set splitter sizes
        splitter.setSizes([200, 600, 400])
        
        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Connect file explorer signal
        self.file_explorer.file_opened.connect(self.open_markdown_file)
        
        # Create status bar
        self.create_status_bar()
        
        # Connect signals
        self.current_editor().textChanged.connect(self.update_preview)
        
        # Initialize QSettings for persistent configuration
        self.settings = QSettings('CloudWerx Lab', 'Noteism')
        
        # Restore previous settings
        self.restore_settings()
        
    def change_font_family(self, font_name):
        """Change font family for all open editors"""
        font = QFont(font_name)
        
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            editor.setFont(font)
        
        # Persist font preference
        self.settings.setValue("editor/font_family", font_name)
    
    def change_font_size(self, size):
        """Change font size for all open editors"""
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            current_font = editor.font()
            current_font.setPointSize(size)
            editor.setFont(current_font)
        
        # Persist font size preference
        self.settings.setValue("editor/font_size", size)
    
    def set_tab_width(self, width):
        """Set tab width for all open editors"""
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            editor.setTabStopDistance(width * 10)  # Approximate pixel width
        
        # Persist tab width preference
        self.settings.setValue("editor/tab_width", width)
    
    def set_auto_save_interval(self, interval):
        """Set auto save interval and start/stop timer"""
        # Stop existing timer if it exists
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        
        # If interval is 0, auto-save is disabled
        if interval > 0:
            # Create or recreate timer
            self.auto_save_timer = QTimer(self)
            self.auto_save_timer.timeout.connect(self.auto_save)
            self.auto_save_timer.start(interval * 60 * 1000)  # Convert minutes to milliseconds
        
        # Persist auto-save preference
        self.settings.setValue("editor/auto_save_interval", interval)
    
    def auto_save(self):
        """Automatically save all modified files"""
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            file_path = editor.property("file_path")
            
            # Check if file has been saved before and is modified
            if file_path and editor.document().isModified():
                try:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(editor.toPlainText())
                    
                    # Mark document as not modified after saving
                    editor.document().setModified(False)
                    
                    # Show status message
                    self.statusBar().showMessage(f"Auto-saved: {os.path.basename(file_path)}", 2000)
                except Exception as e:
                    # Show error if auto-save fails
                    self.statusBar().showMessage(f"Auto-save failed: {str(e)}", 3000)
    
    def restore_settings(self):
        """Restore previously saved application settings"""
        # Restore font family
        font_family = self.settings.value("editor/font_family", "Inter")
        font_size = self.settings.value("editor/font_size", 12, type=int)
        tab_width = self.settings.value("editor/tab_width", 4, type=int)
        auto_save_interval = self.settings.value("editor/auto_save_interval", 0, type=int)
        preview_style = self.settings.value("markdown/preview_style", "Default")
        theme = self.settings.value("application/theme", "Neon Dark")
        
        # These methods will be called after initialization to apply saved settings
        QTimer.singleShot(0, lambda: [
            self.change_font_family(font_family),
            self.change_font_size(font_size),
            self.set_tab_width(tab_width),
            self.set_auto_save_interval(auto_save_interval),
            self.change_preview_style(preview_style),
            self.theme_manager.apply_theme(theme)
        ])
    
    def create_new_tab(self, file_path=None):
        """Create a new markdown editor tab"""
        editor = QTextEdit()
        editor.setFont(QFont("Fira Code", 10))
        
        # Add markdown highlighter
        MarkdownHighlighter(editor.document())
        
        # Connect text changed signal
        editor.textChanged.connect(self.update_preview)
        
        # Determine tab name
        if file_path:
            tab_name = os.path.basename(file_path)
            editor.setProperty("file_path", file_path)
        else:
            tab_name = "Untitled"
        
        # Add tab
        tab_index = self.editor_tabs.addTab(editor, tab_name)
        self.editor_tabs.setCurrentIndex(tab_index)
        
        return editor
    
    def current_editor(self):
        """Get the current active editor"""
        return self.editor_tabs.currentWidget()
    
    def close_tab(self, index):
        """Close a specific tab"""
        self.editor_tabs.removeTab(index)
        
        # Ensure at least one tab remains
        if self.editor_tabs.count() == 0:
            self.create_new_tab()
    
    def open_markdown_file(self, file_path):
        """Open a markdown file in the editor"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file is already open
            for i in range(self.editor_tabs.count()):
                editor = self.editor_tabs.widget(i)
                if editor.property("file_path") == file_path:
                    # Activate existing tab
                    self.editor_tabs.setCurrentIndex(i)
                    return
            
            # Create new tab and set content
            editor = self.create_new_tab(file_path)
            editor.setPlainText(content)
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
    
    def update_preview(self):
        """Convert markdown to HTML and update preview"""
        editor = self.current_editor()
        markdown_text = editor.toPlainText()
        
        # Use Pygments for code block syntax highlighting
        def highlight_code_blocks(match):
            code = match.group(1)
            language = match.group(2) or 'text'
            try:
                lexer = get_lexer_by_name(language)
                formatter = HtmlFormatter(noclasses=True, style='monokai')
                highlighted_code = pygments.highlight(code, lexer, formatter)
                return f'<pre>{highlighted_code}</pre>'
            except Exception:
                return f'<pre><code>{code}</code></pre>'
        
        # Markdown with code block highlighting
        code_block_pattern = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
        markdown_with_code = code_block_pattern.sub(highlight_code_blocks, markdown_text)
        
        html_content = markdown.markdown(markdown_with_code, extensions=['fenced_code', 'codehilite'])
        
        full_html = f"""
        <html>
        <head>
            <style>
                html, body {{ 
                    background-color: {NeonPalette.BACKGROUND_DARK} !important; 
                    color: {NeonPalette.TEXT_COLOR} !important; 
                    font-family: 'Inter UI', Arial, sans-serif; 
                    padding: 20px;
                    margin: 0;
                }}
                ::-webkit-scrollbar {{
                    width: 10px;
                    background-color: {NeonPalette.BACKGROUND_SECONDARY};
                }}
                ::-webkit-scrollbar-thumb {{
                    background-color: {NeonPalette.NEON_BLUE};
                    border-radius: 5px;
                }}
                pre {{ 
                    background-color: {NeonPalette.BACKGROUND_SECONDARY} !important; 
                    padding: 15px; 
                    border-radius: 5px; 
                    border: 1px solid {NeonPalette.NEON_BLUE};
                    overflow-x: auto;
                    color: {NeonPalette.TEXT_COLOR} !important;
                }}
                code {{ 
                    color: {NeonPalette.NEON_GREEN} !important; 
                    font-family: 'Fira Code', monospace; 
                    background-color: {NeonPalette.BACKGROUND_SECONDARY} !important;
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
                h1, h2, h3 {{ 
                    color: {NeonPalette.NEON_BLUE} !important; 
                    border-bottom: 1px solid {NeonPalette.NEON_BLUE};
                    padding-bottom: 0.3em;
                }}
                a {{ 
                    color: {NeonPalette.ACCENT_BLUE} !important; 
                    text-decoration: none; 
                }}
                a:hover {{ 
                    text-decoration: underline; 
                    color: {NeonPalette.NEON_BLUE} !important; 
                }}
                blockquote {{
                    border-left: 4px solid {NeonPalette.NEON_PURPLE};
                    padding-left: 10px;
                    color: {NeonPalette.TEXT_MUTED} !important;
                    font-style: italic;
                    background-color: {NeonPalette.BACKGROUND_SECONDARY} !important;
                }}
                p, li, td, th {{
                    color: {NeonPalette.TEXT_COLOR} !important;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        self.preview_view.setHtml(full_html)

    def generate_markdown_html(self, markdown_text, style='Default'):
        """
        Generate a stylized HTML rendering of markdown text with multiple style options
        """
        # Get current editor font
        current_editor = self.current_editor()
        current_font = current_editor.font()
        font_family = current_font.family()
        font_size = current_font.pointSize()
        
        # Base CSS for all styles
        base_css = f"""
        body {{
            font-family: '{font_family}', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-size: {font_size}pt;
        }}
        """
        
        # Style-specific CSS
        style_css = {
            'Default': """
            body {
                background-color: #121212;
                color: #e0e0e0;
            }
            h1, h2, h3, h4, h5, h6 { 
                color: #3498db; 
                border-bottom: 1px solid rgba(52, 152, 219, 0.2);
                padding-bottom: 0.3em;
            }
            a { color: #4ecdc4; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code { 
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                padding: 0.2em 0.4em;
            }
            pre { 
                background-color: #1e1e1e;
                border-radius: 6px;
                padding: 15px;
                overflow-x: auto;
            }
            blockquote {
                border-left: 4px solid #3498db;
                margin: 1.5em 0;
                padding-left: 15px;
                font-style: italic;
                color: #a0a0a0;
            }
            """,
            
            'Minimal': """
            body {
                background-color: #f4f4f4;
                color: #333;
                font-weight: 300;
            }
            h1, h2, h3, h4, h5, h6 { 
                color: #2c3e50; 
                font-weight: 300;
                border-bottom: 1px solid rgba(0,0,0,0.1);
            }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code { 
                background-color: rgba(0,0,0,0.05);
                border-radius: 3px;
                padding: 0.2em 0.4em;
                font-size: 0.9em;
            }
            pre { 
                background-color: #f8f8f8;
                border: 1px solid #e9e9e9;
                border-radius: 4px;
                padding: 15px;
            }
            blockquote {
                border-left: 3px solid #3498db;
                margin: 1.5em 0;
                padding-left: 15px;
                color: #777;
                font-style: italic;
            }
            """,
            
            'Academic': """
            body {
                background-color: #ffffff;
                color: #2c3e50;
                max-width: 700px;
            }
            h1, h2, h3, h4, h5, h6 { 
                color: #2980b9; 
                font-weight: 500;
                border-bottom: 1px solid rgba(41, 128, 185, 0.2);
                padding-bottom: 0.3em;
            }
            a { color: #2980b9; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code { 
                background-color: #f8f8f8;
                border: 1px solid #e9e9e9;
                border-radius: 3px;
                padding: 0.2em 0.4em;
                font-family: 'Courier New', monospace;
            }
            pre { 
                background-color: #f8f8f8;
                border: 1px solid #e9e9e9;
                border-radius: 4px;
                padding: 15px;
            }
            blockquote {
                border-left: 3px solid #2980b9;
                margin: 1.5em 0;
                padding-left: 15px;
                color: #666;
                font-style: italic;
            }
            """,
            
            'Modern': """
            body {
                background-color: #1a1a2e;
                color: #e0e0e0;
                font-weight: 300;
            }
            h1, h2, h3, h4, h5, h6 { 
                color: #4ecdc4; 
                font-weight: 400;
                border-bottom: 1px solid rgba(78, 205, 196, 0.2);
                padding-bottom: 0.3em;
            }
            a { color: #4ecdc4; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code { 
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                padding: 0.2em 0.4em;
                font-family: 'Fira Code', monospace;
            }
            pre { 
                background-color: #16213e;
                border-radius: 6px;
                padding: 15px;
                border: 1px solid rgba(78, 205, 196, 0.1);
            }
            blockquote {
                border-left: 4px solid #4ecdc4;
                margin: 1.5em 0;
                padding-left: 15px;
                color: #a0a0a0;
                font-style: italic;
            }
            """,
            
            'Classic': """
            body {
                background-color: #f5f5f5;
                color: #333;
                font-family: Georgia, serif;
                max-width: 750px;
            }
            h1, h2, h3, h4, h5, h6 { 
                color: #2c3e50; 
                font-family: 'Palatino Linotype', serif;
                border-bottom: 1px solid rgba(0,0,0,0.1);
                padding-bottom: 0.3em;
            }
            a { color: #2980b9; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code { 
                background-color: #f8f8f8;
                border: 1px solid #e9e9e9;
                border-radius: 3px;
                padding: 0.2em 0.4em;
                font-family: Consolas, monospace;
            }
            pre { 
                background-color: #f8f8f8;
                border: 1px solid #e9e9e9;
                border-radius: 4px;
                padding: 15px;
                font-family: Consolas, monospace;
            }
            blockquote {
                border-left: 3px solid #2980b9;
                margin: 1.5em 0;
                padding-left: 15px;
                color: #666;
                font-style: italic;
            }
            """
        }
        
        # Syntax Highlighting CSS
        syntax_css = """
        /* Syntax Highlighting */
        .highlight .k  { color: #ff79c6; }  /* Keyword */
        .highlight .kt { color: #8be9fd; }  /* Keyword Type */
        .highlight .n  { color: #f8f8f2; }  /* Name */
        .highlight .s  { color: #f1fa8c; }  /* String */
        .highlight .m  { color: #bd93f9; }  /* Number */
        .highlight .c  { color: #6272a4; }  /* Comment */
        .highlight .o  { color: #ff79c6; }  /* Operator */
        .highlight .p  { color: #f8f8f2; }  /* Punctuation */
        """
        
        # Combine CSS
        full_css = base_css + (style_css.get(style, style_css['Default']) + syntax_css)
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_text, 
            extensions=[
                'markdown.extensions.extra', 
                'markdown.extensions.codehilite', 
                'markdown.extensions.toc',
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code'
            ],
            extension_configs={
                'markdown.extensions.codehilite': {
                    'css_class': 'highlight',
                    'linenums': False,
                    'guess_lang': False
                }
            }
        )
        
        # Combine CSS and HTML content
        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>{full_css}</style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        return full_html
    
    def change_preview_style(self, style):
        """Change markdown preview style"""
        # Regenerate preview for all open tabs
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            markdown_text = editor.toPlainText()
            preview_html = self.generate_markdown_html(markdown_text, style)
            self.preview_view.setHtml(preview_html)
        
        # Persist preview style preference
        self.settings.setValue("markdown/preview_style", style)
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        # New File Action
        new_file_action = QAction("New", self)
        new_file_action.setShortcut("Ctrl+N")
        new_file_action.triggered.connect(self.create_new_tab)
        file_menu.addAction(new_file_action)
        
        # Open File Action
        open_file_action = QAction("Open", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)
        
        # Save File Action
        save_file_action = QAction("Save", self)
        save_file_action.setShortcut("Ctrl+S")
        save_file_action.triggered.connect(self.save_current_file)
        file_menu.addAction(save_file_action)
        
        # Save As Action
        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        # Close Tab Action
        close_tab_action = QAction("Close Tab", self)
        close_tab_action.setShortcut("Ctrl+W")
        close_tab_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_tab_action)
        
        # Exit Action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Theme Menu
        theme_menu = menubar.addMenu("&Theme")
        
        # Create theme actions
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        
        for theme_name in ThemeManager.THEMES.keys():
            theme_action = QAction(theme_name, self, checkable=True)
            theme_action.setChecked(theme_name == 'Neon Dark')  # Default theme
            theme_action.triggered.connect(
                lambda checked, name=theme_name: self.theme_manager.apply_theme(name)
            )
            theme_menu.addAction(theme_action)
            theme_group.addAction(theme_action)
        
        # Settings Menu
        settings_menu = menubar.addMenu("&Settings")
        
        # Editor Settings Submenu
        editor_settings_menu = settings_menu.addMenu("Editor")
        
        # Font Settings
        font_menu = editor_settings_menu.addMenu("Font")
        
        # Font Family
        font_family_group = QActionGroup(self)
        font_family_group.setExclusive(True)
        font_families = [
            "Inter", 
            "Fira Code", 
            "Roboto Mono", 
            "Source Code Pro", 
            "JetBrains Mono"
        ]
        for family in font_families:
            font_action = QAction(family, self, checkable=True)
            font_action.setChecked(family == "Inter")
            font_action.triggered.connect(
                lambda checked, f=family: self.change_font_family(f)
            )
            font_menu.addAction(font_action)
            font_family_group.addAction(font_action)
        
        # Font Size
        font_size_menu = editor_settings_menu.addMenu("Font Size")
        font_sizes = [10, 12, 14, 16, 18, 20]
        font_size_group = QActionGroup(self)
        font_size_group.setExclusive(True)
        for size in font_sizes:
            size_action = QAction(f"{size} pt", self, checkable=True)
            size_action.setChecked(size == 14)
            size_action.triggered.connect(
                lambda checked, s=size: self.change_font_size(s)
            )
            font_size_menu.addAction(size_action)
            font_size_group.addAction(size_action)
        
        # Line Spacing
        line_spacing_menu = editor_settings_menu.addMenu("Line Spacing")
        line_spacings = [1.0, 1.2, 1.5, 2.0]
        line_spacing_group = QActionGroup(self)
        line_spacing_group.setExclusive(True)
        for spacing in line_spacings:
            spacing_action = QAction(f"{spacing}x", self, checkable=True)
            spacing_action.setChecked(spacing == 1.5)
            spacing_action.triggered.connect(
                lambda checked, sp=spacing: self.change_line_spacing(sp)
            )
            line_spacing_menu.addAction(spacing_action)
            line_spacing_group.addAction(spacing_action)
        
        # Tab Settings
        tab_settings_menu = editor_settings_menu.addMenu("Tabs")
        
        # Tab Width
        tab_width_menu = tab_settings_menu.addMenu("Tab Width")
        tab_widths = [2, 4, 8]
        tab_width_group = QActionGroup(self)
        tab_width_group.setExclusive(True)
        for width in tab_widths:
            width_action = QAction(f"{width} spaces", self, checkable=True)
            width_action.setChecked(width == 4)
            width_action.triggered.connect(
                lambda checked, w=width: self.set_tab_width(w)
            )
            tab_width_menu.addAction(width_action)
            tab_width_group.addAction(width_action)
        
        # Markdown Settings Submenu
        markdown_settings_menu = settings_menu.addMenu("Markdown")
        
        # Preview Style
        preview_style_menu = markdown_settings_menu.addMenu("Preview Style")
        preview_styles = [
            "Default", 
            "Minimal", 
            "Academic", 
            "Modern", 
            "Classic"
        ]
        preview_style_group = QActionGroup(self)
        preview_style_group.setExclusive(True)
        for style in preview_styles:
            style_action = QAction(style, self, checkable=True)
            style_action.setChecked(style == "Default")
            style_action.triggered.connect(
                lambda checked, st=style: self.change_preview_style(st)
            )
            preview_style_menu.addAction(style_action)
            preview_style_group.addAction(style_action)
        
        # Auto Save Settings
        auto_save_menu = settings_menu.addMenu("Auto Save")
        auto_save_intervals = [
            ("Disabled", 0),
            ("5 Minutes", 5),
            ("10 Minutes", 10),
            ("15 Minutes", 15),
            ("30 Minutes", 30)
        ]
        auto_save_group = QActionGroup(self)
        auto_save_group.setExclusive(True)
        for label, interval in auto_save_intervals:
            auto_save_action = QAction(label, self, checkable=True)
            auto_save_action.setChecked(interval == 10)
            auto_save_action.triggered.connect(
                lambda checked, inv=interval: self.set_auto_save_interval(inv)
            )
            auto_save_menu.addAction(auto_save_action)
            auto_save_group.addAction(auto_save_action)
        
        # Preferences Action
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.open_preferences_dialog)
        settings_menu.addAction(preferences_action)
    
    def change_line_spacing(self, line_spacing):
        """Change editor line spacing"""
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            cursor_format = QTextBlockFormat()
            cursor_format.setLineHeight(
                line_spacing * 100, 
                QTextBlockFormat.LineDistancePercent
            )
            cursor = editor.textCursor()
            cursor.select(QTextCursor.Document)
            cursor.setBlockFormat(cursor_format)
            editor.setTextCursor(cursor)
    
    def set_auto_save_interval(self, interval):
        """Set auto save interval"""
        if interval > 0:
            self.status_update_timer.stop()
            self.status_update_timer.setInterval(interval * 60 * 1000)  # Convert to milliseconds
            self.status_update_timer.start()
        else:
            self.status_update_timer.stop()
    
    def open_preferences_dialog(self):
        """Open a comprehensive preferences dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Noteism Preferences")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Tabs for different preference sections
        tab_widget = QTabWidget()
        
        # Editor Tab
        editor_tab = QWidget()
        editor_layout = QFormLayout()
        
        # Font Selection
        font_combo = QComboBox()
        font_combo.addItems([
            "Inter", "Fira Code", "Roboto Mono", 
            "Source Code Pro", "JetBrains Mono"
        ])
        editor_layout.addRow("Font Family:", font_combo)
        
        # Font Size
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 32)
        font_size_spin.setValue(14)
        editor_layout.addRow("Font Size:", font_size_spin)
        
        # Line Spacing
        line_spacing_combo = QComboBox()
        line_spacing_combo.addItems(["1.0x", "1.2x", "1.5x", "2.0x"])
        line_spacing_combo.setCurrentText("1.5x")
        editor_layout.addRow("Line Spacing:", line_spacing_combo)
        
        editor_tab.setLayout(editor_layout)
        tab_widget.addTab(editor_tab, "Editor")
        
        # Markdown Tab
        markdown_tab = QWidget()
        markdown_layout = QFormLayout()
        
        # Preview Style
        preview_style_combo = QComboBox()
        preview_style_combo.addItems([
            "Default", "Minimal", "Academic", "Modern", "Classic"
        ])
        markdown_layout.addRow("Preview Style:", preview_style_combo)
        
        markdown_tab.setLayout(markdown_layout)
        tab_widget.addTab(markdown_tab, "Markdown")
        
        # Auto Save Tab
        autosave_tab = QWidget()
        autosave_layout = QFormLayout()
        
        # Auto Save Interval
        autosave_combo = QComboBox()
        autosave_combo.addItems([
            "Disabled", "5 Minutes", "10 Minutes", 
            "15 Minutes", "30 Minutes"
        ])
        autosave_layout.addRow("Auto Save Interval:", autosave_combo)
        
        autosave_tab.setLayout(autosave_layout)
        tab_widget.addTab(autosave_tab, "Auto Save")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def open_file(self):
        """Open an existing markdown file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Markdown File", 
            self.current_root,  # Use the markdown directory as default
            "Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            # Check if file is already open
            for i in range(self.editor_tabs.count()):
                editor = self.editor_tabs.widget(i)
                if editor.property("file_path") == file_path:
                    # Activate existing tab
                    self.editor_tabs.setCurrentIndex(i)
                    return
            
            # Read file contents
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Create new tab
                editor = self.create_new_tab()
                editor.setPlainText(content)
                
                # Set file path as a property of the editor
                editor.setProperty("file_path", file_path)
                
                # Add tab with filename and full path as tooltip
                tab_index = self.editor_tabs.addTab(
                    editor, 
                    os.path.basename(file_path)
                )
                self.editor_tabs.setTabToolTip(tab_index, file_path)
                
                # Set current tab
                self.editor_tabs.setCurrentIndex(tab_index)
            
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Could not open file: {str(e)}"
                )
    
    def save_current_file(self):
        """Save the current file"""
        current_index = self.editor_tabs.currentIndex()
        if current_index == -1:
            return
        
        current_editor = self.editor_tabs.widget(current_index)
        current_file_path = self.editor_tabs.tabToolTip(current_index)
        
        if current_file_path:
            # Existing file, save directly
            try:
                with open(current_file_path, 'w', encoding='utf-8') as file:
                    file.write(current_editor.toPlainText())
                
                # Update tab name to reflect saved state
                self.editor_tabs.setTabText(
                    current_index, 
                    os.path.basename(current_file_path)
                )
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Could not save file: {str(e)}"
                )
        else:
            # No existing file, call save as
            self.save_file_as()
    
    def save_file_as(self):
        """Save the current file with a new name"""
        current_index = self.editor_tabs.currentIndex()
        if current_index == -1:
            return
        
        current_editor = self.editor_tabs.widget(current_index)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Markdown File", 
            os.path.join(self.current_root, "new_file.md"),
            "Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            # Ensure .md extension
            if not file_path.lower().endswith('.md'):
                file_path += '.md'
            
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(current_editor.toPlainText())
                
                # Update tab with new filename and path
                self.editor_tabs.setTabText(
                    current_index, 
                    os.path.basename(file_path)
                )
                self.editor_tabs.setTabToolTip(current_index, file_path)
            
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Could not save file: {str(e)}"
                )
    
    def close_current_tab(self):
        """Close the current tab"""
        current_index = self.editor_tabs.currentIndex()
        if current_index != -1:
            # Check if file is modified
            current_editor = self.editor_tabs.widget(current_index)
            
            # If the file has unsaved changes, prompt for save
            if current_editor.document().isModified():
                reply = QMessageBox.question(
                    self, 
                    'Save Changes', 
                    'Do you want to save changes before closing?',
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    self.save_current_file()
                elif reply == QMessageBox.Cancel:
                    return
            
            # Close the tab
            self.editor_tabs.removeTab(current_index)
    
    def create_toolbar(self):
        toolbar = QToolBar("Markdown Formatting")
        self.addToolBar(toolbar)
        
        # Text Formatting
        bold_action = QAction("Bold", self)
        bold_action.triggered.connect(lambda: MarkdownToolbar.bold(self.current_editor()))
        toolbar.addAction(bold_action)
        
        italic_action = QAction("Italic", self)
        italic_action.triggered.connect(lambda: MarkdownToolbar.italic(self.current_editor()))
        toolbar.addAction(italic_action)
        
        strikethrough_action = QAction("Strikethrough", self)
        strikethrough_action.triggered.connect(lambda: MarkdownToolbar.strikethrough(self.current_editor()))
        toolbar.addAction(strikethrough_action)
        
        inline_code_action = QAction("Inline Code", self)
        inline_code_action.triggered.connect(lambda: MarkdownToolbar.code_inline(self.current_editor()))
        toolbar.addAction(inline_code_action)
        
        toolbar.addSeparator()
        
        # Headings
        for i in range(1, 4):
            heading_action = QAction(f"H{i}", self)
            heading_action.triggered.connect(
                lambda checked, level=i: MarkdownToolbar.insert_heading(self.current_editor(), level)
            )
            toolbar.addAction(heading_action)
        
        toolbar.addSeparator()
        
        # Lists
        unordered_list_action = QAction("Unordered List", self)
        unordered_list_action.triggered.connect(lambda: MarkdownToolbar.insert_list(self.current_editor(), ordered=False))
        toolbar.addAction(unordered_list_action)
        
        ordered_list_action = QAction("Ordered List", self)
        ordered_list_action.triggered.connect(lambda: MarkdownToolbar.insert_list(self.current_editor(), ordered=True))
        toolbar.addAction(ordered_list_action)
        
        toolbar.addSeparator()
        
        # Insert Tools
        link_action = QAction("Insert Link", self)
        link_action.triggered.connect(lambda: MarkdownToolbar.insert_link(self.current_editor()))
        toolbar.addAction(link_action)
        
        code_block_action = QAction("Code Block", self)
        code_block_action.triggered.connect(lambda: MarkdownToolbar.insert_code_block(self.current_editor()))
        toolbar.addAction(code_block_action)
        
        table_action = QAction("Insert Table", self)
        table_action.triggered.connect(lambda: MarkdownToolbar.insert_table(self.current_editor()))
        toolbar.addAction(table_action)
        
        task_list_action = QAction("Insert Task List", self)
        task_list_action.triggered.connect(lambda: MarkdownToolbar.insert_task_list(self.current_editor()))
        toolbar.addAction(task_list_action)
        
        footnote_action = QAction("Insert Footnote", self)
        footnote_action.triggered.connect(lambda: MarkdownToolbar.insert_footnote(self.current_editor()))
        toolbar.addAction(footnote_action)
        
        horizontal_rule_action = QAction("Insert Horizontal Rule", self)
        horizontal_rule_action.triggered.connect(lambda: MarkdownToolbar.insert_horizontal_rule(self.current_editor()))
        toolbar.addAction(horizontal_rule_action)
        
        blockquote_action = QAction("Insert Blockquote", self)
        blockquote_action.triggered.connect(lambda: MarkdownToolbar.insert_blockquote(self.current_editor()))
        toolbar.addAction(blockquote_action)

    def create_status_bar(self):
        status_bar = self.statusBar()
        
        # Document Statistics
        self.file_format_label = QLabel("Format: Markdown")
        self.file_size_label = QLabel("Size: 0 bytes")
        self.word_count_label = QLabel("Words: 0")
        self.line_count_label = QLabel("Lines: 0")
        self.cursor_pos_label = QLabel("Pos: 0, 0")
        self.char_count_label = QLabel("Chars: 0")
        
        status_bar.addPermanentWidget(self.file_format_label)
        status_bar.addPermanentWidget(self.file_size_label)
        status_bar.addPermanentWidget(self.word_count_label)
        status_bar.addPermanentWidget(self.line_count_label)
        status_bar.addPermanentWidget(self.cursor_pos_label)
        status_bar.addPermanentWidget(self.char_count_label)
        
        # Update status periodically
        self.status_update_timer = QTimer(self)
        self.status_update_timer.timeout.connect(self.update_status)
        self.status_update_timer.start(1000)  # Update every second
        
    def update_status(self):
        """Update document statistics in status bar"""
        text = self.current_editor().toPlainText()
        cursor = self.current_editor().textCursor()
        
        self.file_size_label.setText(f"Size: {len(text)} bytes")
        self.word_count_label.setText(f"Words: {len(text.split())}")
        self.line_count_label.setText(f"Lines: {text.count(chr(10)) + 1}")
        self.cursor_pos_label.setText(
            f"Pos: {cursor.blockNumber() + 1}, {cursor.columnNumber()}"
        )
        self.char_count_label.setText(f"Chars: {len(text)}")
        
def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Inter UI", 10)
    app.setFont(font)
    
    editor = NoteismMarkdownEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
