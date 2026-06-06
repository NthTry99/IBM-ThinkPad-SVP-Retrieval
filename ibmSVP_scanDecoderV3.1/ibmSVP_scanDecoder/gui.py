import tkinter as tk

from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .logic import SCANCODES, SVPDecoder

class DecoderAPP:
    def __init__(self, root):
        self.root = root
        self.root.title("ibmSVP_scanDecoder_v3.1")
        self.decoder = SVPDecoder() # Initialize logic engine

        # Create GUI
        self._setup_window()
        self._apply_styles()
        self._create_widgets()

    def _setup_window(self):
        """ Handles window sizing and grid layout. """

        # Instance variables
        self.file_content = None
        self.file_path = None
        self.tree_left = None       # Scancodes displayed
        self.tree_right = None      # between 2 adjacent tables
        self.popup_scancode = None
     
        self.root.geometry("750x500")
        self.root.minsize(750,500)

        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

    def _apply_styles(self):
        """Configures global ttk styles and themes."""
        style = ttk.Style()
        style.theme_use("clam")  # 'clam' theme supports better border customization
        style.configure("Treeview", 
                        background="white", 
                        fieldbackground="white", 
                        foreground="black", 
                        rowheight=25, 
                        borderwidth=1, 
                        font=('Arial', 14)
                        )
        style.configure("Treeview.Heading", font=('TkDefaultFont', 12, 'bold'))
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) # Ensures the border draws

    def _create_widgets(self):
        self.label_file_loaded = tk.Label(self.root, text="Click \"Load File\" to get started", font=('Arial', 16))
        self.label_file_loaded.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

        self.label_SVP = tk.Label(self.root, text="", font=('Arial', 16))
        self.label_SVP.grid(row=1, column=0, sticky="nw", padx=5)

        self.button_load = tk.Button(self.root, text="Load File", font=('Arial', 16), command=self.on_button_load_click)
        self.button_load.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        self.button_scancode = tk.Button(self.root, text="Scancode Table", font=('Arial', 16), command=self.on_button_scancode_click)
        self.button_scancode.grid(row=0, column =2, pady=5)

        self.button_svp = tk.Button(self.root, text="Show SVP", width=13, font=('Arial', 16), command=self.on_button_svp_click)
        self.button_svp.grid(row=1, column=3, sticky="ew", padx=5)
        self.button_svp.config(state=tk.DISABLED)

        self.output_box = tk.Text(self.root, font=("Courier", 12, "bold"), wrap=tk.WORD)
        self.output_box.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        self.output_box.config(state=tk.DISABLED)

    def on_button_svp_click(self):
        """ GUI. On click. Calls the decode method then displays and highlights results """
        try:
            if self.button_svp.cget('text') in ["Show SVP", "Show Scancode"]:
                # Show output as Scancodes
                created_hex_dump = self.decoder.add_hex_headers_to_bin(self.file_content, "scan")
                # Change button to Show ASCII
                self.button_svp.config(text="Show ASCII")
            else:
                # Change button to Show Scancode
                self.button_svp.config(text="Show Scancode")
                # Show output as ASCII
                created_hex_dump = self.decoder.add_hex_headers_to_bin(self.file_content, "ascii")
            
            # Display and print the dump
            self.display_outputbox(created_hex_dump)
    #        print(created_hex_dump)
            # Decode and print password in terminal and SVP label
            password = self.decoder.decode_svp(self.file_content)
    #        print(f"Supervisor Password: {password}")
            self.label_SVP.config(text=f"Supervisor Password: {password}")
            # Highlight password in output box
            # Get SVP offsets from raw file content (byte list)
            SVP_offsets = self.decoder.get_svp_offsets(self.file_content)
            # Isolates and highlights the password in the offset
            self.highlight_and_scroll(self.output_box, SVP_offsets)
            
        except Exception as e:
            error = "[error]: No SVP detected. Either this is the wrong file, a dump of a block which does not contain the SVP, or an incorrect EEPROM dump. Try again.\n"
            print(f"<{Path(self.file_path).name}> on_button_svp_click: except: {e}\n{error}")
            # Update lables with error, show error dialog
            self.label_SVP.config(text="No SVP detected!")
            self.label_file_loaded.config(text="Error: <" + Path(self.file_path).name + ">")
            messagebox.showerror("No SVP detected", error)

    def highlight_and_scroll(self, text_widget, SVP_offsets):
        """ GUI: Highlights and scrolls to the SVP in the displayed hex dump """

        # Convert offsets to hex (which will be highlighted)
        highlight_SVP = " ".join(f"{x:02x}" for x in SVP_offsets)

        # Clear previous highlights
        text_widget.tag_remove("hex_highlight", "1.0", "end")
        
        # Search loop
        start_pos = "1.0"
        while True:
            # search() returns the index of the first match
            start_pos = self.output_box.search(highlight_SVP, start_pos, stopindex="end")
            if not start_pos:
                break
            # Calculate end position: start index + length of highlight_SVP
            end_pos = f"{start_pos}+{len(highlight_SVP)}c"
            # Apply the tag to the range
            self.output_box.tag_add("hex_highlight", start_pos, end_pos)
            text_widget.tag_configure("hex_highlight", background="yellow")

            # Keep searching (to get the password repeat) and go to the highlight
            start_pos = end_pos
            text_widget.see(start_pos)

    def display_outputbox (self, message):
        """ GUI: updates the big main outputbox display """
        # Unlock text box
        self.output_box.config(state=tk.NORMAL)
        # Delete text box contents
        self.output_box.delete("1.0", tk.END) # Clear from line 1, char 0 to end
        # Insert new text content
        self.output_box.insert(tk.END, message + "\n")
        # Relock text box
        self.output_box.config(state=tk.DISABLED)

    def on_button_load_click(self):
        """ GUI: loads and displays file, prepares GUI for loaded file """
        load_file_path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[("raw binary files", "*.bin"), ("hex dumps", ".txt"), ("All files", "*.*")]
        )

        if load_file_path:
            # Only set self.file_path if a file was acutally selected
            self.file_path = load_file_path
            # Ensure SVP button is reset
            self.button_svp.config(text="Show SVP")

            try:
                # Get the file as a bytes list, set to instance variable
                self.file_content = self.decoder.read_file_bytes(self.file_path)
                print(f"File Loaded: <{Path(self.file_path).name}> -- {len(self.file_content)} bytes")

                # Add offset labels/headers and display/print it
                created_hex_dump = self.decoder.add_hex_headers_to_bin(self.file_content)
                # print(created_hex_dump)
                self.display_outputbox(created_hex_dump)

                # Display name of loaded file in label
                self.label_file_loaded.config(text="File Loaded: <" + Path(self.file_path).name + ">")
                # Unlock SVP button
                self.button_svp.config(state=tk.NORMAL)
                self.label_SVP.config(text="Click \"Get SVP\"")

            except Exception as e:
                errorMsg = "[error]: This file is not supported. It must be a raw binary file (.bin) or a hex dump (.txt)\n"
                print(f"<{Path(self.file_path).name}> on_button_load_click: except: {e}\n{errorMsg}")
                self.display_outputbox(errorMsg)

                # Put error in the file label, disable SVP button, clear SVP label
                self.label_file_loaded.config(text="Error: <" + Path(self.file_path).name + ">")
                self.button_svp.config(state=tk.DISABLED)
                self.label_SVP.config(text="")


#########SCANCODE BUTTON/TABLE STUFF############
    def sort_and_redistribute(self, col_index, reverse):
        # Convert the scancodes to a list of string tuples (used in GUI)
        scancodes_strings_tuples = [(f"0x{code:02x}", str(char)) for code, char in SCANCODES.items()]

        # Sort the entire dataset
        if col_index == 0: # Sort by Scancode (Hex Encoding)
            scancodes_strings_tuples.sort(key=lambda x: int(x[0], 16), reverse=reverse)
        else: # Sort by Value (a-z, 0-9)
            scancodes_strings_tuples.sort(key=lambda x: x[1], reverse=reverse)

        # Clear and Refill both tables
        for tree in [self.tree_left, self.tree_right]:
            for item in tree.get_children():
                tree.delete(item)

        midpoint = len(scancodes_strings_tuples) // 2
        for i, (enc, val) in enumerate(scancodes_strings_tuples):
            target_tree = self.tree_left if i < midpoint else self.tree_right
            target_tree.insert("", "end", values=(enc, val))

        # Update indicators
        char = " ▼" if reverse else " ▲"
        for tree in [self.tree_left, self.tree_right]:
            for idx, name in enumerate(["Scancode", "Value"]):
                new_text = name + (char if idx == col_index else "")
                tree.heading(name, text=new_text, 
                             command=lambda c=idx: self.sort_and_redistribute(c, not reverse))

    def on_button_scancode_click(self):
        # Create scancode popup if it doesn't exist
        if self.popup_scancode is None or not self.popup_scancode.winfo_exists():
            self.popup_scancode = tk.Toplevel(self.root)
            self.popup_scancode.title("Scancode Table")
            self.popup_scancode.geometry("480x500")
            self.popup_scancode.resizable(False, False)

            # Container for the two tables
            main_frame = tk.Frame(self.popup_scancode)
            main_frame.pack(padx=10, pady=10)

            cols = ("Scancode", "Value")
            
            # Create Left and Right tables
            self.tree_left = ttk.Treeview(main_frame, columns=cols, show="headings", height=18, selectmode="none")
            self.tree_right = ttk.Treeview(main_frame, columns=cols, show="headings", height=18, selectmode="none")

            # Create tables
            for tree in [self.tree_left, self.tree_right]:
                for i, col in enumerate(cols):
                    tree.heading(col, text=col, command=lambda c=i: self.sort_and_redistribute(c, False))
                    tree.column(col, width=110, anchor="center")
                tree.pack(side="left", padx=5)

            # Prevent multiple selections and disable resizing headings
            for tree, other in [(self.tree_left, self.tree_right), (self.tree_right, self.tree_left)]:
                tree.bind("<Button-1>", lambda e, t=tree, o=other: self.manual_select(e, t, o))
                tree.bind("<Button-1>", lambda e, t=tree: self.disable_resize(e, t), add='+')

            # Initial data load
            self.sort_and_redistribute(1, False) # Default sort by Value
            
        # Automatically bring to front and focus
        self.popup_scancode.deiconify()     # Restores the window if it was minimized
        self.popup_scancode.lift()          # Brings it to the top of all other windows
        self.popup_scancode.focus_force()   # Force keyboard focus

    def disable_resize(self, event, tree):
        # Check if the user clicked the column border ("separator")
        if tree.identify_region(event.x, event.y) == "separator":
            return "break"  # Stop the resize event from happening

    def manual_select(self, event, clicked_tree, other_tree):
    # Figure out which row was clicked
        row_id = clicked_tree.identify_row(event.y)
        
        if row_id:
            # Clear the OTHER table completely
            other_tree.selection_remove(other_tree.selection())
            
            # Select ONLY the clicked row in this table
            clicked_tree.selection_set(row_id)
            clicked_tree.focus(row_id)


# stays in gui.py
# This part ensures the app only starts if this file is executed directly
if __name__ == "__main__":
    root = tk.Tk()              # Create the actual window
    app = DecoderAPP(root)      # Initialize your class and pass the window to it
    root.mainloop()             # Start the application loop
