import os
import shutil
import subprocess
import json
import tkinter as tk
from tkinter import ttk
import threading

class CustomApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jar Testing GUI")
        self.root.geometry("1000x700")

        # Dark Mode Configuration
        self.bg_color = "#343a40"  # Dark background color (Bootstrap dark)
        self.fg_color = "#f8f9fa"  # Light foreground color for text
        self.button_color = "#007bff"  # Blue button color (Bootstrap)
        self.button_hover_color = "#0056b3"  # Button hover color
        self.entry_bg_color = "#495057"  # Dark background for entry fields
        self.entry_fg_color = "#f8f9fa"  # Light text color for entry fields

        # Directories
        self.jars_folder = "jars"
        self.test_folder = "test"
        self.plugins_folder = "plugins"  # Plugins folder
        self.configs_folder = "configs"  # Folder containing configuration files

        # JSON data
        self.json_data = []
        self.current_test_index = -1  # Tracks the current test index

        # To keep track of the server process
        self.server_process = None

        # Configure the root window to be dark
        self.root.configure(bg=self.bg_color)

        # Button Frame
        button_frame = tk.Frame(root, bg=self.bg_color)
        button_frame.pack(pady=10)

        # Buttons
        self.generate_button = tk.Button(button_frame, text="Load Jars", command=self.scan_and_generate,
                                          bg=self.button_color, fg=self.fg_color, activebackground=self.button_hover_color)
        self.generate_button.pack(side=tk.LEFT, padx=5)

        self.start_test_button = tk.Button(button_frame, text="Start Test", command=self.start_test,
                                           bg=self.button_color, fg=self.fg_color, activebackground=self.button_hover_color)
        self.start_test_button.pack(side=tk.LEFT, padx=5)

        self.start_server_button = tk.Button(button_frame, text="Start Server", command=self.start_server,
                                             bg=self.button_color, fg=self.fg_color, activebackground=self.button_hover_color)
        self.start_server_button.pack(side=tk.LEFT, padx=5)

        self.next_test_button = tk.Button(button_frame, text="Next Test", command=self.next_test,
                                          bg=self.button_color, fg=self.fg_color, activebackground=self.button_hover_color)
        self.next_test_button.pack(side=tk.LEFT, padx=5)

        self.generate_log_button = tk.Button(button_frame, text="Generate Log", command=self.generate_log,
                                             bg="#28a745", fg="#fff", activebackground="#218838")
        self.generate_log_button.pack(side=tk.LEFT, padx=5)

       
        # Progress Meter
        progress_frame = tk.Frame(root)
        progress_frame.pack(pady=10)

        self.progress_label = tk.Label(progress_frame, text="Progress: 0%")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=5)


        # Pass/Fail Group
        pass_fail_frame = tk.Frame(root, bg=self.bg_color)
        pass_fail_frame.pack(pady=5)

        self.pass_fail_label = tk.Label(pass_fail_frame, text="Pass/Fail:", bg=self.bg_color, fg=self.fg_color)
        self.pass_fail_label.pack(side=tk.LEFT, padx=5)

        self.pass_fail_var = tk.StringVar(value="Pending")
        self.pass_fail_combobox = ttk.Combobox(pass_fail_frame, textvariable=self.pass_fail_var,
                                               values=["Pass", "Fail", "Pending"])
        self.pass_fail_combobox.pack(side=tk.LEFT, padx=5)

        # Notes Group
        notes_frame = tk.Frame(root, bg=self.bg_color)
        notes_frame.pack(pady=5)

        self.notes_label = tk.Label(notes_frame, text="Notes:", bg=self.bg_color, fg=self.fg_color)
        self.notes_label.pack(side=tk.LEFT, padx=5)

        self.notes_entry = tk.Entry(notes_frame, width=50, bg=self.entry_bg_color, fg=self.entry_fg_color)
        self.notes_entry.pack(side=tk.LEFT, padx=5)

        self.update_status_button = tk.Button(notes_frame, text="Update Status", command=self.update_status,
                                              bg=self.button_color, fg=self.fg_color, activebackground=self.button_hover_color)
        self.update_status_button.pack(side=tk.LEFT, padx=5)

        # Table for JSON Data
        self.table = ttk.Treeview(root, columns=("File Name", "Status", "Notes"), show="headings", height=15)
        self.table.heading("File Name", text="File Name")
        self.table.heading("Status", text="Status")
        self.table.heading("Notes", text="Notes")
        self.table.column("File Name", width=400)
        self.table.column("Status", width=150)
        self.table.column("Notes", width=200)
        self.table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Feedback Area
        feedback_frame = tk.Frame(root, bg=self.bg_color)
        feedback_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.feedback_text = tk.Text(feedback_frame, wrap=tk.WORD, height=10, bg=self.entry_bg_color, fg=self.entry_fg_color)
        self.feedback_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.feedback_text.config(state=tk.DISABLED)

    def log_feedback(self, message):
        """Log feedback messages to the text area."""
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.insert(tk.END, message + "\n")
        self.feedback_text.see(tk.END)
        self.feedback_text.config(state=tk.DISABLED)

    def scan_and_generate(self):
        """Scans the jars folder for .jar files and generates a JSON file."""
        try:
            if not os.path.exists(self.jars_folder):
                os.makedirs(self.jars_folder)

            files = [file for file in os.listdir(self.jars_folder) if file.endswith(".jar")]
            self.json_data = [{"file_name": file, "status": "Pending", "notes": ""} for file in files]

            with open("output.json", "w") as f:
                json.dump(self.json_data, f, indent=4)

            self.log_feedback("JSON file 'output.json' generated successfully!")
            self.load_table()
        except Exception as e:
            self.log_feedback(f"Error: {e}")

    def load_table(self):
        """Loads the JSON data into the table and colors the status."""
        for row in self.table.get_children():
            self.table.delete(row)

        for index, item in enumerate(self.json_data):
            status_color = ""
            if item["status"] == "Pass":
                status_color = "green"
            elif item["status"] == "Fail":
                status_color = "red"
            elif index == self.current_test_index:  # Highlight current test in purple
                status_color = "purple"

            # Insert item into the table with appropriate color for status
            self.table.insert("", "end", values=(item["file_name"], item["status"], item["notes"]),
                              tags=(status_color,))

        # Apply colors to the "Status" column
        self.table.tag_configure("green", background="lightgreen")
        self.table.tag_configure("red", background="lightcoral")
        self.table.tag_configure("purple", background="lavender")  # Add purple highlight
        self.update_progress()

    def start_test(self):
        """Prepares the test folder for testing."""
        try:
            if os.path.exists(self.test_folder):
                shutil.rmtree(self.test_folder)
            os.makedirs(self.test_folder)

            self.current_test_index = 0
            self.copy_to_test_folder()  # Move the copying logic here

        except Exception as e:
            self.log_feedback(f"Error: {e}")

    def copy_to_test_folder(self):
        """Copies the current jar file, generates the batch file, and copies the plugins and configs folders."""
        try:
            if 0 <= self.current_test_index < len(self.json_data):
                jar_file = self.json_data[self.current_test_index]["file_name"]
                jar_path = os.path.join(self.jars_folder, jar_file)

                # Copy the jar file to the test folder
                shutil.copy(jar_path, self.test_folder)
                self.log_feedback(f"Copied {jar_file} to the test folder.")

                # Create the run.bat file
                bat_file = os.path.join(self.test_folder, "run.bat")
                with open(bat_file, 'w') as bat:
                    bat.write(f"@echo off\n")
                    bat.write(f"java -Xmx1G -jar {jar_file}\n")

                self.log_feedback(f"run.bat file created for {jar_file}.")

                # Copy the contents of the configs folder to the test folder
                if os.path.exists(self.configs_folder):
                    for item in os.listdir(self.configs_folder):
                        s = os.path.join(self.configs_folder, item)
                        d = os.path.join(self.test_folder, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                    self.log_feedback("Configs folder contents copied to the test folder.")
                else:
                    self.log_feedback("Configs folder not found. Skipping copy.")


        except Exception as e:
            self.log_feedback(f"Error: {e}")

    def start_server(self):
        """Starts the server by running the batch file in the test folder using threading."""
        try:
            bat_file = os.path.join(self.test_folder, "run.bat")

            if not os.path.exists(bat_file):
                self.log_feedback("Error: run.bat file not found in the test folder.")
                return

            # Create a new thread to run the batch file
            thread = threading.Thread(target=self.run_batch_file, args=("run.bat",))
            thread.start()

        except Exception as e:
            self.log_feedback(f"Error: {e}")

    def update_progress(self):
        """Updates the progress bar and label based on test statuses."""
        if not self.json_data:
            self.progress_bar["value"] = 0
            self.progress_label.config(text="Progress: 0%")
            return

        total_tests = len(self.json_data)
        completed_tests = sum(1 for test in self.json_data if test["status"] in ["Pass", "Fail"])
        progress_percentage = int((completed_tests / total_tests) * 100)

        self.progress_bar["value"] = progress_percentage
        self.progress_label.config(text=f"Progress: {progress_percentage}%")
        
    def run_batch_file(self, bat_file_name):
        """Runs the batch file in a separate thread."""
        try:
            bat_file_path = os.path.join(self.test_folder, bat_file_name)

            # Run the .bat file using subprocess (we won't capture output)
            self.server_process = subprocess.Popen(
                ['cmd', '/c', bat_file_name], cwd=self.test_folder
            )

        except Exception as e:
            self.log_feedback(f"Error: {e}")

    def update_status(self):
        """Updates the status and notes for the current jar file."""
        try:
            if 0 <= self.current_test_index < len(self.json_data):
                self.json_data[self.current_test_index]["status"] = self.pass_fail_var.get()
                self.json_data[self.current_test_index]["notes"] = self.notes_entry.get()

                with open("output.json", "w") as f:
                    json.dump(self.json_data, f, indent=4)

                self.load_table()
                self.log_feedback("Status and notes updated successfully.")
            else:
                self.log_feedback("No jar file is currently set for testing.")
        except Exception as e:
            self.log_feedback(f"Error: {e}")
        self.update_progress()
            

    def next_test(self):
        """Prepares the next test by killing the server (if running) and starting the next test."""
        try:
            # Kill the currently running server
            self.kill_server()

            # Find the next test with status "Pending"
            for _ in range(len(self.json_data)):
                # Increment test index and wrap around if necessary
                self.current_test_index = (self.current_test_index + 1) % len(self.json_data)
                current_test = self.json_data[self.current_test_index]

                if current_test["status"] == "Pending":
                    # Clear the test folder
                    if os.path.exists(self.test_folder):
                        shutil.rmtree(self.test_folder)
                    os.makedirs(self.test_folder)

                    # Copy the JAR file and other necessary files to the test folder
                    self.copy_to_test_folder()

                    return

            # If no pending tests are found, notify the user
            self.log_feedback("No pending tests found. All tests are complete.")

        except Exception as e:
            self.log_feedback(f"Error: {e}")

    def kill_server(self):
        """Kills the running Minecraft server process."""
        if self.server_process:
            try:
                self.server_process.terminate()  # Kill the process
                self.log_feedback("Minecraft server killed successfully.")
                self.server_process = None
            except Exception as e:
                self.log_feedback(f"Error while killing the server: {e}")
        else:
            self.log_feedback("No server process is currently running.")

    def generate_log(self):
        """Generates a text log and saves it to a file."""
        try:
            with open("test_output_log.txt", "w") as log_file:
                for item in self.json_data:
                    log_file.write(f"{item['file_name']} - {item['status']} - {item['notes']}\n")
            self.log_feedback("Log file 'test_output_log.txt' generated successfully.")
        except Exception as e:
            self.log_feedback(f"Error while generating log: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CustomApp(root)
    root.mainloop()
