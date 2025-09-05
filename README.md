# ClassChat

**A simple, real-time chat application for classroom communication.**

ClassChat is a Python-based server-client chat system designed to facilitate communication between classmates in a local network. This project was created to provide a fun and practical way for us and our classmates to talk, collaborate, and share messages during class or group study sessions.

## Why We Made This

The idea behind ClassChat came from a desire to create a lightweight, easy-to-use tool that allows us to chat with our classmates without relying on external platforms. Whether it's coordinating group projects, asking quick questions, or just staying connected during class downtime, ClassChat provides a private and localized solution tailored to our needs. Plus, it was a great opportunity to dive into network programming and build something useful together!

## Features

### Server Features
- **Customizable Server Setup**: Set a server name and maximum number of participants.
- **Real-Time Messaging**: Broadcast messages to all connected clients or send private whispers to specific users.
- **Moderation Tools**: Kick or ban users by IP or name, unban users, and clear the chat history.
- **Command System**: Use commands like `say`, `tell`, `list`, `kick`, `ban`, `unban`, `clear`, and `exit` to manage the server.
- **Spam Protection**: Limits message frequency to prevent flooding.
- **Chat History**: Maintains a log of messages and events (joins/leaves) with a configurable cutoff.
- **Discovery Mode**: Optionally advertise the server name for clients to find it on the network.

### Client Features
- **Simple Interface**: A terminal-based UI with colored output for readability (e.g., messages, whispers, join/leave notifications).
- **Whisper Functionality**: Send private messages to specific users with `/msg` or `/send`.
- **Chat Catch-Up**: New clients receive the recent chat history upon joining.
- **Mention Highlights**: Messages mentioning your name (e.g., `@yourname`) or `@here` are highlighted in yellow.
- **Smooth Typing**: Real-time input buffer with backspace and enter key support.
- **Discovery System**: Automatically detect available servers on the local network or join manually with a code.

### General Features
- **Cross-Platform**: Works on Windows (with `pywin32`) and other systems (with minor adjustments).
- **Dependency Management**: Automatically installs missing Python modules (`keyboard`, `pywin32`) on first run.
- **Local Network Focus**: Uses IP-based communication, ideal for classroom or LAN settings.

## How It Works

ClassChat operates as a client-server application:
1. **Server**: One user runs the `server.py` script to host the chat. It listens for client connections on a specified port (default: 5432) and manages the chat session.
2. **Client**: Other users run the `client.py` script to connect to the server using its IP-based join code. Clients can discover servers on the same network or manually enter a code.

The server handles message broadcasting, private whispers, and moderation, while the client provides a user-friendly interface for sending and receiving messages.

## Prerequisites

- **Python 3.x**: Ensure Python is installed on your system.
- **Modules**: The script auto-installs required libraries (`keyboard`, `pywin32`), but you can manually install them with:
  ```bash
  pip install keyboard pywin32
  ```
- **Windows**: `pywin32` is used for window focus detection; on non-Windows systems, you may need to adapt the code.

## Setup and Usage

### Running the Server
1. Save the server code as `server.py`.
2. Open a terminal and navigate to the directory containing `server.py`.
3. Run the script:
   ```bash
   python server.py
   ```
4. Enter the maximum number of participants and a server name (leave blank for a private server).
5. Share the **join code** (the last octet of your IP, e.g., `123` from `192.168.1.123`) with classmates.

### Joining as a Client
1. Save the client code as `client.py`.
2. Open a terminal and navigate to the directory containing `client.py`.
3. Run the script:
   ```bash
   python client.py
   ```
4. The client will attempt to discover servers on the network:
   - Select a server from the list (e.g., `[1]`) or press `[0]` to enter a join code manually.
5. Enter your name and start chatting!

## Server Commands

The server provides a command-line interface for managing the chat session. Commands are typed into the server terminal and executed when you press Enter. Below is a detailed list of all available commands:

- **`kick <name/ip>`**
  - **Description**: Disconnects a specific client from the server.
  - **Arguments**: The client’s name (e.g., `Alice`) or IP address (e.g., `192.168.1.100`).
  - **Example**: `kick Alice`
  - **Result**: Alice is disconnected, and a message is logged: `[WARNING] Kicked Alice - 192.168.1.100`. If the name or IP isn’t found, an error is logged.

- **`ban <name/ip>`**
  - **Description**: Disconnects a client and bans their IP, preventing them from reconnecting until unbanned.
  - **Arguments**: The client’s name or IP address.
  - **Example**: `ban 192.168.1.100`
  - **Result**: The client is kicked, their IP is added to the banned list, and a message is logged: `[WARNING] Ban Ip <name> - 192.168.1.100`.

- **`unban <ip>`**
  - **Description**: Removes an IP from the banned list, allowing that client to reconnect.
  - **Arguments**: The IP address to unban (e.g., `192.168.1.100`).
  - **Example**: `unban 192.168.1.100`
  - **Result**: The IP is unbanned, and a message is logged: `[WARNING] Unbanned ip 192.168.1.100`. If the IP isn’t banned, an error is logged.

- **`say <message>`**
  - **Description**: Broadcasts a message to all connected clients as "SERVER".
  - **Arguments**: The message text (multiple words allowed).
  - **Example**: `say Hello everyone!`
  - **Result**: All clients see: `SERVER: Hello everyone!`, and the server logs: `[INFO] Brodcasted message: Hello everyone!`.

- **`tell <name/ip> <message>`**
  - **Description**: Sends a private whisper to a specific client from "SERVER".
  - **Arguments**: The client’s name or IP, followed by the message.
  - **Example**: `tell Bob How’s it going?`
  - **Result**: Bob receives: `[WHISPER] SERVER -> Bob: How’s it going?`, and the server logs: `[DEBUG] Whispered to Bob: How’s it going?`. If the name/IP isn’t found, an error is logged.

- **`list`**
  - **Description**: Displays a list of all connected clients.
  - **Arguments**: None.
  - **Example**: `list`
  - **Result**: Logs the number of clients and their details, e.g., `[INFO] 2 client(s) connected: -192.168.1.100 - Alice, -192.168.1.101 - Bob`.

- **`clear`**
  - **Description**: Erases the server’s chat history.
  - **Arguments**: None.
  - **Example**: `clear`
  - **Result**: The chat history is wiped, and the server logs: `[INFO] Cleared chat!`. New clients will no longer see past messages.

- **`exit`**
  - **Description**: Shuts down the server and disconnects all clients.
  - **Arguments**: None.
  - **Example**: `exit`
  - **Result**: The server closes, all client connections are terminated, and the program exits after cleanup.

- **Notes**:
  - Commands are case-sensitive and must be typed exactly as shown.
  - If an invalid command is entered (e.g., `xyz`), the server logs: `[ERROR] Unknown Command!`.

## Client Commands

- **`/msg <name> <message>` or `/send <name> <message>`**
  - Sends a private whisper to the specified user.
  - Example: `/msg Alice Hi there!`
  - Result: Alice sees a whisper; you see a confirmation.
- **Press `Ctrl+C`**: Disconnects from the server gracefully.

## Example Usage

**Server:**
```
> python server.py
Please enter the max participants: 10
Please enter server name: ClassChat101
[INFO] 2025-03-10 12:00:00: Starting up server...
[INFO] 2025-03-10 12:00:01: SERVER JOIN CODE: 123
>>> say Welcome to ClassChat101!
[INFO] 2025-03-10 12:00:02: Brodcasted message: Welcome to ClassChat101!
```

**Client:**
```
> python client.py
Welcome to ClassChat!
Discovery is ACTIVE

[0] Manual join code
[1] ClassChat101

> 1
Enter your name: Alice
SERVER: Welcome to ClassChat101!
Alice: Hello everyone!
```

## Limitations

- **Local Network Only**: Designed for LAN use; no internet support.
- **Windows-Centric**: Focus detection relies on `pywin32`, which may not work as-is on Linux/Mac.
- **Basic UI**: Terminal-based; no graphical interface.
- **No Encryption**: Messages are sent in plain text over the network.

## Future Ideas

- Implement message encryption for privacy.
- Support file sharing between clients.
- Extend to work over the internet with port forwarding or a relay server.

## Contributing

Feel free to fork this project, submit pull requests, or suggest improvements! This was a collaborative effort between [Your Name] and AlonHor, and we’d love to see how others can build on it.

## License

This project is open-source and available under the [MIT License](LICENSE).
