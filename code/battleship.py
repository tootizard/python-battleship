''' Overview
Determine Operating System (used for terminal/cmd prompt commands).
Ask if user will host or join.

If Host: present user with public IP and port (UPNP?), spawn socket and listen for connection (asynchronous) provide user option to cancel/quit.
    Also spawn a join socket on localhost. - Every Host has its own client but every client must not host...    <- Fork process or some sort of asynch hosting? OR do we do peer-to-peer instead of client server?
If Join: ask user for public IP and port and spawn socket, attempt to connect to Host (asynchronous) provide user option to cancel/quit.
In both situations, attempt to connect until timeout interval, notify user of timeout and provide retry/quit option.

Present user with the game board.
Tell user to place their ships.
    Send ship, coord, and direction to host.
    Client awaits confirmation from host, True = move on, False = replace/tell user it wasn't placed.
Host recieves placement data, checks oob and collision.
    Host sends bool back, True = placement success. False indicates replacement.
Client waits for start game signal from host.

Once ships are placed from all players, host sends 'start game' signal to both clients.

Clients receive start game signal from host.
One client is chosen to start with the "your turn signal".

Game Loop:
    That client asks user to enter a coordinate pair. And confirms choice.
    That client then sends the coordinate to the host.
        Accomodate out-of-bounds?
    That client updates their map-render.

    Host calls attack on other client's board and ships.
    Host passes attack to other client.

    Other client receives attack, updates own map render.

    Other client prompts for attack.
        Repeat until all ships are dead on one board.

Notify clients who won the game.
'''

# ===== Imports =====
import helpers
import subprocess
import time
import threading
import socket
import board
import ships
import pickle

# ===== Constants =====
LOCAL_ADDRESS = '0.0.0.0' # Bind to all
PORT = 5598 # Arbitrary
ALL_PLACED = b'ALL PLACED'
START_GAME = b'START GAME'
HIT = GOOD = b'1' # Good is a "good" response, use it to tell your peer their turn is over.
MISS = BAD = b'0' # Bad is a "bad" response, use it to ask the peer for their coordinate again.
HM_LENGTH = 2 # First byte for hit/miss, second for fleet index of hit ship.
ATTACK_PICKLE_BUFFER_LENGTH = 64

# ===== Global Varibles =====
user_input = '' # A string to hold our user input.
host_flag = None
network_data = b'' # A byte object to hold network transmissions.

# ===== Code =====
# Figure out how to clear their screen, clear the terminal and present first prompt.
clear_command = helpers.get_terminal_clear_command()
subprocess.call(clear_command, shell=True)
print('----- Python BattleShip! -----')

while True:
    user_input = input('Enter "h" to host a match or "j" to join one: ')
    user_input = user_input.lower()
    if user_input not in ('h','j'):
        print('Invalid input, please enter "h" or "j" without quotation marks.')
    else:
        break

# Process host or join response.
if user_input == 'h':
    # Hosting!
    host_flag = True
    helpers.notify_host(PORT)
    peer_connection = helpers.get_client_connection(LOCAL_ADDRESS, PORT)
#    print(peer_connection)
else:
    # Joining!
    host_flag = False
    host_address = helpers.notify_client()
    peer_connection = helpers.get_host_connection(host_address)
#    print(peer_connection)

# Create the boards.
enemy_board = board.Board()
my_board = board.Board()

helpers.place_ships(enemy_board, my_board, clear_command)
subprocess.call(clear_command, shell=True)
helpers.render_map(enemy_board, my_board, "Waiting for peer to place ships...")

# Send ready, await start message.
# Prep your_turn variable.
if not host_flag:
#    peer_connection.sendall(ALL_PLACED)
    helpers.clean_send(peer_connection, ALL_PLACED)
    data = helpers.clean_receive(peer_connection, len(START_GAME))
    # Client goes first.
    your_turn = True
else:
    data = helpers.clean_receive(peer_connection, len(ALL_PLACED))
#    print(data)
#    peer_connection.sendall(START_GAME)
    helpers.clean_send(peer_connection, START_GAME)
    # Host goes second.
    your_turn = False

# Enter the game loop.
while True:
    subprocess.call(clear_command, shell=True)
    if your_turn:
        helpers.render_map(enemy_board, my_board, "Your turn, attack!")
        print("Enter the coordinate you'd like to attack.")
        attack_coord = []
        while True:
            user_input = input("Coordinate, for example, 'A1' or 'g10': ")
            # Check for a good coordinate.
            if user_input[0].lower() not in  ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']:
                print("First value in coordinate must be A-J. Example: 'C5' or 'F9'")
                continue
            try:
                temp = int(user_input[1:])
            except:
                print("Second value in coordinate must be 1-10. Example 'A10' or 'h3'")
                continue
            if temp < 1 or temp > 10:
                print("Second value in coordinate must be 1-10. Example 'A10' or 'h3'")
                continue
            # 96 is the ascii value one lower than character 'a'.
            # We subtract it to map the letter to our coordinate system.
            # Also notice I swapped the coordinates.
            # We need them in y,x pairs so I had to change the order.
            attack_coord = [temp, ord(user_input[0].lower()) - 96]
            # Prevent repeat attacks.
            if attack_coord in enemy_board.hit_list or attack_coord in enemy_board.miss_list:
                print("You already attacked there! Try another location.")
                continue
            break
        serialized_coord = pickle.dumps(attack_coord)
#        peer_connection.sendall(serialized_coord)
        helpers.clean_send(peer_connection, serialized_coord)
        data = helpers.clean_receive(peer_connection, HM_LENGTH)
        # Check hit or miss
        if data[0:1] == HIT: # Slice instead of index. Return bytestring instead of int.
            enemy_board.hit_list.append(attack_coord)
            # Check if a ship sank.
            if len(data) == 2:
                fleet_index = int.from_bytes(data[1:2], byteorder='big') # Slice instead of index. Return bytestring instead of int.
                try:
                    enemy_board.fleet[fleet_index].is_sunk = True
                    enemy_board.fleet[fleet_index].symbol = '*'
                except:
                    pass
        else:
            enemy_board.miss_list.append(attack_coord)
        your_turn = False
    else:
        # Wait for the attack, deserialize, and check for damage.
        helpers.render_map(enemy_board, my_board, "Not your turn, awaiting peer attack...")
        print("Peer's turn, waiting for their attack...")
        serialized_coord = helpers.clean_receive(peer_connection, ATTACK_PICKLE_BUFFER_LENGTH)
        coord = pickle.loads(serialized_coord)
        is_hit = my_board.attack(coord)
        if is_hit:
            if type(is_hit) == tuple:
                fleet_index = is_hit[1].to_bytes(1, byteorder='big')
#                peer_connection.sendall(HIT+fleet_index)
                helpers.clean_send(peer_connection, HIT+fleet_index)
            else:
#                peer_connection.sendall(HIT)
                helpers.clean_send(peer_connection, HIT)
        else:
#            peer_connection.sendall(MISS)
            helpers.clean_send(peer_connection, MISS)
        your_turn = True

    # Win Condition - Loser until proven unlost. A single unsunk ship will do it.
    i_lost = True
    for ship in my_board.fleet:
        if not ship.is_sunk:
            i_lost = False
    if i_lost:
        helpers.render_map(enemy_board, my_board, "You have been defeated! Your peer won!")
        break

    peer_lost = True
    for ship in enemy_board.fleet:
        if not ship.is_sunk:
            peer_lost = False
    if peer_lost:
        helpers.render_map(enemy_board, my_board, "You won! You have defeated your peer!")
        break

# Improvements
#  Sinks reported on attacking side but symbol doesn't change to '*'.
#   Message about what ship sank
#  Update message with the last-attacked position - Denied, would require ugly code.
#  Play again option after game over?
