import socket
import os
import pickle
import threading
import shutil
from peer_GUI import Peer_GUI
import re
import base64

class Peer:
    def __init__(self) -> None:
        self.local_dir = 'local\\'
        self.my_addr = []
        self.is_choosing = False
        self.tracker_socket = None
        self.socket_for_upload = None
        self.other_peer = []
        self.blocked_peer = []
        
    def get_files_name(self):
        return os.listdir(os.path.join(os.getcwd(), self.local_dir))
    
    def get_encode_file(self, file_path):
        with open(file_path, 'rb') as f:
            file_data = f.read()
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        return encoded_data

    def get_files_information(self):
        files_name = self.get_files_name()
        files_info = []
        for f in files_name:
            full_path = os.path.join(os.getcwd(), self.local_dir, f)
            if os.path.isfile(full_path):
                file_size = os.path.getsize(full_path)
                file_hash = self.get_encode_file(full_path)
                files_info.append((f, file_size, file_hash))
        return files_info
        
    def command_handler(self, peer_gui: Peer_GUI):
        try:
            command = peer_gui.get_command()
            if self.is_choosing:
                try:
                    num_choice = re.search(r'\d+', command).group()
                    choice = self.other_peer[int(num_choice) - 1]
                    fetch_ip, fetch_port = (choice[0], choice[1]+1)
                    fetch_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    fetch_socket.connect((fetch_ip, fetch_port))
                    fetch_socket.send(pickle.dumps({
                        'type': 'fetch_peer',
                        'data': self.file_name,
                    }))
                    with open(f'{self.local_dir}{self.file_name}','wb') as file:
                        while True:
                            chunk = fetch_socket.recv(1024)
                            if not chunk: break
                            file.write(chunk)
                            fetch_socket.send('data received.'.encode('utf-8'))
                    fetch_socket.close()
                except Exception as e:
                    peer_gui.print_message(f'Error while fetching: {e}\n\n')
                self.is_choosing = False
                peer_gui.print_message('Fetching completed!!\n')
                files = self.get_files_information()
                self.tracker_socket.send(pickle.dumps({
                    'type': 'publish',
                    'data': files,
                }))
            else:
                args_list = command.split()
                match args_list[0]:
                    case 'fetch':
                        self.file_name  = args_list[1]
                        self.tracker_socket.send(pickle.dumps({
                            'type': 'fetch',
                            'data': self.file_name,
                        }))
                    case 'list':
                        self.tracker_socket.send(pickle.dumps({
                            'type': 'list',
                            'data': None,
                        }))
                    case 'publish':
                        files = self.get_files_information()
                        self.tracker_socket.send(pickle.dumps({
                            'type': 'publish',
                            'data': files,
                        }))
                    case 'history':
                        file_name  = args_list[1]
                        self.tracker_socket.send(pickle.dumps({
                            'type': 'history',
                            'data': file_name,
                        }))
                    case 'reset':
                        file_name = args_list[1]
                        version = args_list[2]
                        self.tracker_socket.send(pickle.dumps({
                            'type': 'reset',
                            'data': (file_name, version),
                        }))
                    case 'block':
                        peer_ip = args_list[1]
                        peer_port = int(args_list[2])
                        self.tracker_socket.send(pickle.dumps({
                            'type': 'block',
                            'data': (peer_ip, peer_port),
                        }))
                    case 'unblock':
                        peer_ip = args_list[1]
                        peer_port = int(args_list[2])
                        self.tracker_socket.send(pickle.dumps({
                            'type': 'unblock',
                            'data': (peer_ip, peer_port),
                        }))
                    case 'quit':
                        peer_gui.print_message('Closing peer socket!\n')
                        if self.socket_for_upload: self.socket_for_upload.close()
                        self.tracker_socket.send(pickle.dumps({
                            'type': 'quit',
                            'data': None,
                        }))
                        self.tracker_socket.close()
                        return 'break'
                    case _:
                        peer_gui.print_message('Not a valid command!\n')
        except Exception as e: 
            peer_gui.print_message('command_handler stop\n')
            return 'break'
                
    def tracker_handler(self, peer_gui: Peer_GUI):
        host = "localhost"
        port = 65432
        self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tracker_socket.connect((host, port))
        self.tracker_socket.send(pickle.dumps({
            'type': 'connect',
            'data': self.get_files_information(),
        }))
        msg = pickle.loads(self.tracker_socket.recv(1024))
        msg_type = msg['type']
        msg_data = msg['data']
        if msg_type == 'connect_result':
            self.my_addr = msg_data
            peer_gui.print_message(f'Tracker successfully registered you at {self.my_addr[0]}:{self.my_addr[1]}\n\n')
            while True:
                try:
                    msg = pickle.loads(self.tracker_socket.recv(1024))
                    msg_type = msg['type']
                    msg_data = msg['data']
                    match msg_type:
                        case 'update':
                            self.tracker_socket.send(pickle.dumps({
                                'type': 'update_result',
                                'data': self.get_files_information(),
                            }))
                        case 'list_result':
                            print_str = f'Number of peers: {len(msg_data)}\n'
                            for i in range(len(msg_data)):
                                if msg_data[i] == tuple(self.my_addr):
                                    print_str += f'Peer {i+1} (you): {msg_data[i]}\n'     
                                elif msg_data[i] in self.blocked_peer:
                                    print_str += f'Peer {i+1} (blocked): {msg_data[i]}\n'
                                else:
                                    print_str += f'Peer {i+1}: {msg_data[i]}\n'
                            peer_gui.print_message(f'{print_str}\n')
                        case 'fetch_result':
                            if len(msg_data) == 0:
                                peer_gui.print_message('File not found!!\n\n')
                                continue
                            print_str = ''
                            for i in range(len(msg_data)):
                                print_str += f'{i + 1}: {msg_data[i]}\n'
                            peer_gui.print_message(f'\n{print_str}')
                            self.is_choosing = True
                            self.other_peer = msg_data
                            peer_gui.fetch_options(len(msg_data))
                        case 'history_result':
                            if len(msg_data) == 0:
                                peer_gui.print_message('File not found!!\n\n')
                                continue
                            print_str = ''
                            for i in range(len(msg_data)):
                                print_str += f'Version {i}: {msg_data[i]}\n'
                            peer_gui.print_message(f'{print_str}\n')
                        case 'reset_result':
                            file_name = msg_data[0]
                            file_data_encoded = msg_data[1]
                            if file_data_encoded is None:
                                peer_gui.print_message('File not found!!\n\n')
                                continue
                            file_data = base64.b64decode(file_data_encoded)
                            file_path = os.path.join(os.getcwd(), self.local_dir, file_name)
                            with open(file_path, 'wb') as f:
                                f.write(file_data)
                            peer_gui.print_message('File is reset\n\n!')
                        case 'block_result':
                            if msg_data is not None:
                                self.blocked_peer.append(msg_data)
                        case 'unblock_result':
                            if msg_data is not None:
                                self.blocked_peer.remove(msg_data)
                        case 'publish_result':
                            if msg_data is True:
                                peer_gui.print_message('Publishing completed!!\n\n')
                        case 'quit':
                            peer_gui.print_message('\nTracker is down!!\n', 'red')
                except Exception as e:
                    peer_gui.print_message('tracker_handler stop!!\n\n')
                    return
            
    def req_listener(self, peer_gui: Peer_GUI):
        self.socket_for_upload = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_for_upload.bind((self.my_addr[0],self.my_addr[1]+1))
        self.socket_for_upload.listen(5)
        peer_gui.print_message(f'Listening on {self.my_addr[0]}:{self.my_addr[1]+1}\n\n')

        def req_handler(req_socket: socket.socket):
            msg = pickle.loads(req_socket.recv(1024))
            msg_type = msg['type']
            msg_data = msg['data']
            if msg_type == 'fetch_peer':
                file_path = f'{self.local_dir}{msg_data}'
                try:
                    with open(file_path, 'rb') as file:
                        while True:
                            chuck = file.read(1024)
                            if not chuck: break
                            req_socket.send(chuck)
                            msg = req_socket.recv(1024).decode('utf-8')
                    req_socket.close()
                except Exception as e:
                    return
                req_socket.close()
                return
            return
        while True:
            try:
                req_socket, req_addr = self.socket_for_upload.accept()
                peer_gui.print_message(f'Accepted connection from {req_addr[0]}:{req_addr[1]}\n\n')
                threading.Thread(target=req_handler, args=[req_socket]).start()
            except Exception as e:
                peer_gui.print_message('req_listener stop!!\n\n')
                return
            
    def main(self):
        peer_gui = Peer_GUI()
        peer_gui.title("Peer terminal")
        peer_gui.bind("<Return>", lambda event, peer_gui = peer_gui: self.command_handler(peer_gui))
        threading.Thread(target=self.tracker_handler, args=[peer_gui]).start()
        while len(self.my_addr) == 0: 
            continue
        threading.Thread(target=self.req_listener, args=[peer_gui]).start()
        peer_gui.mainloop()

        
if __name__ == "__main__":
	(Peer()).main()