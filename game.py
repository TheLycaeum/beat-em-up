import sys

import pygame
from pygame.locals import Rect, DOUBLEBUF, QUIT, K_ESCAPE, KEYDOWN, K_DOWN, \
    K_LEFT, K_UP, K_RIGHT, KEYUP, K_LCTRL, K_RETURN, FULLSCREEN, RLEACCEL


X_MAX = 640
Y_MAX = 480

class Fighter(pygame.sprite.Sprite):
    def __init__(self, image, groups, pos):
        super(Fighter, self).__init__()

        self.sheet = pygame.image.load(image).convert()
        colorkey = self.sheet.get_at((0,0))
        self.sheet.set_colorkey(colorkey)
        self.image = pygame.Surface((69, 118),pygame.SRCALPHA, 32).convert_alpha()
        self.image.blit(self.sheet, dest = (0,0), area = (0,0,69, 118))

        self.rect = self.image.get_rect()
        self.rect.midbottom = pos
        
        self.load_images()
        self.add(groups)

    def load_images(self):
        q = 71
        self.idle = []
        self.idle_idx = 0
        for i in range(0, q*8, q):
            img = pygame.Surface((q, 118), pygame.SRCALPHA, 32).convert_alpha()
            img.blit(self.sheet, dest = (0, 0), area = (i, 0, i+q, 118))
            self.idle.append(img)
        

    def update(self):
        self.image = self.idle[int(self.idle_idx)]
        
        self.idle_idx += 0.25
        self.idle_idx %= 8
        x, y = self.rect.center
        self.rect.center = (x, y)


class Background(pygame.sprite.Sprite):
    def __init__(self,  bgimage, image, groups):
        super(Background, self).__init__()
        
        self.sheet = pygame.image.load(image).convert_alpha()
        colorkey = self.sheet.get_at((0,0))
        self.sheet.set_colorkey(colorkey)

        self.image = pygame.Surface((X_MAX, Y_MAX),pygame.SRCALPHA, 32).convert_alpha()
        self.background = pygame.image.load(bgimage).convert()
        self.image.blit(self.background, dest = (0,0))

        self.rect = self.image.get_rect()

        self.vertical = self.to = 0
        self.vel = 0
        self.add(groups)
        
    def update(self):
        _, _, t, _ = self.sheet.get_rect()
        new_pos = self.vertical + self.vel
        if new_pos >= 0 and new_pos <= t - X_MAX:
            self.vertical = new_pos
        
        if abs(self.vertical - self.to) < 300:
            self.vel /= 1.5

        if abs(self.vertical - self.to) < 50:
            self.to = self.vertical
            self.vel = 0

        self.image.blit(self.background, dest = (0,0))
        self.image.blit(self.sheet, dest = (0,0), area = (self.vertical,0,640, 480))

    def scroll_right(self):
        self.to = self.vertical + X_MAX
        self.vel = 50

    def scroll_left(self):
        self.to = self.vertical - X_MAX
        self.vel = -50

def init_pygame(groups):
    screen = pygame.display.set_mode((X_MAX, Y_MAX), DOUBLEBUF)
    buildings = pygame.image.load("sprites/bg0.png").convert_alpha()

    screen.blit(buildings, dest=(0,0), area = (0,0,640,480))
    return screen, buildings


def main():
    window_x = 0
    everything = pygame.sprite.Group()
    clock = pygame.time.Clock()

    screen, empty = init_pygame(everything)
    b = Background("sprites/bg0.png", "sprites/bg1.png", everything)
    f = Fighter("sprites/fighter.png", everything, (100, 470))

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RIGHT:
                    b.scroll_right()
                    pass
                if event.key == K_LEFT:
                    b.scroll_left()
                    pass


        clock.tick(30)

        everything.clear(screen, empty)
        everything.update()
        everything.draw(screen)
        pygame.display.flip()
            

if __name__ == "__main__":
    main()
