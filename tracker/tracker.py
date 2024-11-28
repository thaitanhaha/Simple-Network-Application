import socket
import os
import pickle
import threading
import time
from tracker_GUI import Tracker_GUI
import tkinter as tk
from collections import defaultdict

class Tracker:
    def __init__(self) -> None:
        self.peers = {}
        self.command_for_peer = {
            "peer_addr": None,
            "has_command": False,
            "type": None,
            "data": None,
        }
        self.block_dict = defaultdict(list)

    def peer_handler(self, peer_socket: socket.socket, peer_addr):
        while True:
            try:
                msg = pickle.loads(peer_socket.recv(1024))
                msg_type = msg['type']
                msg_data = msg['data']
                if (self.command_for_peer["has_command"] and peer_addr == self.command_for_peer["peer_addr"]):
                    self.command_for_peer["data"] = msg_data
                else:
                    match msg_type:
                        case "fetch":
                            file_name = msg_data
                            file_hash = None
                            for i in range(len(self.peers[peer_addr]['peer_files'])):
                                if self.peers[peer_addr]['peer_files'][i][0] == file_name:
                                    file_hash = self.peers[peer_addr]['peer_files'][i][2]
                                    break
                            peers_has_file = []
                            peer_addr_tuple = peer_addr.split(':')
                            peer_addr_tuple = (peer_addr_tuple[0], int(peer_addr_tuple[1]))
                            for peer in self.peers:
                                if peer_addr_tuple in self.block_dict[peer]:
                                    continue
                                if any(file_name == file[0] and file_hash != file[2] for file in self.peers[peer]['peer_files']):
                                    peers_has_file.append(self.peers[peer]['peer_address'])
                            peer_socket.send(pickle.dumps({
                                'type': 'fetch_result',
                                'data': peers_has_file,
                            }))
                        case "list":
                            peer_list = []
                            for peer in self.peers:
                                peer_list.append(self.peers[peer]['peer_address'])
                            peer_socket.send(pickle.dumps({
                                'type': 'list_result',
                                'data': peer_list,
                            }))
                        case "publish":
                            status = True
                            self.peers[peer_addr]['peer_files'] = msg_data
                            self.peers[peer_addr]['peer_history'].append(self.peers[peer_addr]['peer_files'].copy())
                            peer_socket.send(pickle.dumps({
                                'type': 'publish_result',
                                'data': status,
                            }))
                        case "history":
                            file_name = msg_data
                            file_history = []
                            for history in self.peers[peer_addr]['peer_history']:
                                for i in range(len(history)):
                                    if history[i][0] == file_name:
                                        file_history.append(history[i])
                            peer_socket.send(pickle.dumps({
                                'type': 'history_result',
                                'data': file_history,
                            }))
                        case "reset":
                            file_name = msg_data[0]
                            file_version = int(msg_data[1])
                            file_data_encoded = None
                            temp = self.peers[peer_addr]['peer_history'][file_version]
                            for i in range(len(temp)):
                                if temp[i][0] == file_name:
                                    file_data_encoded = temp[i][2]
                            peer_socket.send(pickle.dumps({
                                'type': 'reset_result',
                                'data': (file_name, file_data_encoded),
                            }))
                        case "block":
                            peer_ip = msg_data[0]
                            peer_port = msg_data[1]
                            status = None
                            if f"{peer_ip}:{peer_port}" in self.peers: 
                                self.block_dict[peer_addr].append((peer_ip, peer_port))
                                status = (peer_ip, peer_port)
                            peer_socket.send(pickle.dumps({
                                'type': 'block_result',
                                'data': status,
                            }))
                        case "unblock":
                            peer_ip = msg_data[0]
                            peer_port = msg_data[1]
                            status = None
                            if f"{peer_ip}:{peer_port}" in self.peers and \
                                (peer_ip, peer_port) in self.block_dict[peer_addr]:
                                self.block_dict[peer_addr].remove((peer_ip, peer_port))
                                status = (peer_ip, peer_port)
                            peer_socket.send(pickle.dumps({
                                'type': 'unblock_result',
                                'data': status,
                            }))
                        case "quit":
                            self.peers.pop(peer_addr)
                            peer_socket.close()
                            break
                        case _:
                            continue
            except Exception as e:
                print("peer_handler stop!!")
                break

    def command_handler(self, tracker_socket: socket.socket, tracker_gui: Tracker_GUI):
        def quit_command():
            tracker_gui.print_message("Closing tracker socket!\n")
            for peer in self.peers:
                self.peers[peer]['peer_socket_object'].send(pickle.dumps({
                    'type': 'quit',
                    'data': None,
                }))
                self.peers[peer]['peer_socket_object'].close()
            tracker_socket.close()

        def update_command(peer_addr):
            peer_socket = self.peers[peer_addr]['peer_socket_object']
            tracker_gui.print_message(f"Updating {peer_addr}...\n")
            peer_socket.send(pickle.dumps({
                'type': 'update',
                'data': None,
            }))
            while True:
                if self.command_for_peer["data"] is not None:
                    list_of_files = self.command_for_peer["data"].copy()
                    break
            self.peers[peer_addr]['peer_files'] = list_of_files
            self.peers[peer_addr]['peer_history'].append(self.peers[peer_addr]['peer_files'].copy())
            files = []
            for file_name, _, _ in self.peers[peer_addr]['peer_files']:
                files.append(file_name)
            tracker_gui.print_message(f"Files on {peer_addr}: {files}\n\n")

        command = tracker_gui.get_command()
        
        self.command_for_peer["has_command"] = True
        args_list = command.split()
        print_str = ""
        match args_list[0]:
            case "list":
                if len(args_list) == 1:
                    i = 1
                    if len(self.peers) > 0:
                        for peer in self.peers:
                            files = []
                            for file_name, _, _ in self.peers[peer]['peer_files']:
                                files.append(file_name)
                            print_str += f"{i}. {peer}: {files}\n"
                            i += 1
                    else:
                        print_str = "There is no peer."
                    tracker_gui.print_message(f"{print_str}\n")
                else:
                    tracker_gui.print_message("Not a valid command!\nlist requires no arguments\n")

            case "update":
                self.command_for_peer["type"] = "update"
                for peer_addr in self.peers:
                    self.command_for_peer["peer_addr"] = peer_addr
                    update_command(peer_addr)
                    time.sleep(2)
                    self.command_for_peer["data"] = None

            case "quit":
                quit_command()
            case _:
                tracker_gui.print_message("Not a valid command!\n\n")

        self.command_for_peer = {
            "peer_addr": None,
            "has_command": False,
            "type": None,
            "data": None,
        }
        return "break"

    def peer_listener(self, tracker_socket: socket.socket, tracker_gui: Tracker_GUI):
        while True:
            try:
                peer_socket, peer_addr = tracker_socket.accept()
                msg = pickle.loads(peer_socket.recv(1024))
                msg_type = msg['type']
                msg_data = msg['data']
                if msg_type == 'connect':
                    peer_socket.send(pickle.dumps({
                        'type': 'connect_result',
                        'data': peer_addr,
                    }))
                    files = []
                    for file_name, _, _ in msg_data:
                        files.append(file_name)
                    tracker_gui.print_message(f"Accepted connection from {peer_addr[0]}:{peer_addr[1]} with these files: {files}\n\n")
                    self.peers[f"{peer_addr[0]}:{peer_addr[1]}"] = {
                        "peer_socket_object": peer_socket,
                        "peer_address": peer_addr,
                        "peer_files": msg_data,
                        "peer_history": [msg_data.copy()],
                    }
                    threading.Thread(target=self.peer_handler, args=[peer_socket, f"{peer_addr[0]}:{peer_addr[1]}"]).start()
            except Exception as e:
                tracker_gui.print_message("peer_listener stop!!\n\n")
                return

    def main(self):
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_ip = "localhost"
        tracker_port = 65432
        tracker_socket.bind((tracker_ip, tracker_port))
        tracker_socket.listen(5)

        tracker_gui = Tracker_GUI()
        tracker_gui.title("Tracker terminal")
        tracker_gui.bind(
            "<Return>",
            lambda event, tracker_socket=tracker_socket, tracker_gui=tracker_gui: self.command_handler(tracker_socket, tracker_gui),
        )
        tracker_gui.print_message(f"Listening on {tracker_ip}:{tracker_port}\n\n")
        threading.Thread(target=self.peer_listener, args=[tracker_socket, tracker_gui]).start()
        tracker_gui.mainloop()


if __name__ == "__main__":
    (Tracker()).main()
