MIN_X, MIN_Y, MAX_X, MAX_Y = 1,1,10,10 # 10 by 10.

import ships

class Board():
    '''Variables and functions associated with player boards.'''

    def __init__(self):
        '''Initialize the board with the player's fleet.
        fleet should be a list of ship objects.
        hit_list should be a list of y,x coordinate lists of hit attacks.
        miss_list should be a list of y,x coordinate lists of missed attacks.
        '''
        self.fleet = [ships.Destroyer(), ships.Submarine(), ships.Cruiser(), ships.BattleShip(), ships.AircraftCarrier()]
        self.hit_list = []
        self.miss_list = []

    def check_oob(self, ship):
        '''make sure the ship is within our map boundaries.
        DO NOT ADD SHIP TO FLEET UNTIL IT PASSES THIS CHECK.
        :param ship: a specific ship to check.
        :return: True if ship is in good position. False if out-of-bounds.
        '''
        for pos in ship.get_positions():
            if (pos[0] < MIN_Y
                    or pos[0] > MAX_Y
                    or pos[1] < MIN_X
                    or pos[1] > MAX_X):
                return False
        return True

    def check_collision(self, check_ship):
        '''make sure the ship coordinates don't overlap another ship.
        :param check_ship: a specific ship to check.
        :return: True if ship is not overlapping another ship. False otherwise.
        '''
        check_positions = check_ship.get_positions()
        for ship in self.fleet:
            # Skip myself.
            if ship == check_ship:
                continue
            positions = ship.get_positions()
            for position in check_positions:
                if position in positions:
                    return False
        return True

    def attack(self, coordinate):
        '''Add the coordinate to our hit_list.
        :param coordinate: y,x coordinate pair.
        Returns true if we hit a ship, false if we missed.
            If we hit and sank a ship, return a tuple of (True, index of ship)
        '''
        for ship in self.fleet:
            # Don't worry about already sunk ships.
            if ship.is_sunk:
                continue
            if ship.damage_ship(coordinate):
                self.hit_list.append(coordinate)
                if ship.is_sunk:
                    fleet_index = self.fleet.index(ship)
                    return (True, fleet_index)
                return True
        self.miss_list.append(coordinate)
        return False

    def get_attacks(self):
        ''':return: The list of attacked coordinates.'''
        return self.hit_list

    def get_last_attack(self):
        ''':return: coordinate in last index of hit_list'''
        return self.hit_list[-1]

    def get_misses(self):
        return self.miss_list
