import sys

import pygame
from pygame.locals import Rect, DOUBLEBUF, QUIT, K_ESCAPE, KEYDOWN, K_DOWN, \
    K_LEFT, K_UP, K_RIGHT, KEYUP, K_LCTRL, K_RETURN, FULLSCREEN, RLEACCEL, K_a


X_MAX = 640
Y_MAX = 480

class Fighter(pygame.sprite.Sprite):
    def __init__(self, image, groups, pos, size):
        super(Fighter, self).__init__()
        self.s_x, self.s_y = size
        self.sheet = pygame.image.load(image).convert()
        colorkey = self.sheet.get_at((0,0))
        self.sheet.set_colorkey(colorkey)
        self.image = pygame.Surface((self.s_x, self.s_y),pygame.SRCALPHA, 32).convert_alpha()
        self.image.blit(self.sheet, dest = (0,0), area = (0,0,self.s_x, self.s_y))
        
        self.rect = self.image.get_rect()
        self.rect.midbottom = pos

        self.load_images()

        self.punching = False

        self.add(groups)

    def load_images(self):
        # Load idling images
        self.idle = []
        self.idle_idx = 0
        for i in range(0, self.s_x*7, self.s_x):
            img = pygame.Surface((self.s_x, self.s_y), pygame.SRCALPHA, 32).convert_alpha()
            img.blit(self.sheet, dest = (0, 0), area = (i, 0, i+self.s_x, self.s_y))
            self.idle.append(img)

        self.punch_images = []
        self.punch_idx = 0
        # q = 1359
        # s = 424
        # q = 1360
        s = 424
        w = 220

        img = pygame.Surface((w, self.s_y), pygame.SRCALPHA, 32).convert_alpha()
        img.blit(self.sheet, dest = (0, 0), area = (q, s, q+w, s+self.s_y))
        self.punch_images.append(img)

        img = pygame.Surface((w, self.s_y), pygame.SRCALPHA, 32).convert_alpha()
        img.blit(self.sheet, dest = (0, 0), area = (q+w, s, q+w*2, s+self.s_y))
        self.punch_images.append(img)

        img = pygame.Surface((w, self.s_y), pygame.SRCALPHA, 32).convert_alpha()
        img.blit(self.sheet, dest = (0, 0), area = (q+w*2, s, q+w*3, s+self.s_y))
        self.punch_images.append(img)

        # img = pygame.Surface((w, self.s_y), pygame.SRCALPHA, 32).convert_alpha()
        # img.blit(self.sheet, dest = (0, 0), area = (q+w*2, s+self.s_y, q+w*3, s+self.s_y*2))
        # self.punch_images.append(img)

        # img = pygame.Surface((w, self.s_y), pygame.SRCALPHA, 32).convert_alpha()
        # img.blit(self.sheet, dest = (0, 0), area = (q+w, s+self.s_y, q+w*2, s+self.s_y*2))
        # self.punch_images.append(img)

        # img = pygame.Surface((w, self.s_y), pygame.SRCALPHA, 32).convert_alpha()
        # img.blit(self.sheet, dest = (0, 0), area = (q, s+self.s_y, q+w, s+self.s_y*2))
        # self.punch_images.append(img)



    def punch(self):
        self.punching = True

    def update(self):
        if self.punching:
            try:
                self.image = self.punch_images[int(self.punch_idx)]
                self.punch_idx += 0.25
                self.punch_idx %= len(self.punch_images)
                if self.punch_idx == 0:
                    self.punching = False
            except IndexError as e:
                print (int(self.punch_idx))
                raise
        else:
            self.image = self.image
            self.image = self.idle[int(self.idle_idx)]
            self.idle_idx += 0.25
            self.idle_idx %= 7

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
    f = Fighter("sprites/fighter-terry.png", everything, (200, 490), (185, 245))

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
                if event.key == K_a:
                    f.punch()
                


        clock.tick(30)

        everything.clear(screen, empty)
        everything.update()
        everything.draw(screen)
        pygame.display.flip()
            

if __name__ == "__main__":
    import sys
    q = int(sys.argv[1])
    main()
