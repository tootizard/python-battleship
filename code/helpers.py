import sys
import time
import socket
import board
import ships
import subprocess

LINUX_PLATFORM = 'linux'
MACOS_PLATFORM = 'darwin'
WINDOWS_PLATFORM = 'win32'

SHIP_SUNK_CHAR = '*'

FLEET_SYMBOL_MAP = {
        'd' : 0,
        's' : 1,
        'c' : 2,
        'b' : 3,
        'a' : 4
    }

DISCONNECTED_STRING = "The other player has disconnected. Ending game..."

LENGTH_BYTES = 4

def get_terminal_clear_command():
    '''Return the command used to clear the terminal, for use with map rendering.'''
    platform = sys.platform
    if platform in [LINUX_PLATFORM, MACOS_PLATFORM]:
        return 'clear'
    # Windows
    return 'cls'

def notify_host(port):
    '''Dump the initial hosting notice.'''
    print()
    print(f'Awaiting connection over port {port}...')
    print()
    print('You must share your public IP address if playing over the internet.')
    print('Try https://ipchicken.com. You must also forward the port in your router.')
    print('If playing on the same network, use your private IP address.')
    print('Private IP address can be found with "ipconfig" in Windows CMD or "ip -br a" in Linux terminal.')

def get_client_connection(local_address, local_port):
    '''Start a server, await peer connection, return socket connection object'''
    server = socket.create_server((local_address,local_port))
    conn, addr = server.accept()
    server.close()
    return conn

def notify_client():
    '''Find out where the client wants to connect. return (address, port)'''
    while True:
        user_input = input('Enter IP address and port i.e. 99.123.45.60:5598 or "q" to quit: ')
        if user_input.lower() == 'q':
            exit()
        if ':' not in user_input:
            print('Invalid input, please enter IPADDRESS:PORT')
            continue
        address, port = user_input.split(':')
        port = int(port)
        return (address,port)

def get_host_connection(host_address):
    '''Attempt to connect to the host and return a socket object.
        host_address is tuple in form of (address, port).'''
    try:
        my_socket = socket.socket()
        my_socket.connect(host_address)
        return my_socket
    except:
        print('Error connecting to host...')
        print('Send the following to Jeremiah: ')
        print('')
        raise

def get_sunk_char(board, fleet_index):
    """Helper to retrieve the character for map render.
    return a single character, indicating that ship's sunk state."""
    if board.fleet[fleet_index].is_sunk:
        return '*'
    return ' '

def render_enemy_and_message(enemy_board, message):
    """Print the top half of the screen. The enemy board and game message."""
    print('''=================  Enemy Board ==================
      A   B   C   D   E   F   G   H   I   J
    + - + - + - + - + - + - + - + - + - + - +          ===== Message ==========''')
    for y in range(1, 11):
        if y != 10: # Accomodate the extra digit in "10"
            print(f' {y}  |', end="")
        else:
            print(f' {y} |', end="")
        for x in range(1, 11):
            if [y,x] in enemy_board.get_attacks():
                print(' {} |'.format('X'), end="")
            elif [y,x] in enemy_board.get_misses():
                print(' {} |'.format('O'), end="")
            else:
                print(' {} |'.format(' '), end="")
        if y == 1:
            print(f'           {message}')
        elif y == 8:
            print('          ===== Enemy Status =====')
        elif y == 9:
            if enemy_board.fleet[1].is_sunk:
                sunk_char = '*'
            else:
                sunk_char = ' '
            print('           {} Submarine'.format(sunk_char))
        elif y == 10:
            if enemy_board.fleet[3].is_sunk:
                sunk_char = '*'
            else:
                sunk_char = ' '
            print('           {} Battleship'.format(sunk_char))
        else:
            print()
        print('    + - + - + - + - + - + - + - + - + - + - +', end='')
        if y == 8:
            if enemy_board.fleet[0].is_sunk:
                sunk_char = '*'
            else:
                sunk_char = ' '
            print('           {} Destroyer'.format(sunk_char))
        elif y == 9:
            if enemy_board.fleet[2].is_sunk:
                sunk_char = '*'
            else:
                sunk_char = ' '
            print('           {} Cruiser'.format(sunk_char))
        elif y == 10:
            if enemy_board.fleet[4].is_sunk:
                sunk_char = '*'
            else:
                sunk_char = ' '
            print('           {} Aircraft Carrier'.format(sunk_char))
        else:
            print()

def render_my_board_and_legend(my_board):
    """Print out my board's ship placement, status, and symbol legend"""
    print('''=================  Your Board ===================
      A   B   C   D   E   F   G   H   I   J
    + - + - + - + - + - + - + - + - + - + - +          ===== Your Status =====''')
    for y in range(1, 11):
        if y != 10: # Accomodate the extra digit in "10"
            print(f' {y}  |', end="")
        else:
            print(f' {y} |', end="")
        for x in range(1, 11):
            # Obtain the correct symbol for this cell.
            symbol = ' '
            # Attacked coordinates supercede fleet symbols, unless the ship sank.
            if [y,x] in my_board.get_attacks():
                symbol = 'X'
            elif [y,x] in my_board.get_misses():
                symbol = 'O'
            for ship in my_board.fleet:
                if [y, x] in ship.get_positions():
                    # If the symbol hasn't been set yet or if the ship has been sunk,
                    # set the symbol for this cell.
                    if symbol == ' ' or ship.symbol == '*':
                        symbol = ship.symbol
            print(f' {symbol} |', end="")
        # Tack on the extra info.
        if y == 1:
            sunk_char = get_sunk_char(my_board, 0)
            print(f'           {sunk_char} Destroyer',end="")
        if y == 2:
            sunk_char = get_sunk_char(my_board,2)
            print(f'           {sunk_char} Cruiser',end="")
        if y == 3:
            sunk_char = get_sunk_char(my_board, 4)
            print(f'           {sunk_char} Aircraft Carrier',end="")
        if y == 6:
            print('          ====== Legend ========',end="")
        if y == 7:
            print('           X - Hit',end="")
        if y == 9:
            print('           S - Submarine - 3',end="")
        if y == 10:
            print('           B - Battleship - 4',end="")
        print()
        print('    + - + - + - + - + - + - + - + - + - + - +',end="")
        if y == 1:
            sunk_char = get_sunk_char(my_board, 1)
            print(f'           {sunk_char} Submarine',end="")
        if y == 2:
            sunk_char = get_sunk_char(my_board, 3)
            print(f'           {sunk_char} Battleship',end="")
        if y == 6:
            print('           O - Miss',end="")
        if y == 7:
            print('           * - Sunk ship',end="")
        if y == 8:
            print('           D - Destroyer - 2',end="")
        if y == 9:
            print('           C - Cruiser - 3',end="")
        if y == 10:
            print('           A - Aircraft Carrier - 5',end="")
        print()

def render_map(enemy_board, my_board, message):
    """Present the entire board, status, legend, map, etc."""
    render_enemy_and_message(enemy_board, message)
    render_my_board_and_legend(my_board)
    print() # Decided I wanted an extra line before inputs.

def place_ships(enemy_board, my_board, clear_command):
    """Lock user into the 'place ship' loop.
        Only break once the user locks in their ship positions."""
    # Have the user place their ships.
    extra_message = '' # I just need this somewhere before its called.
    while True:
        # If all ships are on the board, tell the user how to lock-in / ready-up.
        all_ships_placed = True
        for ship in my_board.fleet:
            if ship.get_positions() == []:
                all_ships_placed = False
                break
        if all_ships_placed:
            subprocess.call(clear_command, shell=True)
            render_map(enemy_board, my_board, "All ships on board. Lock in placement or re-place ships.")
            while True:
                user_input = input("Enter 'L' to lock in your placements or 'R' to re-place a ship: ")
                if user_input.lower() in ['l','r']:
                    break
                print("Invalid input: Please enter 'L' to lock-in or 'R' to replace.")
            # Check for lock-in again to break out of the outer loop.
            if user_input.lower() == 'l':
                break

        # Symbol of ship to place.
        subprocess.call(clear_command, shell=True)
        render_map(enemy_board, my_board, "Enter the symbol of the ship you'd like to place (see legend).")
        while True:
            if extra_message:
                print(extra_message)
                print()
            print("Ship symbol, example: 'D' for Destroyer.")
            user_input = input("You can replace a ship by entering its symbol again: ")
            if user_input.lower() not in ['d', 's', 'c', 'b', 'a']:
                print("Invalid input, please enter one ship symbol (see legend for symbols).")
                continue
            fleet_index = FLEET_SYMBOL_MAP[user_input]
            print(fleet_index)
            extra_message = ''
            break

        # Coordinate and direction.
        subprocess.call(clear_command, shell=True)
        render_map(enemy_board, my_board, "Enter your coordinate and direction.")
        while True:
            # Verify that coordinate.
            print("Coordinate and direction, for example, to place a Destroyer across A1 and A2")
            user_input = input("you could enter 'A1 down', 'a1 D', 'a2 Up' or 'A2 u': ")
            try:
                coordinate, direction = user_input.split(" ")
            except:
                print("Response must include a space. Example: 'B10 Up' or 'F9 Left'")
                continue
            if coordinate[0].lower() not in  ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']:
                print("First value in coordinate must be A-J. Example: 'C5' or 'F9'")
                continue
            try:
                temp = int(coordinate[1:])
            except:
                print("Second value in coordinate must be 1-10. Example 'A10' or 'h3'")
                continue
            if temp < 1 or temp > 10:
                print("Second value in coordinate must be 1-10. Example 'A10' or 'h3'")
                continue
            # Verify that direction.
            direction = direction.lower()
            if direction not in ['up', 'down', 'left', 'right', 'u', 'd', 'l', 'r']:
                print("Direction must be up, down, left, right, or the first letter of that direction.")
                continue
            # Process
            # 96 is the ascii value one lower than character 'a'.
            # We subtract it to map the letter to our coordinate system.
            # Also notice I swapped the coordinates.
            # We need them in y,x pairs so I had to change the order.
            coord = [temp, ord(coordinate[0].lower()) - 96]
            if direction in ['up','u']:
                temp = ships.UP
            elif direction in ['down','d']:
                temp = ships.DOWN
            elif direction in ['left','l']:
                temp = ships.LEFT
            else:
                temp = ships.RIGHT
            my_board.fleet[fleet_index].set_positions(coord, temp)
            if (not my_board.check_oob(my_board.fleet[fleet_index]) or
                not my_board.check_collision(my_board.fleet[fleet_index])):
                my_board.fleet[fleet_index].position_list=[] # Reset the positions
                extra_message = "Invalid placement, check other ship positions and board boundaries!"
            break

# Left off around here somewhere. Locking in ships stuck me in infinite loop.
def receive_with_dc_check(socket, length):
    """Receive data with connection close handling.
    Pass in a socket and the length of expected data bytestring.
    Return the data or close the app.
    """
    data = b''
    for i in range(length):
        temp_data = socket.recv(1)
        if not temp_data:
            print(DISCONNECTED_STRING)
            exit()
        data = data + temp_data
    return data

def clean_receive(socket, data_length):
    # Resolve length of data.
    len_bytes = receive_with_dc_check(socket, LENGTH_BYTES)
    length = int.from_bytes(len_bytes, byteorder='big')
    # Parse network data until length received.
    data = receive_with_dc_check(socket, length)
    return data

def clean_send(socket, data):
    """Send data prepended with message length."""
    length = len(data)
    length = length.to_bytes(LENGTH_BYTES, byteorder='big')
    socket.sendall(length+data)

if __name__ == '__main__':
    pass
