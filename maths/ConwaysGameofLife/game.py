import numpy as np
import pygame
import sys

pltRange = 100
windowSize = (700, 500)
backgroundColor = (30, 30, 30)
cellSize = 5
cellColor = 'white'


pygame.init()
screen = pygame.display.set_mode(windowSize)
pygame.display.set_caption("Conway's Game of Life")

clock = pygame.time.Clock()

{
    
}

squares = [
    (50, 50, 40),
    (150, 100, 60),
    (250, 200, 30),
    (350, 350, 50)
]

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.BUTTON_X1:
            print(100)

    screen.fill(backgroundColor)

    for (x, y, size) in squares:
        pygame.draw.rect(screen, cellColor, (x, y, size, size))

    pygame.display.flip()

    # Limit FPS
    clock.tick(60)
