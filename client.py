from typing import Callable
import os, sys, time, base64, threading, re, importlib, socket, msvcrt, socket, ast, site

class Colors:
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"

class Terminal:
    input_buffer = ""
    window_id: tuple[int, int] = (0, 0)

    @staticmethod
    def clear():
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def flush_input_buffer():
        print("\r" + " " * (len(Terminal.input_buffer) + 2), end="\r")

    @staticmethod
    def print_input_buffer():
        print(f"\r> {Colors.UNDERLINE}{Terminal.input_buffer}{Colors.END} ", end="")

    @staticmethod
    def log_with_buffer(message: str):
        Terminal.flush_input_buffer()
        print(message)
        Terminal.print_input_buffer()

    @staticmethod
    def error(message: str):
        Terminal.log_with_buffer(f"{Colors.RED}ERROR: {message}{Colors.END}")

    @staticmethod
    def info(message: str):
        Terminal.log_with_buffer(f"{Colors.CYAN}INFO: {message}{Colors.END}")

    @staticmethod
    def recv_msg(name: str, message: str):
        for item in re.split(r"(@\w*)", message):
            if item.startswith("@") and " " not in item:
                if item == f"@{GlobalConnectionData.my_name}" or item == "@here":
                    message = message.replace(item, f"{Colors.YELLOW}{item}{Colors.END}")

        final = f"{Colors.BOLD}{Colors.LIGHT_CYAN}{name}{Colors.END}: {message}"
        if name == "SERVER":
            final = f"{Colors.BOLD}{Colors.RED}{name}{Colors.END}: {Colors.LIGHT_RED}{message}{Colors.END}"

        Terminal.log_with_buffer(f"{final}")

    @staticmethod
    def recv_whisper(name: str, message:str):
        Terminal.log_with_buffer(f"{Colors.BOLD}{Colors.LIGHT_GRAY}[WHISPER] {Colors.LIGHT_CYAN}{name} -> {GlobalConnectionData.my_name}{Colors.END}: {message}{Colors.END}")

    @staticmethod
    def recv_sent_whisper(name: str, message:str):
        Terminal.log_with_buffer(f"{Colors.BOLD}{Colors.LIGHT_GRAY}[WHISPER] {Colors.LIGHT_CYAN}{GlobalConnectionData.my_name} -> {name}{Colors.END}: {message}{Colors.END}")

    @staticmethod
    def recv_join(name: str):
        Terminal.log_with_buffer(f"{Colors.BOLD}{Colors.GREEN}{name} joined.{Colors.END}")

    @staticmethod
    def recv_left(name: str):
        Terminal.log_with_buffer(f"{Colors.BOLD}{Colors.RED}{name} left.{Colors.END}")

    @staticmethod
    def exit():
        while msvcrt.kbhit():
            try:
                msvcrt.getch()
            except:
                pass
        sys.exit()

class PackageManager:
    @staticmethod
    def safe_import(modules: dict[str, list[str]]):
        needed: list[dict[str, list[str]]] = []
        for module in modules:
            try:
                for m in modules[module]:
                    importlib.import_module(m)
            except ModuleNotFoundError:
                needed.append(module)

        if len(needed) != 0:
            Terminal.clear()
            print("Installing missing modules, please wait...")
            os.system(f"{sys.executable} -m pip install " + " ".join(needed))

        importlib.reload(site)

        for module in needed:
            for m in modules[module]:
                importlib.import_module(m)

modules = {"keyboard": ["keyboard"], "pywin32": ["win32gui", "win32process"]}
PackageManager.safe_import(modules)

import keyboard
import win32gui, win32process

class GlobalConnectionData:
    my_name = ""
    rooms: dict[int, str] = {}
    rooms_lock = threading.Lock()
    is_discovering = False

Terminal.clear()

class System:
    @staticmethod
    def get_ip() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        ip = ""
        try:
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    @staticmethod
    def is_focused():
        curr_window_id = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
        return curr_window_id == Terminal.window_id

class NetworkOptions:
    CHAT_PORT = 5432
    DISCOVER_PORT = 5431
    SEPERATOR = b"\0"
    RECV_SEND_LENGTH_SIZE = 4

class Network:
    @staticmethod
    def close(connection: socket.socket):
        connection.close()
        Terminal.exit()

    @staticmethod
    def discover_thread(ip: str):
        addr = (ip, NetworkOptions.DISCOVER_PORT)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)

        while GlobalConnectionData.is_discovering:
            try:
                s.connect(addr)
                s.sendto(b"DISCOVER", addr)

                data_room_name, verified_address = s.recvfrom(100)
                room_name = data_room_name.decode()

                server_ip: str = verified_address[0]
                room = int(server_ip.split(".")[3])

                with GlobalConnectionData.rooms_lock:
                    GlobalConnectionData.rooms[room] = room_name

            except:
                pass
            time.sleep(1)
        return

class Chat:
    def __init__(self, addr: tuple[str, int]):
        self.name = ""
        self.expected_messages: dict[str, Callable] = {}
        self.lock = threading.Lock()

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.client.settimeout(None)
            self.client.connect(addr)
        except:
            print(f"{Colors.RED}Couldn't connect, exiting...{Colors.END}")
            Terminal.exit()

        self.connected = True

        self.thread = threading.Thread(target=self.recv_thread)
        self.thread.start()

        self.keyboard = threading.Thread(target=self.keyboard_thread)

        self.get_name([])

        self.thread.join()

    def send_message(self, data: list[str]):
        message = NetworkOptions.SEPERATOR.join([d.encode() for d in data])
        length_message = str(len(message)).zfill(NetworkOptions.RECV_SEND_LENGTH_SIZE)
        self.client.sendall(length_message.encode() + message)

    def recv_thread(self):
        while self.connected:
            try:
                len_data_encoded = self.client.recv(NetworkOptions.RECV_SEND_LENGTH_SIZE)
                if len(len_data_encoded) == 0:
                    Terminal.error("Connection forcibly closed.")
                    Network.close(self.client)
                    return

                len_data = len_data_encoded.decode()
                length = int(len_data)

                data = "".encode()
                for _ in range(length):
                    new_data = self.client.recv(1)
                    if len(new_data) == 0:
                        Terminal.error("Connection forcibly closed.")
                        Network.close(self.client)
                        return

                    data += new_data

                if data.decode()[:NetworkOptions.RECV_SEND_LENGTH_SIZE] in self.expected_messages.keys():
                    message_data = [d.decode() for d in data.split(NetworkOptions.SEPERATOR)]
                    self.expected_messages[data.decode()[:NetworkOptions.RECV_SEND_LENGTH_SIZE]](message_data)
                else:
                    Terminal.error("Unexpected message: " + data.decode())
                    Network.close(self.client)
            except:
                Terminal.info("Connection closed.")
                Network.close(self.client)

    def keyboard_thread(self):
        def on_press(key_event):
            if not System.is_focused(): return

            key = key_event.name
            if len(key) == 1:
                Terminal.input_buffer += key
                Terminal.print_input_buffer()
            elif key == "enter":
                self.send_message(["SEND", Terminal.input_buffer])
                Terminal.flush_input_buffer()
                Terminal.input_buffer = ""
                Terminal.print_input_buffer()
            elif key == "backspace":
                Terminal.input_buffer = Terminal.input_buffer[:-1]
                Terminal.print_input_buffer()
            elif key == "space":
                Terminal.input_buffer += " "
                Terminal.print_input_buffer()

        def disconnect_ctrl_c():
            curr_window_id = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
            if curr_window_id != Terminal.window_id: return

            Terminal.info("Ctrl + C pressed, closing connection...")
            Network.close(self.client)

        keyboard.on_press(callback=on_press)
        keyboard.add_hotkey("ctrl+c", callback=disconnect_ctrl_c)

    def get_name(self, _: list[str]):
        name = ""
        while name == "":
            try:
                name = input(f"{Colors.CYAN}Enter your name: {Colors.YELLOW}")
            except:
                print(Colors.END, end="")
                Network.close(self.client)
            print(Colors.END, end="")

        self.name = name
        GlobalConnectionData.my_name = name

        self.expected_messages = {"OKNM": self.okay_name, "CHNM": self.change_name}
        self.send_message(["NAME", self.name])

    def change_name(self, _: list[str]):
        Terminal.error("Name is either invalid or someone with that name is already connected!")
        print("\r", end="")
        self.get_name(_)

    def okay_name(self, _: list[str]):
        Terminal.clear()

        self.expected_messages = {"CTUP": self.catch_up}
        self.send_message(["CTUP"])

    def catch_up(self, message_data: list[str]):
        all_messages_b64 = message_data[1]
        all_messages_bytes = base64.b64decode(all_messages_b64)
        all_messages_str = all_messages_bytes.decode()
        all_messages_list: list[dict[str, str]] = ast.literal_eval(all_messages_str)

        for data in all_messages_list:
            event = data["event"]

            if event == "join":
                name = data["name"]
                Terminal.recv_join(name)
            elif event == "left":
                name = data["name"]
                Terminal.recv_left(name)
            elif event == "message":
                name = data["name"]
                message = data["message"]
                Terminal.recv_msg(name, message)

        self.expected_messages = {"RECV": self.receive_message, "WSPR": self.receive_whisper, "WSNO": self.bad_whisper, "JOIN": self.user_join, "LEFT": self.user_left, "WSRC": self.sent_whisper}
        self.keyboard.start()
        Terminal.print_input_buffer()

    def receive_message(self, message_data: list[str]):
        name = message_data[1]
        message = message_data[2]
        Terminal.recv_msg(name, message)

    def receive_whisper(self, message_data: list[str]):
        name = message_data[1]
        message = message_data[2]
        Terminal.recv_whisper(name, message)

    def sent_whisper(self, message_data: list[str]):
        name = message_data[1]
        message = message_data[2]
        Terminal.recv_sent_whisper(name, message)

    def bad_whisper(self, _: list[str]):
        Terminal.error(f"{Colors.LIGHT_GRAY}[WHISPER] {Colors.RED}That user isn't connected.")

    def user_join(self, message_data: list[str]):
        name = message_data[1]
        Terminal.recv_join(name)

    def user_left(self, message_data: list[str]):
        name = message_data[1]
        Terminal.recv_left(name)

def print_discover_menu():
    Terminal.clear()

    print(f"{Colors.LIGHT_CYAN}Welcome to ClassChat!{Colors.END}")
    print(f"{Colors.LIGHT_CYAN}Discovery is {f'{Colors.GREEN}ACTIVE' if GlobalConnectionData.is_discovering else f'{Colors.YELLOW}PAUSED'}{Colors.END}")

    print("")

    if len(GlobalConnectionData.rooms.keys()) == 0:
        print(f"{Colors.RED}No open rooms found{' (yet)' if GlobalConnectionData.is_discovering else ''}.{Colors.END}", end="\n\n")

    print(f"{Colors.LIGHT_WHITE}[0] {Colors.LIGHT_CYAN}Manual join code{Colors.END}")

    for index, (code, name) in enumerate(GlobalConnectionData.rooms.items()):
        print(f"{Colors.LIGHT_WHITE}[{index + 1}] {Colors.GREEN}{name}{Colors.END}")

    if not GlobalConnectionData.is_discovering:
        print(f"\n{Colors.LIGHT_WHITE}[r] {Colors.YELLOW}Continue discovering...{Colors.END}")

    print("\n> ", end="")

def discover():
    GlobalConnectionData.is_discovering = True

    def stop_discovering(key_event: keyboard.KeyboardEvent):
        if not System.is_focused(): return

        key = key_event.name
        if key == None: return

        if len(key) == 1:
            if GlobalConnectionData.is_discovering:
                GlobalConnectionData.is_discovering = False
                print_discover_menu()

    keyboard.on_press(callback=stop_discovering)

    start_ip = ".".join(System.get_ip().split(".")[:3]) + "."
    code = 0

    for i in range(1, 255):
        ip = start_ip + str(i)
        threading.Thread(target=Network.discover_thread, args=(ip,)).start()

    time.sleep(0.1)

    prev_rooms = GlobalConnectionData.rooms.copy()
    prev_discovering = GlobalConnectionData.is_discovering

    while GlobalConnectionData.is_discovering:
        print_discover_menu()

        while prev_rooms == GlobalConnectionData.rooms and prev_discovering == GlobalConnectionData.is_discovering:
            time.sleep(0.1)

        prev_rooms = GlobalConnectionData.rooms.copy()
        prev_discovering = GlobalConnectionData.is_discovering

    time.sleep(0.05)

    try:
        fail = True
        while fail:
            try:
                picked = input("\r> ")
                if picked == "r":
                    discover()
                picked = int(picked)
                fail = False
                if picked == 0:
                    try:
                        code = int(input(f"{Colors.CYAN}Enter join code: {Colors.YELLOW}"))
                    except:
                        print(Colors.END, end="")
                        Terminal.exit()

                    print(Colors.END, end="")
                elif picked <= len(GlobalConnectionData.rooms.keys()):
                    code = list(GlobalConnectionData.rooms.keys())[picked - 1]
                else:
                    print(f"{Colors.RED}You are being stupid!{Colors.END}")
                    fail = True

            except KeyboardInterrupt:
                Terminal.exit()

            except:
                Terminal.exit()

    except:
        Terminal.exit()

    Chat((f"{start_ip}{code}", NetworkOptions.CHAT_PORT))

def main():
    Terminal.window_id = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())

    discover()

if __name__ == "__main__":
    main()
