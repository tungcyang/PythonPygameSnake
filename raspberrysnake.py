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
INIT_SNAKE_SPEED = 1            # Speed of the snake when the game begins.
MAX_SNAKE_SPEED = 30            # Maximum snake speed.

# Global variables
# Defining colors.  Note that https://www.pygame.org/docs/ref/color_list.html has provided some named
#     colors.
redColor = pygame.Color("red")
blackColor = pygame.Color("black")
whiteColor = pygame.Color("white")
greyColor = pygame.Color("gray")

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

# Generating a new raspberry
def newRaspberry(width, height):
    # We ensure playareaWidth and playareaHeight are multiples of BLOCK_SIZE, but non-integer
    #     arguments to randrange() have been deprecated since Python 3.1.
    x = random.randrange(1, int(width/BLOCK_SIZE))
    y = random.randrange(1, int(height/BLOCK_SIZE))
    return [int(x*BLOCK_SIZE), int(y*BLOCK_SIZE)]

# Defining main function
def main():
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

    if playareaWidth % BLOCK_SIZE != 0 or playareaHeight % BLOCK_SIZE != 0:
        print("The play area width and height should be a multiple of " + str(BLOCK_SIZE) + "!")
        sys.exit()

    # Initialization
    pygame.init()
    fpsClock = pygame.time.Clock()
    playSurface = pygame.display.set_mode((playareaWidth, playareaHeight))
    pygame.display.set_caption("Raspberry Pi 4 Snake")

    # Some snake constants
    snakePosition = [100, 100]
    snakeSegments = [[100, 100], [80, 100], [60, 100]]
    snakeSpeed = INIT_SNAKE_SPEED
    raspberryPosition = newRaspberry(playareaWidth, playareaHeight) 
    raspberryEaten = False
    direction = 0
    changeDirection = direction

    while True:
        for event in pygame.event.get():
            # For pygame event types, please refer to https://riptutorial.com/pygame/example/18046/event-loop.
            #     If the event type is neither QUIT nor KEYDOWN, likely it means the user did not press
            #     any keys.
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                match event.key:
                    case pygame.K_RIGHT:
                        changeDirection = 0 
                    case pygame.K_LEFT:
                        changeDirection = 180
                    case pygame.K_UP:
                        changeDirection = 90
                    case pygame.K_DOWN:
                        changeDirection = 270 
                    case pygame.K_ESCAPE:
                        pygame.event.post(pygame.event.Event(QUIT))
                    case _:
                        print("You pressed the wrong key!")

        # We do not allow the snake to turn 180 degrees.
        if abs(changeDirection - direction) != 180:
            direction = changeDirection

        # Each direction change of the snake moves the snake by one segment.
        match direction:
            case 0:
                snakePosition[0] += BLOCK_SIZE
            case 180:
                snakePosition[0] -= BLOCK_SIZE
            case 90:
                snakePosition[1] -= BLOCK_SIZE
            case 270:
                snakePosition[1] += BLOCK_SIZE

        # Decide if the snake ate a raspberry.  We always insert a segment in the snake head and
        #     pop its tail if the snake doesn't eat any raspberry.  This gives an illusion
        #     that the snake is crawling forward.
        snakeSegments.insert(0, list(snakePosition))
        if snakePosition[0] == raspberryPosition[0] and snakePosition[1] == raspberryPosition[1]:
            raspberryEaten = True
            snakeSpeed = min(MAX_SNAKE_SPEED, snakeSpeed + 1)
        else:
            snakeSegments.pop()

        # Generate a new raspberry.
        if raspberryEaten == True:
            raspberryPosition = newRaspberry(playareaWidth, playareaHeight)
            raspberryEaten = False 

        # Drawing the snake and the raspberry.
        playSurface.fill(blackColor)
        for position in snakeSegments:
            pygame.draw.rect(playSurface, whiteColor, Rect(position[0], position[1],
                             BLOCK_SIZE, BLOCK_SIZE))
        pygame.draw.rect(playSurface, redColor, Rect(raspberryPosition[0], raspberryPosition[1],
                         BLOCK_SIZE, BLOCK_SIZE))
        pygame.display.flip()   # Update the screen

        # Make the snake die if it crawls out of bound.
        if snakePosition[0] > (playareaWidth - BLOCK_SIZE) or snakePosition[0] < 0:
            gameOver(playareaWidth, playSurface)
        if snakePosition[1] > (playareaHeight - BLOCK_SIZE) or snakePosition[1] < 0:
            gameOver(playareaWidth, playSurface)
        # The snake also dies if it hits its own body.
        for snakeBody in snakeSegments[1:]:
            if snakePosition[0] == snakeBody[0] and snakePosition[1] == snakeBody[1]:
                gameOver(playareaWidth, playSurface)

        fpsClock.tick(snakeSpeed)

if __name__ == "__main__":
    main()
