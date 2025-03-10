import base64
import datetime
import socket
import threading
import os
import sys
import importlib
import site
import msvcrt
import time


class PackageManager:
    @staticmethod
    def safe_import(modules: set[str]):
        needed = []
        for module in modules:
           try:
               for m in modules[module]:
                   importlib.import_module(m)
           except ModuleNotFoundError:
               needed.append(module)

        if len(needed) != 0:
            os.system("cls" if os.name == "nt" else "clear")
            print("Installing missing modules... please wait.")
            os.system(f"{sys.executable} -m pip install " + " ".join(needed))

        importlib.reload(site)
        
        for module in needed:
            for m in modules[module]:
                importlib.import_module(m)

modules = {
    "keyboard": ["keyboard"],
    "pywin32": ["win32gui", "win32process"]
}
PackageManager.safe_import(modules)
import keyboard
import win32gui
import win32process

client_lock = threading.Lock()

class Terminal:
    curr_input_buff = ""

    @staticmethod
    def clear():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def log_info(message):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Colors.INFO_COLOR}[INFO] {current_time}: {message}{Colors.RESET}")
        Terminal.print_input_buff()

    @staticmethod
    def log_warning(message):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Colors.WARNING_COLOR}[WARNING] {current_time}: {message}{Colors.RESET}")
        Terminal.print_input_buff()

    @staticmethod
    def log_error(message):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Colors.ERROR_COLOR}[ERROR] {current_time}: {message}{Colors.RESET}")
        Terminal.print_input_buff()

    @staticmethod
    def log_debug(message):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{Colors.DEBUG_COLOR}[DEBUG] {current_time}: {message}{Colors.RESET}")
        Terminal.print_input_buff()

    @staticmethod
    def print_input_buff(length=None):
        length = length if length else len(Terminal.curr_input_buff)
        print(" " * (length + 4), end="\r")
        print(f">>> {Terminal.curr_input_buff} ", end="\r", flush=True)

    @staticmethod
    def on_key_press(key_event):
        if not chat_obj: return
        if not is_window_focused(): return

        with client_lock:
            key = key_event.name
            if len(key) == 1:
                Terminal.curr_input_buff += key
            elif key == "enter":
                chat_obj.handle_command(Terminal.curr_input_buff)
                prev_len = len(Terminal.curr_input_buff)
                Terminal.curr_input_buff = ""
                Terminal.print_input_buff(prev_len)
            elif key == "backspace":
                Terminal.curr_input_buff = Terminal.curr_input_buff[:-1]
            elif key == "space":
                Terminal.curr_input_buff += " "
            else:
                return

            Terminal.print_input_buff()


class Colors():
    RESET = "\033[0m"
    INFO_COLOR = "\033[94m"
    WARNING_COLOR = "\033[93m"
    ERROR_COLOR = "\033[91m"
    DEBUG_COLOR = "\033[90m"


class ChatOptions():
    SEP = b"\0"
    PORT = 5432
    DISCOVER_PORT = 5431
    MSG_CUTOFF = 20
    SPAM_TIME_WINDOW_SEC = 3
    MAX_MESSAGES_IN_SPAM_WINDOW = 3

Terminal.clear()
CURR_WINDOW_PID = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
chat_obj = None

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def is_window_focused():
    if CURR_WINDOW_PID == win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow()):
        return True
    return False


class ChatServer:
    def __init__(self):
        Terminal.log_info("Starting up server...")
        code = get_ip().split(".")[-1]
        Terminal.log_info(f"SERVER JOIN CODE: {Colors.ERROR_COLOR}{code}{Colors.RESET}")

        mpart = int(input("Please enter the max participants: "))
        self.server_name = input("Please enter server name (Press Enter to make private server): ")

        self.server = socket.socket()
        self.server.bind(("0.0.0.0", ChatOptions.PORT))
        self.server.listen(mpart)


        self.clients = {}
        self.chat = []
        self.banned_client_ips = []
        self.msg_times_window = []

        self.open = True

    def close_server(self):
        if not is_window_focused(): return
        try:
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
        except OSError:
            print("Faild to shutdown server socket...")
    
        with client_lock:
            self.open = False

        print("Closing clients...")
        print("Closing threads...")
        for c in self.clients.values():
            c['socket'].shutdown(socket.SHUT_RDWR)
            c['socket'].close()
        self.clients = {}
        print("Closing server...")
        print("Shutting down...")
        
        print("Releasing listening thread...")
        s = socket.socket()
        s.connect(("127.0.0.1", ChatOptions.PORT))
        s.close()
        
        print("Flushing input buffer...")
        while msvcrt.kbhit():
            try:
                msvcrt.getch()
            except:
                pass

    def send_message(self, to, parts):
        body = ChatOptions.SEP.join([p.encode() for p in parts])
        msg = f"{len(body):04}"
        if to == "brd":
            for c in self.clients.values():
                try:
                    c["socket"].sendall(msg.encode() + body)
                except Exception:
                    pass

        else:
            if type(to) == str:
                client = self.clients.get(to)["socket"]
            else:
                client = to
            if not client:
                Terminal.log_warning("Tried sending a message to an IP that is not registered!")
                return False

            try:
                client.sendall(msg.encode() + body)
            except Exception:
                pass

    def recieve_message(self, from_ip):
        try:
            client = self.clients.get(from_ip)
            soc = client['socket'] if client else from_ip
            client_ip = from_ip if client else from_ip.getpeername()

            if client and client["disconnect_c"] == 3:
                Terminal.log_debug(f"{from_ip} has sent 3 empty packets")
                return None

            if not client:
                Terminal.log_warning("Tried sending a message to an IP that is not registered!")

            msg_len = soc.recv(4)
            if len(msg_len) == 0:
                Terminal.log_debug(f"{client_ip} sent an empty packet")
                if client:
                    self.clients[from_ip]["disconnect_c"] += 1
                else:
                    return None
                return False

            msg_len = msg_len.decode()
            if not msg_len.isdigit():
                Terminal.log_error(f"Got an invalid packet length from {client_ip} - {client['name']} ({msg_len})!")
                return False
            data = soc.recv(int(msg_len))

            if len(data) == 0:
                Terminal.log_debug(f"{client_ip} sent an empty packet")
                if client:
                    self.clients[from_ip]["disconnect_c"] += 1
                else:
                    return None
                return False

            if client: self.clients[from_ip]["disconnect_c"] = 0
            return [d.decode() for d in data.split(ChatOptions.SEP)]
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            return None

    def __is_name_in_use(self, name):
        for c in self.clients.values():
            if c["name"] == name:
                return True
        return False

    def register_client(self, ip, port, soc):
        tries = 0
        while tries < 3 and self.open:
            tries += 1
            Terminal.log_info(f"Got connection from {ip}:{port}, waiting for name ({tries}/3)...")
            data = self.recieve_message(soc)
            if data is None:
                return None
            if data == False: continue
            if data[0] != "NAME":
                Terminal.log_error("Invalid name packet! skipping...")
                continue
            name = data[1]

            if self.__is_name_in_use(name) or name == "SERVER" or ' ' in name:
                self.send_message(soc, ["CHNM"])
                Terminal.log_warning(f"{ip} tried using the name \"{name}\", requested change.")
                continue

            self.send_message(soc, ["OKNM"])
            self.clients[ip] = {
                "name": name,
                "socket": soc,
                "disconnect_c": 0
            }
            Terminal.log_info(f"Successfully registered a new client ({ip} - {name})")

            return True

        Terminal.log_error("Failed to register user, disconnecting...")
        soc.close()
        return None

    def __is_spam(self):
        # Advance window
        curr_sec = time.time() - ChatOptions.SPAM_TIME_WINDOW_SEC
        new_times = []
        for msg_time in self.msg_times_window:
            if msg_time > curr_sec:
                new_times.append(msg_time)
        new_times.append(curr_sec+1)
        self.msg_times_window = new_times

        if len(new_times) >= ChatOptions.MAX_MESSAGES_IN_SPAM_WINDOW:
            return True

        return False

    def handle_client(self, ip, port, soc):
        if ip == "127.0.0.1":
            return
        succ = self.register_client(ip, port, soc)
        if not succ:
            Terminal.log_error(f"{ip} failed to connect.")
            soc.shutdown(socket.SHUT_RDWR)
            soc.close()
            return

        client_data = self.clients.get(ip)
        if client_data is None:
            Terminal.log_error(f"Invalid client! ignoring.")
            return

        while self.open and ip in self.clients:
            data = self.recieve_message(ip)
            try:
                if data is None:
                    Terminal.log_warning(f"Client disconnected ({ip}) successfully!")
                    self.clients[ip]["socket"].close()
                    if ip in self.clients: del self.clients[ip]
                    self.send_message("brd", ["LEFT", client_data['name']])
                    self.chat.append({
                        "event": "left",
                        "name": client_data['name']
                    })
                    break

                if data == False:
                    continue

                action = data[0]

                if action == "SEND":
                    if self.__is_spam():
                        continue

                    try:
                        if data[1].startswith("/msg ") or data[1].startswith("/send "):  # Whisper functionality
                            to = data[1].split(" ", 2)[1]
                            msg = ' '.join(data[1].split(" ")[2:])
                            for (i, c) in self.clients.items():
                                if to == c['name']:
                                    self.send_message(i, ["WSPR", client_data['name'], msg])
                                    self.send_message(ip, ["WSRC", c['name'], msg])
                                    Terminal.log_debug(f"{client_data['name']} -> {c['name']}: {msg}")
                                    break
                            else:
                                self.send_message(ip, ["WSNO"])
                                Terminal.log_warning(
                                    f"{client_data['name']} - {ip} tried to whisper to {to} which is not a valid client")
                            continue
                    except Exception:
                        pass

                    if data[1].strip() == "": continue

                    self.chat.append({
                        "event": "message",
                        "name": client_data["name"],
                        "message": data[1]
                    })

                    self.send_message("brd", ["RECV", client_data["name"], data[1]])
                    Terminal.log_debug(f"Message by {ip} - {client_data["name"]}: {data[1]}")

                elif action == "CTUP":
                    chat_serialized = self.chat if len(self.chat) <= ChatOptions.MSG_CUTOFF else self.chat[
                                                                                                :ChatOptions.MSG_CUTOFF]
                    chat_b64 = base64.b64encode(str(chat_serialized).encode())
                    self.send_message(ip, ["CTUP", chat_b64.decode()])
                    self.send_message("brd", ["JOIN", client_data['name']])
                    self.chat.append({
                        "event": "join",
                        "name": client_data['name']
                    })
            except Exception:
                return None

    def accept_clients(self):
        s = self.server
        while self.open:
            soc, addr = s.accept()
            if addr[0] in self.banned_client_ips:
                Terminal.log_warning(f"{addr[0]} tried joining the server while banned.")
                self.send_message(soc, ["RECV", "SERVER", "You are IP banned for this session."])
                soc.shutdown(socket.SHUT_RDWR)
                soc.close()
                continue

            thread = threading.Thread(target=self.handle_client, args=(addr[0], addr[1], soc,), daemon=True)
            thread.start()
            

    def handle_command(self, cmd):
        parts = cmd.split(" ")
        if parts[0] == "kick" and len(parts) == 2:
            for (ip, c) in self.clients.items():
                if ip == parts[1] or c["name"] == parts[1]:
                    Terminal.log_warning(f"Kicked {c["name"]} - {ip}")
                    c["socket"].shutdown(socket.SHUT_RDWR)
                    c["socket"].close()
                    if ip in self.clients: del self.clients[ip]
                    break
            else:
                Terminal.log_error(f"Could not find client with name/ip of {parts[1]}")

        elif parts[0] == "ban" and len(parts) == 2:
            for (ip, c) in self.clients.items():
                if ip == parts[1] or c["name"] == parts[1]:
                    Terminal.log_warning(f"Ban Ip {c["name"]} - {ip}")
                    c["socket"].shutdown(socket.SHUT_RDWR)
                    c["socket"].close()
                    if ip in self.clients: del self.clients[ip]
                    self.banned_client_ips.append(ip)
                    break
            else:
                Terminal.log_error(f"Could not find client with name/ip of {parts[1]}")

        elif parts[0] == "unban" and len(parts) == 2:
            if parts[1] in self.banned_client_ips:
                Terminal.log_warning(f"Unbanned ip {parts[1]}")
                self.banned_client_ips.remove(parts[1])
            else:
                Terminal.log_error(f"Could not find client with name/ip of {parts[1]}")

        elif parts[0] == "say":
            msg = " ".join(parts[1:])
            self.chat.append({
                "event": "message",
                "name": "SERVER",
                "message": msg
            })
            Terminal.log_info(f"Brodcasted message: {msg}")
            self.send_message("brd", ["RECV", "SERVER", msg])

        elif parts[0] == "list":
            Terminal.log_info(f"{len(self.clients.keys())} client(s) connected:")
            for (ip, c) in self.clients.items():
                Terminal.log_info(f"\t-{ip} - {c['name']}")

        elif parts[0] == "tell":
            to = parts[1]
            msg = ' '.join(parts[2:])
            for (ip, c) in self.clients.items():
                if to == c['name'] or to == ip:
                    self.send_message(ip, ["WSPR", "SERVER", msg])
                    Terminal.log_debug(f"Whispered to {c['name']}: {msg}")
                    break
            else:
                Terminal.log_error(f"Could not find client with name/ip of {parts[1]}")

        elif parts[0] == "clear":
            Terminal.log_info(f"Cleared chat!")
            self.chat[:] = []

        elif parts[0] == "exit":
            self.close_server()

        else:
            Terminal.log_error("Unknown Command!")

    def discover_process(self):
        if self.server_name == "": return

        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(("0.0.0.0", ChatOptions.DISCOVER_PORT))
        while self.open:
            try:
                data, addr = self.server.recvfrom(8)
                if data == b"DISCOVER":
                    self.server.sendto(self.server_name.encode(), addr)
            except (KeyboardInterrupt, Exception):
                return


if __name__ == "__main__":
    chat_obj = ChatServer()
    Terminal.print_input_buff()

    client_accept_thread = threading.Thread(target=chat_obj.accept_clients, daemon=True)
    client_accept_thread.start()

    server_discover_thread = threading.Thread(target=chat_obj.discover_process, daemon=True)
    server_discover_thread.start()

    keyboard.on_press(Terminal.on_key_press)

    server_discover_thread.join()
    client_accept_thread.join()
