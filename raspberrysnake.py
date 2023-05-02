#!/usr/bin/python3.10

import os, sys, time, random
# Suppressing Pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from pygame.locals import *

# Constants
DEFAULT_PLAYAREA_WIDTH = 640
DEFAULT_PLAYAREA_HEIGHT = 480
BLOCK_SIZE = 20                 # Size of the raspberry and snake segments
EYE_SIZE = 4                    # Size of the snake eyes.
INIT_SNAKE_SPEED = 1            # Speed of the snake when the game begins.
MAX_SNAKE_SPEED = 30            # Maximum snake speed.
MAX_NUM_AI_SNAKES = 3           # Maxinum number of snakes controlled by
                                #     Raspberry Pi.
INIT_SNAKE_MARGIN = 100         # When initializing, the snakes are never
                                #     drawn within the margin of the play
                                #     area boundaries.
INIT_SNAKE_SEGMENTS = 3         # Number of segments when snakes were born.
UNOCCUPIED_GRID = -1            # Grid value indicating there are no snakes.

# Global variables
# Defining colors.  Note that https://www.pygame.org/docs/ref/color_list.html
#     has provided some named colors.
redColor = pygame.Color("red")
blackColor = pygame.Color("black")
greyColor = pygame.Color("grey30")
# The following two colors are for human players' snakes.
whiteColor = pygame.Color("white")
# The following three colors are for computer snakes.
goldColor = pygame.Color("gold")
goldenrodColor = pygame.Color("goldenrod")
khakiColor = pygame.Color("khaki")
eyeColor = blackColor

playareaGrid = []
playareaGridWidth = 0
playareaGridHeight = 0

# Defining functions

# Handing Game Over
def gameOver(width, playSurface):
    gameOverFont = pygame.font.Font('freesansbold.ttf', 72)
    gameOverSurf = gameOverFont.render('Game Over', True, greyColor)
    gameOverRect = gameOverSurf.get_rect()
    gameOverRect.midtop = (width/2, 10)
    playSurface.blit(gameOverSurf, gameOverRect)
    pygame.display.flip()
    time.sleep(5)
    pygame.quit()
    sys.exit()

# Generating a new grid position
def newRandPosition(gridWidth, gridHeight):
    # We ensure playareaWidth and playareaHeight are multiples of BLOCK_SIZE,
    #     but non-integer arguments to randrange() have been deprecated
    #     since Python 3.1.
    x = random.randrange(0, int(gridWidth))
    y = random.randrange(0, int(gridHeight))
    return [int(x), int(y)]

# Generating a new raspberry at a random empty position.
def newRaspberry(gridWidth, gridHeight):
    while True:
        raspberryPos = newRandPosition(gridWidth, gridHeight)
        if playareaGrid[raspberryPos[1]][raspberryPos[0]] == UNOCCUPIED_GRID:
            break
    return raspberryPos

# Drawing the snakes in the beginning.
def init_Snakes(numPlayers, numAISnakes):
    # We have numSnakes = numPlayers + numAISnakes (with maxima 2 and
    #     MAX_NUM_AI_SNAKES, respectively) when the game begins.  We divide
    #     the playarea width into numSnakes sections with
    #     INIT_SNAKE_MARGIN on both sides.  We then put the one (or two)
    #     player's snake in the rightmost section (or the leftmost too).
    #     Then we put in the AI snakes inbetween -- this means when the game
    #     begins, the snakes won't be too close to each other.  The snake
    #     head locations are randomly generated, then we generate the snake
    #     segments upwards or downwards.
    global playareaGrid

    numSnakes = numPlayers + numAISnakes
    snakePositions = [[0, 0]] * numSnakes
    snakeColors = [blackColor] * numSnakes
    sectionGridWidth = ((playareaGridWidth*BLOCK_SIZE - \
                         2*INIT_SNAKE_MARGIN)//numSnakes) // BLOCK_SIZE

    # Position all the snakes (in each section) and then adjust individual
    #     snake positions.
    for i in range(numSnakes):
        snakePositions[i] = newRandPosition(sectionGridWidth, \
                                            playareaGridHeight)
    # First the player snake; it is always the rightmost one.
    snakePositions[0][0] += INIT_SNAKE_MARGIN // BLOCK_SIZE + \
                            (numSnakes - 1)*sectionGridWidth
    snakeColors[0] = whiteColor
    # Then position the second player snake, if applicable.  It is always
    #     the leftmost one.
    if numPlayers > 1:
        snakePositions[1][0] += INIT_SNAKE_MARGIN // BLOCK_SIZE
        snakeColors[1] = greyColor
    # Then the AI snake positions, spreading between the two human players'
    #     snakes.
    for i in range(numPlayers, numSnakes):
        snakePositions[i][0] += INIT_SNAKE_MARGIN // BLOCK_SIZE + \
                                (i - 1)*sectionGridWidth
    if numAISnakes > 0:
        snakeColors[numPlayers] = goldColor
    if numAISnakes > 1:
        snakeColors[numPlayers + 1] = goldenrodColor
    if numAISnakes > 2:
        snakeColors[numPlayers + 2] = khakiColor

    # Generating all the snake segments.  We assume the snakes are short
    #     initially so they do not touch the edges without bending.
    snakeSegLists = []
    for i in range(numSnakes):
        if snakePositions[i][1] >= playareaGridHeight/2:
            # The snake segments are generated downwards.
            snakeSegIncrement = -1
        else:
            # The snake segments are generated upwards.
            snakeSegIncrement = 1
        segPosition = snakePositions[i].copy()
        snakeSegList = []
        for j in range(INIT_SNAKE_SEGMENTS):
            snakeSegList.append(segPosition.copy())
            playareaGrid[segPosition[1]][segPosition[0]] = i
            segPosition[1] += snakeSegIncrement
        snakeSegLists.append(snakeSegList.copy())

    return snakeSegLists, snakeColors

# Drawing the snake eyes depending on their directions.
def drawSnakeEyes(playSurface, position, snakeDirection):
    # We assume the snake has two eyes and they are always leading the
    #     snake head in the front, the gap from the eyes to the front of
    #     the snake is also EYE_SIZE, and the gap between the eyes is 2.
    #     If the snake has direction 0 (heading right), the snake head
    #     looks like:
    #
    #         +-------------------+
    #         |              5    |
    #         |            *--*   |
    #         |           4|  | 4 |
    #         |            +--+   |
    #         |              2    |     ======>>> (Snake crawling direction)
    #         |            +--+   |
    #         |           4|  | 4 |
    #         |            +--+   |
    #         |              5    |
    #         +-------------------+
    #
    #     where the eyes are EYE_SIZE x EYE_SIZE squares (4x4).  The gap
    #     between the eye and the side of the head is
    #     (BLOCK_SIZE - 2*EYE_SIZE - 2)/2 (5).  If the snake is crawling
    #     towards another direction, the two eye locations are changed
    #     accordingly.

    match snakeDirection:
        case 0:
            x0_offset = BLOCK_SIZE - 2*EYE_SIZE
            y0_offset = (BLOCK_SIZE - 2*EYE_SIZE - 2)/2
            x1_offset = BLOCK_SIZE - 2*EYE_SIZE
            y1_offset = BLOCK_SIZE - y0_offset - EYE_SIZE
        case 180:
            x0_offset = EYE_SIZE
            y0_offset = (BLOCK_SIZE - 2*EYE_SIZE - 2)/2
            x1_offset = EYE_SIZE
            y1_offset = BLOCK_SIZE - y0_offset - EYE_SIZE
        case 90:
            x0_offset = (BLOCK_SIZE - 2*EYE_SIZE - 2)/2
            y0_offset = EYE_SIZE
            x1_offset = BLOCK_SIZE - x0_offset - EYE_SIZE
            y1_offset = EYE_SIZE
        case 270:
            x0_offset = (BLOCK_SIZE - 2*EYE_SIZE - 2)/2
            y0_offset = BLOCK_SIZE - 2*EYE_SIZE
            x1_offset = BLOCK_SIZE - x0_offset - EYE_SIZE
            y1_offset = BLOCK_SIZE - 2*EYE_SIZE

    pygame.draw.rect(playSurface, blackColor,
        Rect(position[0]*BLOCK_SIZE + x0_offset,
             position[1]*BLOCK_SIZE + y0_offset, EYE_SIZE, EYE_SIZE))
    pygame.draw.rect(playSurface, blackColor,
        Rect(position[0]*BLOCK_SIZE + x1_offset,
             position[1]*BLOCK_SIZE + y1_offset, EYE_SIZE, EYE_SIZE))

# Determining if the given position is safe for a snake.
def snakePositionSafe(position):
    return position[0] < playareaGridWidth and \
           position[0] >= 0 and \
           position[1] < playareaGridHeight and \
           position[1] >= 0 and \
           playareaGrid[position[1]][position[0]] == UNOCCUPIED_GRID

# Determining new directions for the AI snakes
def newAISnakeDirection(snakeSegLists, changeDirection, direction,
        raspberryPos, numPlayers, numAISnakes):
    for i in range(numPlayers, numPlayers + numAISnakes):
        if len(snakeSegLists[i]) > 0:
            snakeHeadPos = snakeSegLists[i][0].copy()
            currDirection = direction[i]
            # Generating the list of new directions, with current direction
            #     taking top priority.  The other two directions are
            #     appended randomly.
            newDirection = [currDirection]
            if random.randrange(2) == 0:
                newDirection.append(currDirection + 90)
                newDirection.append(currDirection - 90)
            else:
                newDirection.append(currDirection - 90)
                newDirection.append(currDirection + 90)

            # newDirection is now a list of three directions.  Removing
            #     invalid ones and normalizing them to one of 0, 90, 180
            #     and 270.  We are iterating downwards so deleting entries
            #     in a for loop is easier.
            minDist2Raspberry = playareaGridWidth + playareaGridHeight
            bestNewDirection = currDirection
            for j in range(len(newDirection)):
                newDirection[j] = newDirection[j] % 360
                newSnakeHead = snakeHeadPos.copy()
                match newDirection[j]:
                    case 0:
                        newSnakeHead[0] = snakeHeadPos[0] + 1
                    case 180:
                        newSnakeHead[0] = snakeHeadPos[0] - 1
                    case 90:
                        newSnakeHead[1] = snakeHeadPos[1] - 1
                    case 270:
                        newSnakeHead[1] = snakeHeadPos[1] + 1

                dist2Raspberry = abs(newSnakeHead[0] - raspberryPos[0]) + \
                                 abs(newSnakeHead[1] - raspberryPos[1])
                if dist2Raspberry < minDist2Raspberry and \
                   snakePositionSafe(newSnakeHead):
                    bestNewDirection = newDirection[j]
                    minDist2Raspberry = dist2Raspberry

            # bestNewDirection was initialized to currDirection.  It might
            #     be possible that the AI snake doesn't have any valid
            #     direction to crawl to (it is destined to die).  In that
            #     case we simply make the snake to maintain the current
            #     direction.
            changeDirection[i] = bestNewDirection

    return changeDirection

# Defining main function
def main():
    global playareaGrid, playareaGridWidth, playareaGridHeight

    # Printing out Python and library versions
    print("Python Version: " + sys.version)
    print("Pygame Version: " + pygame.__version__)
    print("\n\n")

    # Parsing command-line options (if any)
    argc = len(sys.argv)
    if argc == 1:
        playareaWidth = DEFAULT_PLAYAREA_WIDTH
        playareaHeight = DEFAULT_PLAYAREA_HEIGHT 
    elif argc == 3:
        try:
            playareaWidth = int(sys.argv[1])
            playareaHeight = int(sys.argv[2])
        except:
            print("Please use integers on the command-line!")
            sys.exit()

        if playareaWidth <= 0 or playareaHeight <= 0:
            print("Please use positive widths or heights!")
            sys.exit()
    else:
        print("\n\n")
        print("Invalid command-line options.")
        print("    Please use the following form:")
        print("        raspberrysnake.py [ width height]")
        print("    with both width and height as valid integers.")
        print("\n\n")
        sys.exit()

    # Validating the playarea width and length.
    if playareaWidth % BLOCK_SIZE != 0 or playareaHeight % BLOCK_SIZE != 0:
        print("The play area width and height should be a multiple of " \
              + str(BLOCK_SIZE) + "!")
        sys.exit()

    # Defining a 2-D grid of playarea width and height in units of BLOCK_SIZE.
    playareaGridWidth = playareaWidth // BLOCK_SIZE
    playareaGridHeight = playareaHeight // BLOCK_SIZE
    playareaGrid = [[UNOCCUPIED_GRID]*playareaGridWidth \
                   for i in range(playareaGridHeight)]

    # Querying the user if someone else wants to join.
    try:
        numPlayers = int(input("Please enter the number" \
                               + " of players, [1] or 2: ") or "1")
        if numPlayers <= 0 or numPlayers >= 3:
            raise ValueError
    except:
        print("Please enter either 1, 2 or Enter (1)!\n\n")
        sys.exit()

    # Asking the user(s) if they want to play with the AI snakes.
    try:
        numAISnakes = int(input("Please enter the number" \
                                + " of AI snakes, [0] or maximum " \
                                + str(MAX_NUM_AI_SNAKES) + ": ") or "0")
        if numAISnakes < 0 or numAISnakes > MAX_NUM_AI_SNAKES:
            raise ValueError
    except:
        print("Please enter a valid number of AI snakes, 0 .. " \
              + str(MAX_NUM_AI_SNAKES) + "!\n\n")
        sys.exit()

    # Initialization
    pygame.init()
    fpsClock = pygame.time.Clock()
    playSurface = pygame.display.set_mode((playareaWidth, playareaHeight))
    pygame.display.set_caption("Raspberry Pi 4 Snake")

    # Preparing the snakes
    snakeSegLists, snakeColors = init_Snakes(numPlayers, numAISnakes)
    numSnakes = numPlayers + numAISnakes
    snakeSpeed = INIT_SNAKE_SPEED
    raspberryPosition = newRaspberry(playareaGridWidth, playareaGridHeight)
    raspberryEaten = False
    direction = [0] * numSnakes
    changeDirection = direction

    while True:
        for event in pygame.event.get():
            # For pygame event types, please refer to
            #     https://riptutorial.com/pygame/example/18046/event-loop.
            # If the event type is neither QUIT nor KEYDOWN, likely it means
            #     the user did not press any keys.
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if numPlayers == 2:
                    # The following match block is executed only when we have
                    #     two players.
                    match event.key:
                        case pygame.K_d:
                            changeDirection[1] = 0
                        case pygame.K_a:
                            changeDirection[1] = 180
                        case pygame.K_w:
                            changeDirection[1] = 90
                        case pygame.K_s:
                            changeDirection[1] = 270

                # The following match block is executed always.
                match event.key:
                    case pygame.K_RIGHT:
                        changeDirection[0] = 0
                    case pygame.K_LEFT:
                        changeDirection[0] = 180
                    case pygame.K_UP:
                        changeDirection[0] = 90
                    case pygame.K_DOWN:
                        changeDirection[0] = 270
                    case pygame.K_ESCAPE:
                        pygame.event.post(pygame.event.Event(QUIT))
                    # We ignore any other keys being pressed.

        # Generate the new directions for the AI snakes.
        changeDirection = newAISnakeDirection(snakeSegLists, changeDirection,
            direction, raspberryPosition, numPlayers, numAISnakes)

        # We do not allow the player snake to turn 180 degrees.  The AI snakes
        #     are programmed not to do so.
        for i in range(numPlayers):
            if len(snakeSegLists[i]) > 0 and \
               abs(changeDirection[i] - direction[i]) != 180:
                direction[i] = changeDirection[i]

        # Each direction change of the snake moves the snake by one segment.
        for i in range(numSnakes):
            if len(snakeSegLists[i]) == 0:
                continue

            snakePosition = snakeSegLists[i][0].copy()
            match direction[i]:
                case 0:
                    snakePosition[0] += 1
                case 180:
                    snakePosition[0] -= 1
                case 90:
                    snakePosition[1] -= 1
                case 270:
                    snakePosition[1] += 1

            # Decide if the snake ate a raspberry.  We always insert a segment
            #     in the snake head and pop its tail if the snake doesn't eat
            #     any raspberry.  This gives an illusion that the snake is
            #     crawling forward.
            snakeSegLists[i].insert(0, list(snakePosition))

            if snakePosition[0] == raspberryPosition[0] and \
               snakePosition[1] == raspberryPosition[1]:
                raspberryEaten = True
                snakeSpeed = min(MAX_SNAKE_SPEED, snakeSpeed + 1)
            else:
                snakeTailPos = snakeSegLists[i][len(snakeSegLists[i]) - 1]
                playareaGrid[snakeTailPos[1]][snakeTailPos[0]] = UNOCCUPIED_GRID
                snakeSegLists[i].pop()

            # Make the player snake disintegrate if it crawls out of bound
            #     or crawls into another snake (including self).
            if not snakePositionSafe(snakePosition):
                # Skipping over snake head because it goes outside the play
                #     area already or hit snake bodies already.
                for j in range(1, len(snakeSegLists[i])):
                    snakeSegment = snakeSegLists[i][j]
                    playareaGrid[snakeSegment[1]][snakeSegment[0]] = \
                        UNOCCUPIED_GRID
                snakeSegLists[i].clear()
            else:
                playareaGrid[snakePosition[1]][snakePosition[0]] = i

        # If both/all player snakes disintegrates, then the game is over.
        allPlayerSnakesDone = True
        for i in range(numPlayers):
            if len(snakeSegLists[i]) > 0:
                allPlayerSnakesDone = False
                break
        if allPlayerSnakesDone:
            gameOver(playareaWidth, playSurface)

        # Generate a new raspberry if it is eaten.
        if raspberryEaten == True:
            raspberryPosition = newRaspberry(playareaGridWidth,
                                             playareaGridHeight)
            raspberryEaten = False 

        # Drawing the snakes and the raspberry.
        playSurface.fill(blackColor)
        for i in range(numSnakes):
            if len(snakeSegLists[i]) == 0:
                continue

            for j in range(len(snakeSegLists[i])):
                position = snakeSegLists[i][j]
                pygame.draw.rect(playSurface, snakeColors[i],
                    Rect(position[0]*BLOCK_SIZE, position[1]*BLOCK_SIZE,
                         BLOCK_SIZE, BLOCK_SIZE))
                if j == 0:
                    # Adding the eyes
                    drawSnakeEyes(playSurface, position, direction[i])
        pygame.draw.rect(playSurface, redColor,
                         Rect(raspberryPosition[0]*BLOCK_SIZE,
                              raspberryPosition[1]*BLOCK_SIZE,
                              BLOCK_SIZE, BLOCK_SIZE))
        pygame.display.flip()   # Update the screen

        fpsClock.tick(snakeSpeed)

if __name__ == "__main__":
    main()
