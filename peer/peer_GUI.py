import tkinter as tk
from tkinter import scrolledtext
import sys
sys.path.append('../')
from GUI_redirector import GUI_Redirector

class Peer_GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("File Transfer Peer")
        self.geometry("600x400")

        label_app = tk.Label(self, text="File-sharing application", font=("Arial", 16, "bold"), fg="blue", bg="#F0F0F0")
        label_app.pack(side=tk.TOP, pady=10)
        label_side = tk.Label(self, text="Peer side", font=("Arial", 16, "bold"), fg="blue", bg="#F0F0F0")
        label_side.pack(side=tk.TOP)

        self.button_frame = tk.Frame(self, bg="#D0D0D0")
        self.button_frame.pack(side=tk.TOP, fill=tk.X)

        button_help = tk.Button(self.button_frame, text="Help", command=self.button_help_action, bg="#90EE90")
        button_help.grid(row=0, column=0, padx=5, pady=5)

        button_list = tk.Button(self.button_frame, text="List", command=self.button_list_action, bg="#90EE90")
        button_list.grid(row=0, column=1, padx=5, pady=5)

        button_publish = tk.Button(self.button_frame, text="Publish", command=self.button_publish_action, bg="#FFD700")
        button_publish.grid(row=0, column=2, padx=5, pady=5)

        button_clear = tk.Button(self.button_frame, text="Clear", command=self.clear_console, bg="#87CEEB")
        button_clear.grid(row=0, column=3, padx=5, pady=5)

        button_quit = tk.Button(self.button_frame, text="Quit", command=self.quit_action, bg="#FF6347")
        button_quit.grid(row=0, column=4, padx=5, pady=5)

        button_fetch = tk.Button(self.button_frame, text="Fetch", command=self.button_fetch_action, bg="#FFD700")
        button_fetch.grid(row=1, column=0, padx=5, pady=5)
        self.entry_fetch = tk.Entry(self.button_frame)
        self.entry_fetch.grid(row=1, column=1, padx=5, pady=5)

        button_history = tk.Button(self.button_frame, text="History", command=self.button_history_action, bg="#FFD700")
        button_history.grid(row=2, column=0, padx=5, pady=5)
        self.entry_history = tk.Entry(self.button_frame)
        self.entry_history.grid(row=2, column=1, padx=5, pady=5)

        button_reset = tk.Button(self.button_frame, text="Reset", command=self.button_reset_action, bg="#FFD700")
        button_reset.grid(row=3, column=0, padx=5, pady=5)
        self.entry_reset_file = tk.Entry(self.button_frame)
        self.entry_reset_file.grid(row=3, column=1, padx=5, pady=5)
        self.entry_reset_version = tk.Entry(self.button_frame)
        self.entry_reset_version.grid(row=3, column=2, padx=5, pady=5)

        button_block = tk.Button(self.button_frame, text="Block", command=self.button_block_action, bg="#FFD700")
        button_block.grid(row=4, column=0, padx=5, pady=5)
        button_unblock = tk.Button(self.button_frame, text="Unblock", command=self.button_unblock_action, bg="#FFD700")
        button_unblock.grid(row=4, column=1, padx=5, pady=5)
        self.entry_block_ip = tk.Entry(self.button_frame)
        self.entry_block_ip.grid(row=4, column=2, padx=5, pady=5)
        self.entry_block_port = tk.Entry(self.button_frame)
        self.entry_block_port.grid(row=4, column=3, padx=5, pady=5)

        console_frame = tk.Frame(self, bg="#F0F0F0")
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.console_text = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, font=("Arial", 12), bg="#F0F0F0", fg="#333333")  # Dark gray text on light gray background
        self.console_text.pack(fill=tk.BOTH, expand=True)

        self.console_text.insert(tk.END, ''' Welcome to file transferring application! 
 This is the PEER side!
''')

        sys.stdout = GUI_Redirector(self.console_text)

        self.console_text.tag_configure("red", foreground="red")
        self.console_text.tag_configure("blue", foreground="blue")
        self.console_text.tag_configure("black", foreground="black")
        self.console_text.config(state=tk.DISABLED)

        self.option_buttons = []

    def button_help_action(self):
        self.print_message("Help\n", "blue")
        self.print_message('''list - List all peers in the application
publish - Send information of all files to tracker
fetch fname - Send a fetch request to tracker to fetch file with name at fname
history fname - Get all the history version of a file
reset fname version - Get the data of a file in a specific version
block/unblock peer - Block/Unblock a peer
quit - Shut down peer socket.\n
''', "black")
        self.console_text.mark_set('insert', tk.END)

    def button_publish_action(self):
        self.print_message("publish\n", "blue")
        self.call_action()

    def button_list_action(self):
        self.print_message("list\n", "blue")
        self.call_action()

    def button_fetch_action(self):
        entry_fetch_text = self.entry_fetch.get()
        if entry_fetch_text == "":
            self.print_message("fetch: Please enter a file name!\n", "red")
            self.console_text.mark_set('insert', tk.END)
        else:
            self.print_message("fetch " + entry_fetch_text + "\n", "blue")
            self.call_action()

    def button_history_action(self):
        entry_history_text = self.entry_history.get()
        if entry_history_text == "":
            self.print_message("fetch: Please enter a file name!\n", "red")
            self.console_text.mark_set('insert', tk.END)
        else:
            self.print_message("history " + entry_history_text + "\n", "blue")
            self.call_action()

    def button_reset_action(self):
        entry_reset_file = self.entry_reset_file.get()
        entry_reset_version = self.entry_reset_version.get()
        if entry_reset_file == "" and entry_reset_version == "":
            self.print_message("fetch: Please enter a file name and a version!\n", "red")
            self.console_text.mark_set('insert', tk.END)
        else:
            self.print_message("reset " + entry_reset_file + " " + entry_reset_version + "\n", "blue")
            self.call_action()

    def button_block_action(self):
        entry_block_ip_text = self.entry_block_ip.get()
        entry_block_port_text = self.entry_block_port.get()
        if entry_block_ip_text == "" and entry_block_port_text == "":
            self.print_message("fetch: Please enter a peer address!\n", "red")
            self.console_text.mark_set('insert', tk.END)
        else:
            self.print_message("block " + entry_block_ip_text + " " + entry_block_port_text + "\n", "blue")
            self.call_action()

    def button_unblock_action(self):
        entry_block_ip_text = self.entry_block_ip.get()
        entry_block_port_text = self.entry_block_port.get()
        if entry_block_ip_text == "" and entry_block_port_text == "":
            self.print_message("fetch: Please enter a peer address!\n", "red")
            self.console_text.mark_set('insert', tk.END)
        else:
            self.print_message("unblock " + entry_block_ip_text + " " + entry_block_port_text + "\n", "blue")
            self.call_action()

    def quit_action(self):
        self.print_message("quit\n", "blue")
        self.call_action()

    def print_message(self, msg: str, color="black"):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, msg, color)
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)

    def call_action(self):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.event_generate("<Return>")
        self.console_text.config(state=tk.DISABLED)
        self.console_text.mark_set('insert', tk.END)

    def get_command(self):
        return self.console_text.get("end-2l", "end-1c")
    
    def clear_console(self):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state=tk.DISABLED)

    def fetch_options(self, num_options):
        self.option_buttons = []
        for i in range(num_options):
            button = tk.Button(
                self.button_frame, text=f"Option {i+1}", 
                command=lambda i=i: self._option_action(i), bg="#ADD8E6"
            )
            button.grid(row=1, column=2 + i, padx=5, pady=5)
            self.option_buttons.append(button)

    def _option_action(self, index):
        self.print_message(f"Option {index+1} selected\n")
        for button in self.option_buttons:
            button.destroy()
        self.option_buttons = []
        self.call_action()



