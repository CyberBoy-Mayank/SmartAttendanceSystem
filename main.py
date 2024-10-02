import os
import csv
import shutil  # To delete a directory and its contents
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw, ImageFont
import tempfile
import win32api


class SmartAttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance System")

        # Set minimum window size to ensure responsiveness
        self.root.minsize(800, 500)

        # Create the top frame for Operations
        self.operations_frame = ttk.LabelFrame(self.root, text="Operations")
        self.operations_frame.pack(side=tk.TOP, fill=tk.X, expand=False, padx=10, pady=10)

        # Configure the grid to stretch widgets in the operations frame
        self.operations_frame.columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10), weight=1)

        # ID Label and Entry
        self.id_label = ttk.Label(self.operations_frame, text="ID:")
        self.id_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        vcmd_id = (root.register(self.validate_id), '%P')  # Validate ID (digits only)
        self.id_entry = ttk.Entry(self.operations_frame, validate='key', validatecommand=vcmd_id)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Name Label and Entry
        self.name_label = ttk.Label(self.operations_frame, text="Name:")
        self.name_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        vcmd_name = (root.register(self.validate_name), '%P')  # Validate Name (alphabets only)
        self.name_entry = ttk.Entry(self.operations_frame, validate='key', validatecommand=vcmd_name)
        self.name_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Capture Button (disabled by default)
        self.capture_button = ttk.Button(self.operations_frame, text="Capture", state=tk.DISABLED,
                                         command=self.capture_data)
        self.capture_button.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        # Mark Attendance Button
        self.mark_button = ttk.Button(self.operations_frame, text="Mark Attendance", command=self.mark_attendance)
        self.mark_button.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        # # Combobox for selecting attendance CSV file
        # self.attendance_combobox = ttk.Combobox(self.operations_frame, state="readonly")
        # self.attendance_combobox.grid(row=0, column=6, padx=5, pady=5, sticky="ew")
        # self.attendance_combobox.bind("<<ComboboxSelected>>", self.load_attendance_data)

        # Combobox for selecting attendance CSV file
        self.attendance_combobox = ttk.Combobox(self.operations_frame, state="readonly")
        self.attendance_combobox.grid(row=0, column=6, padx=5, pady=5, sticky="ew")
        self.attendance_combobox.bind("<<ComboboxSelected>>", self.load_attendance_data)


        # Show All Button
        self.show_all_button = ttk.Button(self.operations_frame, text="Show All", command=self.show_all_data)
        self.show_all_button.grid(row=0, column=7, padx=5, pady=5, sticky="ew")

        # Delete Button (disabled by default)
        self.delete_button = ttk.Button(self.operations_frame, text="Delete", state=tk.DISABLED,
                                        command=self.delete_record)
        self.delete_button.grid(row=0, column=8, padx=5, pady=5, sticky="ew")

        # Print Button
        self.print_button = ttk.Button(self.operations_frame, text="Print", command=self.print_data)
        self.print_button.grid(row=0, column=9, padx=5, pady=5, sticky="ew")

        # Exit Button
        self.exit_button = ttk.Button(self.operations_frame, text="Exit", command=self.exit_application)
        self.exit_button.grid(row=0, column=10, padx=5, pady=5, sticky="ew")

        # Create the bottom frame for Data
        self.data_frame = ttk.LabelFrame(self.root, text="Data")
        self.data_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create Treeview with Scrollbars in Data frame
        self.tree_frame = ttk.Frame(self.data_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        self.v_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.h_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.treeview = ttk.Treeview(self.tree_frame, columns=("ID", "Name", "Time"),
                                     show='headings', yscrollcommand=self.v_scrollbar.set,
                                     xscrollcommand=self.h_scrollbar.set)
        self.treeview.pack(fill=tk.BOTH, expand=True)

        self.v_scrollbar.config(command=self.treeview.yview)
        self.h_scrollbar.config(command=self.treeview.xview)

        self.treeview.heading("ID", text="ID")
        self.treeview.heading("Name", text="Name")
        self.treeview.heading("Time", text="Time")

        # Bind Treeview select event to enable Delete button
        self.treeview.bind("<<TreeviewSelect>>", self.on_treeview_select)

        self.load_today_attendance()

        # Start refreshing the combobox and treeview
        self.refresh_combobox()

        # Schedule the combobox to refresh every 5 seconds (5000 ms)
        self.auto_update_combobox()


    def refresh_combobox(self):
        """Refresh attendance dates in the combobox."""
        self.attendance_dates = ["Select Day"] + self.get_attendance_dates()
        self.attendance_combobox['values'] = self.attendance_dates
        self.attendance_combobox.current(0)

    def auto_update_combobox(self):
        """Automatically update the combobox every few seconds."""
        self.refresh_combobox()
        self.root.after(5000, self.auto_update_combobox)  # Refresh every 5 seconds


    def check_id_exists(self, entered_id):
        """Check if the entered ID already exists in names.csv."""
        try:
            with open('names.csv', newline='') as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                for row in reader:
                    existing_id = row[0].strip()  # Get the ID from each row
                    if existing_id == entered_id:
                        return True  # ID already exists
        except FileNotFoundError:
            messagebox.showerror("Error", "names.csv file not found")
        return False  # ID does not exist

    def capture_data(self):
        """Capture the data if the ID does not already exist."""
        entered_id = self.id_entry.get()
        entered_name = self.name_entry.get()

        # Check if the ID already exists in names.csv
        if self.check_id_exists(entered_id):
            messagebox.showwarning("Duplicate ID", f"ID {entered_id} already exists. Please use a different ID.")
        else:
            # Create an instance of FaceCapture with the entered ID and Name
            try:
                import add_faces
                fc = add_faces.FaceCapture(user_id=entered_id, user_name=entered_name)
                fc.capture_faces()  # Start face capturing process

                # After the face capture completes, show a confirmation dialog
                keep_data = messagebox.askyesno("Keep Captured Data",
                                                "Face capture completed successfully! Would you like to keep the captured faces for training?")

                if not keep_data:
                    # If the user selects 'No', delete the directory and remove the entry from names.csv
                    face_dir = f"Faces/{entered_id}_{entered_name}"
                    shutil.rmtree(face_dir)  # Delete the face directory

                    self.remove_record_from_csv('names.csv', entered_id, entered_name)  # Remove the ID/Name from CSV
                    messagebox.showinfo("Data Deleted", "ID, name, and captured faces have been deleted.")
                else:
                    import train_model
                    try:
                        trainer = train_model.Trainer()
                        trainer.train_faces()
                    except Exception as e:
                        messagebox.showwarning("Unsuccessful", f"Model doesn't train du to: {e}")
                    messagebox.showinfo("Data Saved", "Captured data has been saved for model training.")
            except Exception as e:
                messagebox.showerror("Error", f"Face capture failed: {e}")

        # Clear entry fields after successful capture and training
        self.id_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)

    def validate_id(self, new_value):
        """Allow only digits for the ID field."""
        if new_value.isdigit() or new_value == "":
            self.check_fields()  # Check if both fields are filled to enable Capture button
            return True
        return False

    def validate_name(self, new_value):
        """Allow only alphabetic characters for the Name field."""
        if new_value.isalpha() or new_value == "":
            self.check_fields()  # Check if both fields are filled to enable Capture button
            return True
        return False

    def check_fields(self):
        """Enable the Capture button when both fields are filled."""
        id_filled = self.id_entry.get().isdigit() and len(self.id_entry.get()) > 0
        name_filled = self.name_entry.get().isalpha() and len(self.name_entry.get()) > 0
        if id_filled and name_filled:
            self.capture_button.config(state=tk.NORMAL)
        else:
            self.capture_button.config(state=tk.DISABLED)

    def get_attendance_dates(self):
        """Fetch CSV filenames in 'attendance' directory and return dates (yyyy-mm-dd)."""
        if not os.path.exists('attendance'):
            os.makedirs('attendance')
        return [filename.replace('.csv', '') for filename in os.listdir('attendance') if filename.endswith('.csv')]

    def load_attendance_data(self, event):
        """Load attendance data from the selected CSV file into the Treeview."""
        selected_date = self.attendance_combobox.get()
        if selected_date != "Select Day":
            file_path = os.path.join('attendance', f'{selected_date}.csv')
            self.load_csv_data(file_path)

            # Disable Delete button since we are displaying attendance data
            self.delete_button.config(state=tk.DISABLED)

    def show_all_data(self):
        """Display data from names.csv into Treeview, skipping the first row."""
        # Reset the combobox to default value "Select Day"
        self.attendance_combobox.set("Select Day")
        self.load_csv_data('names.csv', skip_first_row=True)

    def load_today_attendance(self):
        """Check for today's attendance file and load it into the Treeview."""
        today_date = datetime.now().strftime('%Y-%m-%d')  # Format today's date as 'yyyy-mm-dd'
        file_path = os.path.join('attendance', f'{today_date}.csv')  # Path to today's attendance file

        if os.path.isfile(file_path):
            self.load_csv_data(file_path)  # Load data into the Treeview

    def load_csv_data(self, filepath, skip_first_row=False):
        """Load data from a given CSV file and display it in the Treeview."""
        try:
            with open(filepath, newline='') as file:
                reader = csv.reader(file)
                self.clear_treeview()

                # Skip the first row if specified
                if skip_first_row:
                    next(reader, None)  # Skip the first row (header)

                for row in reader:
                    self.treeview.insert("", "end", values=row)
        except FileNotFoundError:
            messagebox.showerror("Error", f"File {filepath} not found")

    def clear_treeview(self):
        """Clear all items in the Treeview."""
        for row in self.treeview.get_children():
            self.treeview.delete(row)

    def on_treeview_select(self, event):
        """Enable the Delete button when an item from names.csv is selected."""
        selected_item = self.treeview.selection()
        if selected_item:
            # Check if the data is from names.csv
            current_combobox_value = self.attendance_combobox.get()
            if current_combobox_value == "Select Day":
                self.delete_button.config(state=tk.NORMAL)
        else:
            self.delete_button.config(state=tk.DISABLED)

    def delete_record(self):
        """Delete the selected record from names.csv and remove its corresponding directory."""
        selected_item = self.treeview.selection()
        if not selected_item:
            messagebox.showwarning("Select Record", "Please select a record to delete.")
            return

        # Get the selected record data
        item_values = self.treeview.item(selected_item[0])['values']
        id_to_delete = item_values[0]
        name_to_delete = item_values[1]

        # Combine ID and Name for directory path
        combined_name = f"{id_to_delete}_{name_to_delete}"
        directory_path = os.path.join("Faces", combined_name)

        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {id_to_delete} {name_to_delete}?"):
            # Remove record from names.csv
            self.remove_record_from_csv('names.csv', id_to_delete, name_to_delete)

            # Remove directory
            self.remove_directory(directory_path)

            # Refresh the Treeview to show the updated data
            self.show_all_data()  # Reload the data from names.csv

    def remove_record_from_csv(self, filepath, id_to_delete, name_to_delete):
        """Remove a record from the specified CSV file."""
        updated_rows = []

        # Make sure both ID and Name are treated as strings for comparison
        id_to_delete = str(id_to_delete).strip()
        name_to_delete = str(name_to_delete).strip()

        with open(filepath, newline='') as file:
            reader = csv.reader(file)

            # Read and keep the header row
            header = next(reader)
            updated_rows.append(header)  # Keep the header in the updated rows

            for row in reader:
                # Strip any extra spaces from the row data
                id_value = row[0].strip()
                name_value = row[1].strip()

                # Check if the current row matches the ID and Name to delete
                if id_value == id_to_delete and name_value == name_to_delete:
                    continue  # Skip this row (effectively deleting it)

                updated_rows.append(row)  # Keep rows that do not match

        # After reading all rows, write the updated rows back to the file
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(updated_rows)  # Write the remaining rows

    def remove_directory(self, directory_path):
        """Remove the specified directory and its contents if it exists."""
        if os.path.exists(directory_path):
            try:
                shutil.rmtree(directory_path)  # Remove the directory and its contents
                messagebox.showinfo("Success", f"Deleted directory {directory_path}.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete directory {directory_path}. {e}")

    def mark_attendance(self):
        import recognize_faces
        try:
            recognizer = recognize_faces.FaceRecognizer()
            recognizer.recognize_faces()
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to start face recognition: {e}")

    def print_data(self):
        """Print the data from the Treeview."""
        try:
            # Get the data from the Treeview
            records = []
            for row in self.treeview.get_children():
                records.append(self.treeview.item(row)['values'])

            if not records:
                messagebox.showwarning("No Data", "There are no records to print.")
                return

            # Create a temporary image to draw the Treeview data
            temp_image_path = tempfile.mktemp(suffix=".png")
            self.create_image_from_records(records, temp_image_path)

            # Print the image using the default printer
            win32api.ShellExecute(0, "print", temp_image_path, None, ".", 0)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while printing: {e}")

    def create_image_from_records(self, records, image_path):
        """Create an image from the records and save it to the specified path."""
        # Create an image with white background
        img_width = 400
        img_height = 20 + len(records) * 30 + 30  # Adjust height based on number of records
        image = Image.new("RGB", (img_width, img_height), "white")
        draw = ImageDraw.Draw(image)

        # Load a font
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except IOError:
            font = ImageFont.load_default()

        # Draw header
        headers = ["ID", "Name", "Time"]
        header_y = 10
        for i, header in enumerate(headers):
            draw.text((10 + i * 130, header_y), header, fill="black", font=font)

        # Draw records
        record_y = header_y + 30
        for record in records:
            for i, value in enumerate(record):
                draw.text((10 + i * 130, record_y), str(value), fill="black", font=font)
            record_y += 30

        # Optionally, add a little extra padding at the bottom
        draw.text((10, record_y), " ", fill="white", font=font)  # Adds a blank line at the end

        # Save the image
        image.save(image_path)

    def exit_application(self):
        """Exit the application with confirmation."""
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit?"):
            self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartAttendanceSystem(root)
    root.mainloop()
