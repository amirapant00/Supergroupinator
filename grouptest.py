import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QListWidgetItem
from PyQt5.uic import loadUi
import random
from fpdf import FPDF

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        # Load the UI file
        loadUi(r"C:\Users\biksn\OneDrive\Documents\computer\CS 460\practice\main.ui", self)

        # Initialize a dictionary to hold class and student data
        self.classes = {}

        self.tabWidget.setCurrentIndex(0)

        # Connect buttons and actions
        self.manageClassButton.clicked.connect(self.go_to_manage_classes)
        self.createClassButton.clicked.connect(self.go_to_new_class)
        self.uploadFileButton.clicked.connect(self.upload_file)
        self.createClassButton_2.clicked.connect(self.create_class)
        self.viewClassButton.clicked.connect(self.view_class)  # Button for viewing a class
        self.deleteClassButton.clicked.connect(self.delete_class)  # Button for deleting a class
        self.addStudentButton.clicked.connect(self.add_student)  # Button to add a student
        self.removeStudentButton.clicked.connect(self.remove_student)  # Button to remove a student
        self.saveClassButton.clicked.connect(self.save_class) #Button to save class after making changes
        self.selectClassCombo.currentIndexChanged.connect(self.update_student_list) # Connect the combo box to the update method
        self.createGroupsButton.clicked.connect(self.on_create_groups_button_clicked)
        self.exportGroupsButton.clicked.connect(self.export_groups_to_pdf)

        self.tabWidget.currentChanged.connect(self.on_tab_changed)

        self.classList.itemClicked.connect(self.select_class)

        # Initialize variables to track selected class
        self.selected_class = None

    def go_to_manage_classes(self):
        """Switch to the 'Manage Classes' tab."""
        self.tabWidget.setCurrentWidget(self.manageClass)

    def go_to_new_class(self):
        """Switch to the 'New Class' tab."""
        self.tabWidget.setCurrentWidget(self.newClass)

    def upload_file(self):
        """Handle file upload for student names."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Student List File", "", "CSV Files (*.csv);;Text Files (*.txt)"
        )
        if file_name:
            self.fileNameLabel.setText(file_name)
            self.load_students_from_file(file_name)

    def load_students_from_file(self, file_name):
        """Load students from a given file into the student list."""
        try:
            with open(file_name, 'r') as file:
                students = [student.strip() for student in file.readlines()]
            self.studentList.addItems(students)
        except Exception as e:
            print(f"Error loading file: {e}")

    def create_class(self):
        """Handle creating a new class."""
        class_name = self.classNameInput.text()
        file_path = self.fileNameLabel.text()

        if not class_name:
            QMessageBox.warning(self, "Missing Class Name", "Please enter a class name!")
            return

        if file_path == "No file selected": # not file_path.strip():
            QMessageBox.warning(self, "Missing File", "Please upload a student list file!")
            return

        if class_name in self.classes:
            QMessageBox.warning(self, "Duplicate Class", f"Class '{class_name}' already exists!")
            return

        try:
            # Read students from the selected file
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                students = [student.strip() for student in file.readlines()]

            # Save class and student list in the dictionary
            self.classes[class_name] = students

            # Add class name to classList Widget
            self.classList.addItem(class_name)
            self.update_class_combo_box()

            # Clear input fields
            self.classNameInput.clear()
            self.fileNameLabel.setText("No file selected")
            self.studentList.clear()

            # Confirmation dialog
            QMessageBox.information(self, "Class Created", f"Class '{class_name}' has been successfully created!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create class: {e}")

    def view_class(self):
        """View the selected class and populate its students."""
        if self.selected_class:
            self.studentList.clear()
            students = self.classes[self.selected_class]
         #  self.studentList.clear()
            self.studentList.addItems(students)
        else:
            QMessageBox.warning(self, "No Class Selected", "Please select a class to view!")

    def delete_class(self):
        """Delete the selected class."""
        if self.selected_class:
            confirm = QMessageBox.question(
                self, "Confirm Delete", f"Are you sure you want to delete '{self.selected_class}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                del self.classes[self.selected_class]
                self.classList.clear()
                self.classList.addItems(self.classes.keys())
                self.update_class_combo_box() #updates combo box so it doesn't show deleted class
                self.studentList.clear()
                self.selected_class = None
        else:
            QMessageBox.warning(self, "No Class Selected", "Please select a class to delete!")

    def add_student(self):
        """Add a student to the selected class."""
        if self.selected_class:
            student_name = self.studentNameInput.text()
            if student_name:
                self.classes[self.selected_class].append(student_name)
                self.studentList.addItem(student_name)
                self.studentNameInput.clear()
            else:
                QMessageBox.warning(self, "Invalid Input", "Student name cannot be empty!")
        else:
            QMessageBox.warning(self, "No Class Selected", "Please select a class to add a student!")

    def remove_student(self):
        """Remove a selected student from the current class."""
        if self.selected_class:
            selected_item = self.studentList.currentItem()
            if selected_item:
                student_name = selected_item.text()

                # Confirm deletion
                confirm = QMessageBox.question(
                    self, "Confirm Deletion", f"Are you sure you want to delete '{student_name}'?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if confirm == QMessageBox.Yes:
                    # Remove student from the list
                    self.classes[self.selected_class].remove(student_name)

                    # Also remove the student from the displayed list
                    self.studentList.takeItem(self.studentList.row(selected_item))

                    # Display confirmation message
                    QMessageBox.information(self, "Student Removed", f"'{student_name}' has been removed from the class.")
            else:
                QMessageBox.warning(self, "No Student Selected", "Please select a student to remove!")
        else:
            QMessageBox.warning(self, "No Class Selected", "Please select a class to remove a student!")

    def save_class(self):
        """Save the updated class list (in-memory only)."""
        if self.selected_class:
            # Inform the user that changes are saved in memory
            QMessageBox.information(self, "Class Saved", f"Class '{self.selected_class}' changes have been saved!")

    def select_class(self, item):
        """Track the selected class."""
        self.selected_class = item.text()
        self.studentList.clear()

    def update_student_list(self):
        """Update the student list in ClassList_2 when a class is selected from the combo box."""
        selected_class = self.selectClassCombo.currentText()  # Get selected class name
        self.studentList_2.clear()
        
        if selected_class:  # If a class is selected
            # Get the list of students for the selected class
            students = self.classes.get(selected_class, [])
            
            # Clear current list
            self.classList_2.clear()
            
            # Add the students to the ClassList_2 widget
            if students:
                self.classList_2.addItems(students)
            else:
                self.ClassList_2.addItem("No students in this class.")
        else:
            # If no class is selected, clear the list
            self.classList_2.clear()

    def update_class_combo_box(self):
        """Update the combo box with the current list of class names."""
        self.selectClassCombo.clear()  # Clear the combo box first
        # Add all class names in the current classes dictionary
        self.selectClassCombo.addItems(self.classes.keys())

    def create_groups(self, students, group_size):
        """Randomly assigns students into groups of specified size."""
        # Shuffle the student list to ensure randomness
        shuffled_students = students[:]
        random.shuffle(shuffled_students)

        # Split the shuffled list into groups of the specified size
        groups = [shuffled_students[i:i + group_size] for i in range(0, len(shuffled_students), group_size)]
        
        #distribute leftovers 
        if len(groups[-1]) < group_size and len(groups) > 1:
            leftovers = groups.pop()  # Get the last group
            for i, student in enumerate(leftovers):
                groups[i % len(groups)].append(student)
        
        return groups

    def on_create_groups_button_clicked(self):
        """Handles the click event for the Create Groups button."""
        # Get the selected class from the combo box
        selected_class = self.selectClassCombo.currentText()

        # Ensure a class is selected
        if not selected_class:
            QMessageBox.warning(self, "No Class Selected", "Please select a class from the dropdown.")
            return

        # Retrieve the student list for the selected class
        students = self.classes.get(selected_class, [])

        # Ensure there are students in the class
        if not students:
            QMessageBox.warning(self, "No Students", f"No students found for class '{selected_class}'.")
            return

        # Get the number of students per group from the spin box
        group_size = self.spinStudentsGroups.value()

        # Ensure a valid group size is selected
        if group_size == 0:
            QMessageBox.warning(self, "Invalid Group Size", "Please select a valid number of students per group.")
            return

        # Create the groups using the function
        groups = self.create_groups(students, group_size)

        # Clear the current list in the widget before displaying the new groups
        self.studentList_2.clear()

        # Display the groups in the studentList_2 widget
        for i, group in enumerate(groups, start=1):
            group_text = f"Group {i}: {', '.join(group)}"
            self.studentList_2.addItem(group_text)

        # Optionally, you can show a success dialog
        QMessageBox.information(self, "Groups Created", f"Successfully created {len(groups)} groups!")

    def export_groups_to_pdf(self):
        """Exports the created groups to a PDF file using fpdf."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Groups as PDF", "", "PDF Files (*.pdf)")
        if not file_name:
            return  # User canceled save dialog

        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", style='B', size=16)
            pdf.cell(200, 10, "Student Groups", ln=True, align='C')
            pdf.ln(10)

            pdf.set_font("Arial", size=12)
            for i in range(self.studentList_2.count()):
                group_text = self.studentList_2.item(i).text()
                pdf.multi_cell(0, 10, group_text)
                pdf.ln(5)

            pdf.output(file_name)
            QMessageBox.information(self, "Export Successful", "Groups have been exported to PDF successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred while exporting: {e}")

    def on_tab_changed(self, index):
        """Handle actions when tabs are changed."""
        current_tab = self.tabWidget.widget(index)

        #also clear student list
        self.studentList.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
