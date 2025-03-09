# ===== Constants ===== #
# Directions
UP, DOWN, LEFT, RIGHT = 1,2,3,4
# Diagonals can be added if desired.

# Position_list indices.
Y_INDEX, X_INDEX, DAMAGE_INDEX = 0, 1, 2

# Damaged_flag values in position_list.
UNDAMAGED = 0
DAMAGED = 1

def get_coord_maths(direction):
    '''Return lamda functions containing math
        for each axis based on the passed direction.
    :param direction: A constant indicating which
        lamda to return.
    :return: A tuple of y_math,x_math.
    '''
    # Math lambdas for calculating coordinates.
    # By default, return the same value.
    # Otherwise, perform math on coord related to
    # our direction.
    y_math = lambda y: y
    x_math = lambda x: x
    if direction == UP:
        y_math = lambda y: y-1
    elif direction == DOWN:
        y_math = lambda y: y+1
    elif direction == LEFT:
        x_math = lambda x: x-1
    elif direction == RIGHT:
        x_math = lambda x: x+1
    # Diagonals can be added if desired.

    return y_math, x_math

class Ship:
    '''Variables and functions associated with battleship Ship objects.'''
    def __init__(self, size, symbol):
        '''Create our ship object.
        :param size: Integer indicating how long a ship is.
        :param symbol: A single character to represent the ship.
        '''
        self.size = size
        self.symbol = symbol

        self.is_sunk = False
        self.position_list = [] # List of lists of y_coord, x_coord, damaged_flag.

    def set_positions(self, coordinate, direction):
        '''Fill position_list with initial coordinate and
            subsequent coordinates in direction until size.
        :param coordinate: List with initial y,x
            coordinate, other coordinates will be calculated
            from this coordinate and the direction.
        :param direction: A constant indicating how to
            calculate the other coordinates.
        '''
        # Prepare coordinate math functions based on direction.
        y_math, x_math = get_coord_maths(direction)

        # Set the initial position [y_coord, x_coord, damaged_flag]
        self.position_list =[[coordinate[Y_INDEX], coordinate[X_INDEX], UNDAMAGED]]
        previous_pos = coordinate

        # Iterate through positions, adding to the list.
        # We already loaded one so start at 1 instead of 0.
        for pos in range(1, self.size):
            y_coord = y_math(previous_pos[Y_INDEX])
            x_coord = x_math(previous_pos[X_INDEX])
            self.position_list.append([y_coord, x_coord, UNDAMAGED])
            previous_pos = (y_coord, x_coord)

    def get_positions(self):
        ''':return: List of coordinate lists.'''
        return [[pos[Y_INDEX],pos[X_INDEX]] for pos in self.position_list]

    def get_damage(self):
        ''':return: List of damage values. Helper for damage_ship().'''
        return [pos[DAMAGE_INDEX] for pos in self.position_list]

    def damage_ship(self, coordinate):
        '''Check if coordinate matches one in position_list,
            set damage_flag if so. If all damage_flags are set
            then set is_sunk to True.
        :param coordinate: List of y_coord, x_coord.
        :return: False if coordinate not in ship, otherwise True.
        '''
        positions = self.get_positions()
        # No damage, most common case.
        if coordinate not in positions:
            return False
        # Otherwise, damage the ship (update position_list's damage_index).
        pos_index = positions.index(coordinate)
        self.position_list[pos_index][DAMAGE_INDEX] = DAMAGED
        # Check if we were sunk.
        if UNDAMAGED not in self.get_damage():
            self.is_sunk = True
            self.symbol = '*'
        return True

class Destroyer(Ship):
    def __init__(self):
        Ship.__init__(self, 2, 'D')
class Submarine(Ship):
    def __init__(self):
        Ship.__init__(self, 3, 'S')
class Cruiser(Ship):
    def __init__(self):
        Ship.__init__(self, 3, 'C')
class BattleShip(Ship):
    def __init__(self):
        Ship.__init__(self, 4, 'B')
class AircraftCarrier(Ship):
    def __init__(self):
        Ship.__init__(self, 5, 'A')
