"""
This file contains the solve() function, which uses A* to find 
the shortest solution to a given n•m sliding tile puzzle, if it 
is solvable. If it is not solvable, the function returns None.
"""

__author__ = "Tristan Gaeta"

from heapq import *
from math import ceil, log2

def solve(puz):
    #   We'll express the board as an int to so we don't have to 
    #   copy lists of lists. We must keep track of width, height, 
    #   and the number of bits needed to express a board index.
    width = len(puz[0])
    height = len(puz)
    bit_length = ceil(log2(width*height))
    board = 0
    zero_index = 0 #keep track of empty space

    #Squish board and find empty space
    for i in range(height):
        for j in range(width):
            board += puz[i][j] << (bit_length*(i*width+j))
            if puz[i][j] == 0:
                zero_index += i*width+j
    
    init_state = State(bit_length,width,height,board,zero_index,0,None)

    #Check to see if puzzle is solvable
    if not init_state.is_solvable():
        return None

    #Open and Closed lists
    open = [init_state]
    closed = {}

    #Begin search
    while len(open) > 0:
        current = heappop(open)
        val = current.heuristic_value

        #Put on closed list
        closed[current] = current.src

        if val == 0:
            return _reconstruct(closed,current) 
        else:
            #Up
            up = current.up()
            if up is not None and up not in closed:
                heappush(open,up)
            #Down
            down = current.down()
            if down is not None and down not in closed:
                heappush(open,down)
            #Left
            left = current.left()
            if left is not None and left not in closed:
                heappush(open,left)
            #Right
            right = current.right()
            if right is not None and right not in closed:
                heappush(open,right)

# This method reconstructs the shortest path 
# to the goal node.
def _reconstruct(map, src):
    trail = []
    while map[src] is not None:
        trail.append(map[src][1])
        src = map[src][0]
    trail.reverse()
    return trail

"""
This class represents the game state of a sliding tile puzzle.
The board is expressed as an integer, and tiles are accessed using 
bitwise opperations. States also keep track of their source state and cost.
"""
class State:
    def __init__(self, bit_length, width, height, board, zero_index, cost, src):
        self.cost = cost #cost to get to this state
        self.src = src #source to this state
        self.bit_length = bit_length #bits required for board indices
        self.zero_index = zero_index #index of open spot
        self.height = height #height of board
        self.width = width #width of board
        self.board = board #integer representation of board

        # Determine the heuristic value. While we could alter the value between states,
        # since only 2 tiles are changing, it becomes more difficult when considering
        # linear conflicts. Thus, we recalculate the heuristic for each state.
        self.heuristic_value = 0
        for i in range(self.height):
            for j in range(self.width):
                val = self.tile_at(i*self.width + j)
                if val == 0:
                    dest_i = self.height - 1
                    dest_j = self.width - 1
                else:
                    dest_i = (val - 1) // self.width
                    dest_j = (val - 1) % self.width
                    #Check for linear conflicts src: https://medium.com/swlh/looking-into-k-puzzle-heuristics-6189318eaca2
                    if i == dest_i and dest_j > j:
                        for k in range (i+1,j): 
                            tile = self.tile_at(i*self.width+k)
                            if tile == 0:
                                continue
                            if tile // self.width == i and tile % self.width <= j:
                                #One tile will have to move out of the way and back to let the other pass -><-
                                self.heuristic_value += 2 
                self.heuristic_value += abs(i - dest_i)
                self.heuristic_value += abs(j - dest_j)

    #This method returns the tile at a given index
    def tile_at(self, index):
        center = ((1 << self.bit_length) - 1) << (self.bit_length*index)
        tile = (self.board & center) >> (self.bit_length*index)
        return tile

    #This method checks for equality between two states
    def __eq__(self, other):
        return self.board == other.board

    #This method is called when compating states in the priority queue
    def __lt__(self, other):
        return self.priority() < other.priority()

    #This method defines the hash function
    def __hash__(self):
        return self.board

    #Returns the priority of the state (g+h).
    def priority(self):
        return self.heuristic_value + self.cost

    #Determines if a given state is solvable.
    def is_solvable(self):
        flat = [self.tile_at(index) for index in range(self.width*self.height)]
        flat.pop(self.zero_index)
        inversions = 0
        for i in range(len(flat)):
            for j in range(i+1,len(flat)):
                if flat[j] < flat[i]:
                    inversions += 1
        if self.width % 2 == 1:
            return inversions % 2 == 0
        else:
            offset = (self.height - 1) - (self.zero_index // self.width)
            return (inversions + offset) % 2 == 0

    #Returns the state obtained, if any, by moving a tile up
    def up(self):
        if self.zero_index // self.width == self.height - 1:
            return None
        new_board = self.board
        new_zero_index = self.zero_index + self.width
        tile = self.tile_at(new_zero_index)
        new_board -= tile <<  (self.bit_length*new_zero_index)
        new_board += tile << (self.bit_length*self.zero_index)
        return State(self.bit_length,self.width,self.height,new_board, new_zero_index,self.cost+1,(self,"U"))

    #Returns the state obtained, if any, by moving a tile down
    def down(self):
        if self.zero_index // self.width == 0:
            return None
        new_board = self.board
        new_zero_index = self.zero_index - self.width
        tile = self.tile_at(new_zero_index)
        new_board -= tile << (self.bit_length*new_zero_index)
        new_board += tile << (self.bit_length*self.zero_index)
        return State(self.bit_length,self.width,self.height,new_board, new_zero_index,self.cost+1,(self,"D"))

    #Returns the state obtained, if any, by moving a tile left
    def left(self):
        if self.zero_index % self.width == self.width - 1:
            return None
        new_board = self.board
        new_zero_index = self.zero_index + 1
        tile = self.tile_at(new_zero_index)
        new_board -= tile << (self.bit_length*new_zero_index)
        new_board += tile << (self.bit_length*self.zero_index)
        return State(self.bit_length,self.width,self.height,new_board, new_zero_index,self.cost+1,(self,"L"))

    #Returns the state obtained, if any, by moving a tile right
    def right(self):
        if self.zero_index % self.width == 0:
            return None
        new_board = self.board
        new_zero_index = self.zero_index - 1
        tile = self.tile_at(new_zero_index)
        new_board -= tile << (self.bit_length*new_zero_index)
        new_board += tile << (self.bit_length*self.zero_index)
        return State(self.bit_length,self.width,self.height,new_board, new_zero_index,self.cost+1,(self,"R"))