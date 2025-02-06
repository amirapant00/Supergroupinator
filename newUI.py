import sys
import os
import sqlite3
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem, 
    QInputDialog, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QHeaderView
)
from PyQt5.uic import loadUi
from PyQt5.QtGui import QColor

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(r"C:\Users\biksn\OneDrive\Documents\computer\CS 460\Testing new ui\newUI.ui", self)

        self.db_folder = os.path.join(os.getcwd(), "class_databases")
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)
        
        self.current_db = None
        self.tabWidget.setCurrentIndex(0)
        
        self.createClassButton.clicked.connect(self.create_new_class)
        self.manageClassButton.clicked.connect(self.open_class)
        self.addStudentButton.clicked.connect(self.add_student)
        self.removeStudentButton.clicked.connect(self.remove_student)
        self.searchButton.clicked.connect(self.search_student)
        self.exportClassButton.clicked.connect(self.export_to_csv)
        self.classTable.itemSelectionChanged.connect(self.highlight_row)
        self.classTable.itemChanged.connect(self.update_student_info)
        self.clearButton.clicked.connect(self.clear_search)
        self.undo_stack = []  # Stack to keep track of changes for undo

    def create_new_class(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Class")
        layout = QVBoxLayout()
        
        name_label = QLabel("Class Name:")
        name_input = QLineEdit()
        
        button_box = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        button_box.clicked.connect(lambda: self.process_new_class(dialog, name_input.text()))
        cancel_button.clicked.connect(dialog.reject)
        
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        layout.addWidget(button_box)
        layout.addWidget(cancel_button)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def process_new_class(self, dialog, class_name):
        if not class_name.strip():
            QMessageBox.warning(self, "Invalid Input", "Class name cannot be empty.")
            return
        
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Student List File", "", "CSV Files (*.csv)")
        if not file_name:
            return
        
        db_name = os.path.join(self.db_folder, f"{class_name}.db")
        self.current_db = db_name
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT,
                strength TEXT
            )
        """)
        
        with open(file_name, 'r', encoding='utf-8-sig') as file:
            csv_reader = csv.reader(file)
            students = [(row[0],) for row in csv_reader if row]
        cursor.executemany("INSERT INTO students (name) VALUES (?)", students)
        conn.commit()
        conn.close()
        
        self.load_class(class_name, db_name)
        self.tabWidget.setCurrentIndex(1)  # Switch to Manage Classes tab
        dialog.accept()
        QMessageBox.information(self, "Success", f"Class '{class_name}' has been created and loaded!")

    def open_class(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Class Database", self.db_folder, "Database Files (*.db)")
        if not file_name:
            return
        class_name = os.path.basename(file_name).replace(".db", "")
        self.load_class(class_name, file_name)
        self.tabWidget.setCurrentIndex(1)  # Switch to Manage Classes tab

    def load_class(self, class_name, db_path):
        self.className.setText(class_name)
        self.current_db = db_path
        self.classTable.clear()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(students)")
        columns = [col[1] for col in cursor.fetchall()]
        
        self.classTable.setColumnCount(len(columns))
        self.classTable.setHorizontalHeaderLabels(["ID", "Student Name", "Gender", "Strength"])
        
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        self.classTable.setRowCount(len(students))
        
        for row_idx, row_data in enumerate(students):
            for col_idx, col_data in enumerate(row_data):
                if col_idx == 2:
                    combo = QComboBox()
                    combo.addItems(["Male", "Female"])
                    combo.setCurrentText(col_data)
                    combo.currentIndexChanged.connect(lambda index, r=row_idx, c=col_idx: self.update_combo_value(r, c))
                    self.classTable.setCellWidget(row_idx, col_idx, combo)
                elif col_idx == 3:
                    combo = QComboBox()
                    combo.addItems(["Strong", "Average", "Weak"])
                    combo.setCurrentText(col_data)
                    combo.currentIndexChanged.connect(lambda index, r=row_idx, c=col_idx: self.update_combo_value(r, c))
                    self.classTable.setCellWidget(row_idx, col_idx, combo)
                else:
                    self.classTable.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
        
        self.classTable.setColumnHidden(0, True)  # Hide the ID column
        self.classTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        conn.close()

    def search_student(self):
        search_text = self.lineEdit.text().strip().lower()
        found = False  # Track if any row matches the search

        for row in range(self.classTable.rowCount()):
            item = self.classTable.item(row, 1)  # Assuming column 1 is "Student Name"
            match = item and search_text in item.text().lower()
            self.classTable.setRowHidden(row, not match)
            if match:
                found = True

        if not found:
            QMessageBox.information(self, "No Results", f"No student found with '{search_text}'")
            self.clear_search()

    def clear_search(self):
        self.lineEdit.clear()  # Clear search field
        for row in range(self.classTable.rowCount()):
            self.classTable.setRowHidden(row, False)  # Show all rows again
        
    def highlight_row(self):
        for row in range(self.classTable.rowCount()):
            for col in range(self.classTable.columnCount()):
                item = self.classTable.item(row, col)
                if item:
                    item.setBackground(QColor("white"))
        
        for item in self.classTable.selectedItems():
            item.setBackground(QColor("blue"))

    def export_to_csv(self):
        if not self.current_db:
            QMessageBox.warning(self, "No Class Loaded", "Please load a class first.")
            return
        
        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not file_name:
            return
        
        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students")
        rows = cursor.fetchall()
        conn.close()
        
        with open(file_name, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([desc[0] for desc in cursor.description])
            writer.writerows(rows)
        QMessageBox.information(self, "Export Successful", "Class data exported successfully!")

    def add_student(self):
        if not self.current_db:
            QMessageBox.warning(self, "No Class Loaded", "Please load a class first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Student")
        layout = QVBoxLayout()

        name_label = QLabel("Student Name:")
        name_input = QLineEdit()

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_new_student(dialog, name_input.text()))

        layout.addWidget(name_label)
        layout.addWidget(name_input)
        layout.addWidget(save_button)
        dialog.setLayout(layout)
        dialog.exec_()

    def save_new_student(self, dialog, name):
        if not name.strip():
            QMessageBox.warning(self, "Invalid Input", "Student name cannot be empty.")
            return

        # Store current state for undo
        self.save_current_state()

        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students ('name') VALUES (?)", (name,))
        conn.commit()
        conn.close()

        self.load_class(self.className.text(), self.current_db)
        dialog.accept()

    def remove_student(self):
        selected_row = self.classTable.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Selection", "Please select a student to remove.")
            return

        student_id = self.classTable.item(selected_row, 0).text()

        # Store current state for undo
        self.save_current_state()

        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE ID = ?", (student_id,))
        conn.commit()

        # Renumber IDs
        cursor.execute("SELECT ID FROM students ORDER BY ID")
        ids = [row[0] for row in cursor.fetchall()]
        for new_id, old_id in enumerate(ids, start=1):
            cursor.execute("UPDATE students SET ID = ? WHERE ID = ?", (new_id, old_id))
        conn.commit()
        conn.close()

        self.load_class(self.className.text(), self.current_db)

    def update_student_info(self, item):
        if not self.current_db:
            return

        row = item.row()
        col = item.column()

        # Get column names dynamically
        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(students)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()

        if col == 0:  # Ignore changes to the ID column
            return

        student_id = self.classTable.item(row, 0).text()  # ID is in column 0
        new_value = item.text()
        column_name = columns[col]

        # Store current state for undo
        self.save_current_state()

        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        query = f"UPDATE students SET '{column_name}' = ? WHERE ID = ?"
        cursor.execute(query, (new_value, student_id))
        conn.commit()
        conn.close()

    def update_combo_value(self, row, col):
        if not self.current_db:
            return

        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(students)")
        columns = [col[1] for col in cursor.fetchall()]

        student_id = self.classTable.item(row, 0).text()  # ID is in column 0
        combo_box = self.classTable.cellWidget(row, col)
        new_value = combo_box.currentText()
        column_name = columns[col]

        # Store current state for undo
        self.save_current_state()

        query = f"UPDATE students SET '{column_name}' = ? WHERE ID = ?"
        cursor.execute(query, (new_value, student_id))
        conn.commit()
        conn.close()

    def save_current_state(self):
        """Save the current state before making any modifications."""
        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students")
        data = cursor.fetchall()
        conn.close()
        self.undo_stack.append(data)  # Store the current table data

    def undo_last_action(self):
        """Undo the last modification."""
        if not self.undo_stack:
            QMessageBox.warning(self, "Undo", "No previous state to revert to.")
            return

        # Restore the last saved state
        previous_state = self.undo_stack.pop()
        conn = sqlite3.connect(self.current_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students")  # Clear current data

        for row in previous_state:
            cursor.execute("INSERT INTO students VALUES (?, ?, ?, ?)", row)

        conn.commit()
        conn.close()

        self.load_class(self.className.text(), self.current_db)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
