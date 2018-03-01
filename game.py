import time
import sys
import random

import pygame
from pygame.locals import Rect, DOUBLEBUF, QUIT, K_ESCAPE, KEYDOWN, K_DOWN, \
    K_LEFT, K_UP, K_RIGHT, KEYUP, K_LCTRL, K_RETURN, FULLSCREEN, RLEACCEL, K_a, K_s


X_MAX = 1280
Y_MAX = 480


def load_sprite(sheet, surf_rect, sprite_rect):
    x0, y0, x1, y1 = sprite_rect
    img = pygame.Surface(surf_rect, pygame.SRCALPHA, 32).convert_alpha()
    img.blit(sheet, dest = (0, 0), area = sprite_rect)
    return img

game_state = {}

class EnergyBar(pygame.sprite.Sprite):
    def __init__(self, pos, groups, full, fighter):
        self.max_width = X_MAX-20
        super (EnergyBar, self).__init__()
        self.full = full
        self.fighter = fighter
        self.image = pygame.Surface((self.max_width, 10), pygame.SRCALPHA, 32).convert_alpha()
        pygame.draw.rect(self.image, (255, 255, 255), (0, 0, self.max_width, 10), 1)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.add(groups)

    def update(self):
        ratio = float(self.fighter.energy)/self.full
        if ratio > 0.6:
            colour = (0, 255, 0, 200)
        elif ratio <= 0.6 and ratio > 0.3:
            colour = (255, 255, 0, 200)
        else:
            colour = (255, 0, 0, 200)
        self.image = pygame.Surface((self.max_width, 10), pygame.SRCALPHA, 32).convert_alpha()
        pygame.draw.rect(self.image, (255, 255, 255), (0, 0, self.max_width, 10), 1)
        self.image.fill(colour, rect=(1, 1, (self.max_width*ratio)-2, 8))
        
                                        

class Impact(pygame.sprite.Sprite):
    def __init__(self, images, pos, groups):
        super(Impact, self).__init__()
        self.images = []
        self.idx = 0
        sheet = pygame.image.load(images).convert_alpha()
        for i in range(0, 320, 32):
            img = pygame.Surface((32, 32)).convert()
            img.blit(sheet, dest = (0,0), area = (i, 0, 32, 32))
            self.images.append(img)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        print (pos)
        self.rect.center = pos
        self.add(groups)
        

    def update(self):
        self.image = self.images[self.idx]
        self.idx += 1
        if self.idx >= len(self.images):
            self.kill()


class Enemy(pygame.sprite.Sprite):
    IDLING = "idling"
    WALKING = "walking"
    ATTACKING = "attacking"
    IMPACTED = "impacted"
    DYING = "dying"

    def __repr__(self):
        return "Enemy ({}, {})".format(self.state, self.energy)

    def __init__(self, image, groups, pos, fighter):
        super(Enemy, self).__init__()
        self.sheet = pygame.image.load(image).convert()
        colorkey = self.sheet.get_at((0,0))
        self.sheet.set_colorkey(colorkey)
        self.image = pygame.Surface((10,10), pygame.SRCALPHA, 32).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.midbottom = pos
        self.enemy_pos = pos
        self.load_images()
        self.state = Enemy.IDLING
        self.state = Enemy.WALKING
        self.add(groups)
        self.fighter = fighter
        self.walk_vel = random.randint(15, 20)
        self.direction = "left"
        self.confronting = False

        self.punch_sound = pygame.mixer.Sound("audio/woosh.wav")
        self.punch_sound.set_volume(1)

        self.death_sound = pygame.mixer.Sound("audio/enemy-scream.wav")
        self.death_sound.set_volume(2)

        self.energy = 5

        
    
    def load_images(self):
        # Load idle images
        self.idle_images = []
        self.idle_idx = 0
        img = load_sprite(self.sheet, (168, 194), (12, 478, 12+168, 478+194))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (168, 190), (210, 482, 210+168, 482+190))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (168, 190), (408, 482, 210+168, 482+190))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (168, 192), (606, 480, 606+168, 480+192))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (168, 194), (804, 478, 804+168, 478+194))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (168, 196), (1002, 476, 1002+168, 476+196))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (168, 198), (1200, 474, 1200+168, 474+198))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (168, 198), (1398, 474, 1398+168, 474+198))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (168, 198), (1596, 474, 1596+168, 474+198))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (168, 196), (1794, 476, 1794+168, 476+196))
        self.idle_images += list(reversed(self.idle_images))

        self.idle_images.append(img)
        self.idle_images_right = self.idle_images
        self.idle_images_left = [pygame.transform.flip(x, True, False) for x in self.idle_images_right]

        # Load walking images
        self.walking_images = []
        self.walking_idx = 0
        img = load_sprite(self.sheet, (154, 196), (12, 910, 19+154, 910+196))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (138, 200), (196, 906, 196+138, 906+200))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (138, 200), (364, 904, 196+138, 906+200))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (122, 204), (518, 902, 518+122, 902+204))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (128, 206), (670, 900, 518+128, 902+206))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (134, 204), (828, 902, 828+134, 902+204))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (140, 198), (992, 908, 992+140, 908+198))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (142, 196), (1162, 910, 1162+142, 910+196))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (142, 196), (1334, 910, 1334+142, 910+196))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (146, 194), (1506, 912, 1506+146, 912+194))
        self.walking_images.append(img)
        self.walking_images_right = self.walking_images
        self.walking_images_left = [pygame.transform.flip(x, True, False) for x in self.walking_images_right]

        # Load kicking images
        self.attack_images = []
        self.attack_idx = 0
        img = load_sprite(self.sheet, (154, 202), (4, 2984, 4+154, 2984+202))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (150, 200), (188, 2986, 188+150, 2986+200))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (220, 200), (368, 2986, 368+220, 2986+200))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (229, 200), (618, 2986, 618+229, 2986+200))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (192, 200), (876, 2986, 876+192, 2986+200))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (140, 198), (1098, 2988, 1098+140, 2988+198))
        self.attack_images.append(img)
        self.attack_images_right = self.attack_images
        self.attack_images_left = [pygame.transform.flip(x, True, False) for x in self.attack_images_right]

        # Load impact images
        self.impact_images = []
        self.impact_idx = 0
        img = load_sprite(self.sheet, (165, 192), (1916, 1146, 1916+165, 1146+192))
        self.impact_images.append(img)
        self.impact_images_right = self.impact_images
        self.impact_images_left = [pygame.transform.flip(x, True, False) for x in self.impact_images_right]

        #Load dying images
        self.dying_images = []
        self.dying_idx = 0
        img = load_sprite(self.sheet, (208, 170), (1734, 728, 1734+208, 728+170))
        self.dying_images.append(img)

        img = load_sprite(self.sheet, (208, 170), (1972, 728, 1972+208, 728+170))
        self.dying_images.append(img)

        img = load_sprite(self.sheet, (232, 170), (2210, 728, 2210+232, 728+170))
        self.dying_images.append(img)

        img = load_sprite(self.sheet, (208, 180), (2472, 728, 2472+208, 728+180))
        self.dying_images.append(img)

        img = load_sprite(self.sheet, (208, 170), (2682, 728, 2682+208, 728+170))
        self.dying_images.append(img)


        img = load_sprite(self.sheet, (208, 170), (2943, 728, 2943+208, 728+170))
        self.dying_images.append(img)

        img = load_sprite(self.sheet, (262, 170), (3146, 728, 3146+262, 728+170))
        img2 = pygame.Surface((262, 170), pygame.SRCALPHA, 32).convert_alpha()
        self.dying_images.append(img)
        self.dying_images.append(img)
        self.dying_images.append(img)
        self.dying_images.append(img2)
        self.dying_images.append(img)
        self.dying_images.append(img2)
        self.dying_images.append(img)
        self.dying_images.append(img2)
        self.dying_images.append(img)
        self.dying_images.append(img2)

        self.dying_images_right = self.dying_images
        self.dying_images_left = [pygame.transform.flip(x, True, False) for x in self.dying_images_right]


    def ai(self):
        if self.state == Enemy.DYING:
            return
        f_x, f_y = self.fighter.rect.center
        e_x, e_y = self.rect.center

        distance = abs(f_x - e_x)
        if distance < 150:
            # print ("Close")
            if not self.confronting:
                # print (" Going to confront")
                self.confronting = True
                if random.random() < 0.9:
                    # print("  Punching")
                    self.punch_sound.play(maxtime=10000)
                    self.state = Enemy.ATTACKING
                else:
                    # print("  Idling")
                    self.state = Enemy.IDLING
        else:
            self.confronting = False
            if f_x > e_x:
                # print ("Turn right")
                self.direction = "right"
            else:
                # print ("Turn left")
                self.direction = "left"
            # print("Walking")
            self.state = Enemy.WALKING
            
    def impact(self):
        self.state = Enemy.IMPACTED

    def update(self):
        ""
        if self.energy <= 0:
            self.state = Enemy.DYING

        self.ai()
        if self.direction == "right":
            self.idle_images = self.idle_images_right
            self.walking_images = self.walking_images_right
            self.attack_images = self.attack_images_right
            self.impact_images = self.impact_images_right
            self.dying_images = self.dying_images_right
            self.walk_vel = abs(self.walk_vel)
        if self.direction == "left":
            self.idle_images = self.idle_images_left
            self.walking_images = self.walking_images_left
            self.attack_images = self.attack_images_left
            self.impact_images = self.impact_images_left
            self.dying_images = self.dying_images_left
            self.walk_vel = -abs(self.walk_vel)

        actions = {Enemy.ATTACKING : self.update_attack,
                   Enemy.IDLING    : self.update_idling,
                   Enemy.WALKING   : self.update_walking,
                   Enemy.IMPACTED  : self.update_impacted,
                   Enemy.DYING     : self.update_dying}
        action = actions[self.state] 
        action()

        self.rect = self.image.get_rect()
        self.rect.midbottom = self.enemy_pos

    def update_dying(self):
        self.image = self.image
        self.image = self.dying_images[int(self.dying_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.enemy_pos
        self.dying_idx += 1
        self.dying_idx %= len(self.dying_images)
        if self.dying_idx <= 6:
            x, y = self.enemy_pos
            x -= (self.walk_vel * 6)
            self.enemy_pos = x, y
        if self.dying_idx == 4:
            self.death_sound.play()
        if self.dying_idx == 0:
            self.kill()

        

    def update_impacted(self):
        self.image = self.image
        self.image = self.impact_images[int(self.impact_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.enemy_pos
        self.impact_idx += 0.5
        self.impact_idx %= len(self.impact_images)
        if self.impact_idx == 0:
            self.state = Enemy.IDLING
            self.energy -=1

        
    


    def update_idling(self):
        self.image = self.image
        self.image = self.idle_images[int(self.idle_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.enemy_pos
        self.idle_idx += 0.5
        self.idle_idx %= len(self.idle_images)
        if self.idle_idx == 0:
            self.confronting = False

    def update_walking(self):
        self.image = self.walking_images[int(self.walking_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.enemy_pos
        self.walking_idx += 0.5
        self.walking_idx %= len(self.walking_images)
        x, y = self.enemy_pos
        x += self.walk_vel
        self.enemy_pos = x,y


    def update_attack(self):
        # print ("Starting Enemy {}, {}".format(self.state, self.attack_idx))
        self.image = self.attack_images[int(self.attack_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.enemy_pos
        self.attack_idx += 1
        self.attack_idx %= len(self.attack_images)
        # print ("Fighter is (while running) {}".format(self.fighter.state))
        if self.attack_idx == 0:
            self.state = Enemy.IDLING
            self.confronting = False
            # print ("Fighter is (over) {}".format(self.fighter.state))
            # if self.fighter.state == Fighter.IMPACTED:
            #     print ("Just hit ")



class Fighter(pygame.sprite.Sprite):
    IDLING = "idling"
    PUNCHING = "punching"
    KICKING = "kicking"
    DYING = "dying"
    WALKING_RIGHT = "walking_right"
    WALKING_LEFT = "walking_left"
    IMPACTED = "impacted"
    
    def __repr__(self):
        return "Fighter ({}, {})".format(self.state, self.energy)

    def __init__(self, image, groups, pos, background):
        super(Fighter, self).__init__()
        self.sheet = pygame.image.load(image).convert()
        colorkey = self.sheet.get_at((0,0))
        self.sheet.set_colorkey(colorkey)
        self.image = pygame.Surface((10, 10),pygame.SRCALPHA, 32).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.midbottom = pos
        self.load_images()
        self.state = Fighter.IDLING
        self.add(groups)
        self.background = background

        self.fighter_pos = pos

        self.direction = "right"

        self.punch_sound = pygame.mixer.Sound("audio/woosh.wav")
        self.punch_sound.set_volume(1)

        self.grunt_sound = pygame.mixer.Sound("audio/grunt.wav")
        self.grunt_sound.set_volume(1)

        self.walk_in()
        self.energy = 20

    def walk_in(self):
        self.walking_in = 30
        self.state = Fighter.WALKING_RIGHT
        self.walk_vel = 10
        x, y = self.fighter_pos
        self.fighter_pos = -100, y


    def load_images(self):
        # Load idling images
        self.idle_images = []
        self.idle_idx = 0
        img = load_sprite(self.sheet, (166, 210), (8, 14, 8+163, 22+210))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (166, 210), (197, 14, 197+166, 26+210))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (166, 210), (382, 14, 382+164, 24+210))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (166, 210), (564, 14, 564+162, 18+210))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (166, 210), (750, 14, 750+162, 16+210))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (166, 210), (936, 14, 936+162, 16+210))
        self.idle_images.append(img)
        img = load_sprite(self.sheet, (166, 210), (1118, 14, 1118+162, 14+210))
        self.idle_images.append(img)
        self.idle_images += list(reversed(self.idle_images))
        self.idle_images_right = self.idle_images
        self.idle_images_left = [pygame.transform.flip(x, True, False) for x in self.idle_images_right]


        # Load punching images
        self.punch_images = []
        self.punch_idx = 0
        img = load_sprite(self.sheet, (162, 210), (1380, 432, 1380+162, 432+210))
        self.punch_images.append(img)
        img = load_sprite(self.sheet, (222, 210), (1558, 434, 1558+222, 434+210))
        self.punch_images.append(img)
        img = load_sprite(self.sheet, (188, 210), (1796, 436, 1796+188, 436+210))
        self.punch_images.append(img)
        img = load_sprite(self.sheet, (162, 210), (1380, 432, 1380+162, 432+210))
        self.punch_images.append(img)
        self.punch_images_right = self.punch_images
        self.punch_images_left = [pygame.transform.flip(x, True, False) for x in self.punch_images_right]


        # Load kick images
        self.kicking_images = []
        self.kicking_idx = 0
        img = load_sprite(self.sheet, (140, 208), (1380, 2954, 1380+140, 432+208))
        self.kicking_images.append(img)
        img = load_sprite(self.sheet, (104, 208), (1556, 2954, 1380+104, 432+208))
        self.kicking_images.append(img)
        img = load_sprite(self.sheet, (116, 208), (1684, 2954, 1380+116, 432+208))
        self.kicking_images.append(img)
        img = load_sprite(self.sheet, (276, 208), (1828, 2954, 1828+276, 432+208))
        self.kicking_images.append(img)
        img = load_sprite(self.sheet, (276, 208), (1828, 2954, 1828+276, 432+208))
        self.kicking_images.append(img)
        img = load_sprite(self.sheet, (276, 208), (2124, 2954, 2124+256, 432+208))
        self.kicking_images.append(img)
        img = load_sprite(self.sheet, (276, 208), (2406, 2954, 2406+194, 432+208))
        self.kicking_images.append(img)
        self.kicking_images_right = self.kicking_images
        self.kicking_images_left = [pygame.transform.flip(x, True, False) for x in self.kicking_images_right]

        # Load walking images
        self.walking_images = []
        self.walking_idx = 0
        self.walk_vel = 20
        img = load_sprite(self.sheet, (166, 213), (2, 701, 2+166, 701+213))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (168, 212), (190, 700, 190+168, 700+212))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (168, 212), (380, 694, 380+168, 694+212))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (108, 220), (562, 692, 562+108, 692+220))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (106, 220), (698, 692, 698+106, 692+220))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (106, 222), (832, 690, 832+106, 690+222))
        self.walking_images.append(img)
        img = load_sprite(self.sheet, (150, 218), (968, 694, 968+150, 694+218))
        self.walking_images.append(img)
        self.walking_images_right = self.walking_images
        self.walking_images_left = [pygame.transform.flip(x, True, False) for x in self.walking_images_right]

        # Load impacted images
        self.impacted_images = []
        self.impacted_idx = 0
        img = load_sprite(self.sheet, (166, 210), (382, 1390, 382+166, 1390+210))
        self.impacted_images.append(img)
        img = load_sprite(self.sheet, (170, 210), (562, 1392, 562+170, 1392+210))
        self.impacted_images.append(img)
        img = load_sprite(self.sheet, (180, 194), (740, 1408, 740+180, 1408+194))
        self.impacted_images.append(img)
        self.impacted_images_right = self.impacted_images
        self.impacted_images_left = [pygame.transform.flip(x, True, False) for x in self.impacted_images_right]

        # Load dying images
        self.dying_images = []
        self.dying_idx = 0
        img = load_sprite(self.sheet, (194, 206), (1318, 32, 1313+194, 32+206))
        self.dying_images.append(img)
        img = load_sprite(self.sheet, (184, 206), (1526, 32, 1526+184, 32+206))
        self.dying_images.append(img)
        img = load_sprite(self.sheet, (248, 176), (1702, 32, 1702+248, 32+176))
        self.dying_images.append(img)
        img = load_sprite(self.sheet, (198, 206), (1962, 32, 1962+198, 32+206))
        self.dying_images.append(img)
        img = load_sprite(self.sheet, (194, 146), (1316, 276, 1316+194, 276+146))
        self.dying_images.append(img)
        img = load_sprite(self.sheet, (252, 146), (1784, 276, 1784+252, 276+146))
        self.dying_images.append(img)
        self.dying_images.append(img)
        self.dying_images.append(img)
        self.dying_images.append(img)
        self.dying_images.append(img)
        self.dying_images.append(img)
        self.dying_images.append(img)
        self.dying_images.append(img)

        self.dying_images_right = self.dying_images
        self.dying_images_left = [pygame.transform.flip(x, True, False) for x in self.dying_images_right]


    def idle(self):
        if self.state != Fighter.DYING:
            self.state = Fighter.IDLING

    def punch(self):
        if self.state != Fighter.DYING:
            self.punch_sound.play(maxtime=10000)
            self.state = Fighter.PUNCHING

    def kick(self):
        if self.state != Fighter.DYING:
            self.punch_sound.play(maxtime=10000)
            self.state = Fighter.KICKING
    
    def impact(self):
        if self.state != Fighter.DYING:
            self.state = Fighter.IMPACTED
        

    def walk_right(self):
        if self.state != Fighter.DYING:
            self.state = Fighter.WALKING_RIGHT

    def walk_left(self):
        if self.state != Fighter.DYING:
            self.state = Fighter.WALKING_LEFT

    def update(self):
        if self.energy <= 0:
            self.state = Fighter.DYING
        if self.direction == "right":
            self.idle_images = self.idle_images_right
            self.walking_images = self.walking_images_right
            self.punch_images = self.punch_images_right
            self.impacted_images = self.impacted_images_right
            self.kicking_images = self.kicking_images_right
            self.dying_images = self.dying_images_right
        if self.direction == "left":
            self.idle_images = self.idle_images_left
            self.walking_images = self.walking_images_left
            self.punch_images = self.punch_images_left
            self.impacted_images = self.impacted_images_left
            self.kicking_images = self.kicking_images_left
            self.dying_images = self.dying_images_left
        if self.walking_in:
            self.walking_in -= 1
            if self.walking_in == 0:
                self.state = Fighter.IDLING
                if pygame.mixer.get_init():
                    pygame.mixer.music.load("music/level-1.mp3")
                    pygame.mixer.music.set_volume(0.4)
                    pygame.mixer.music.play(-1)
                self.walk_vel = 25


        actions = {Fighter.PUNCHING      : self.update_punch,
                   Fighter.KICKING       : self.update_kicking,
                   Fighter.IDLING        : self.update_idling,
                   Fighter.WALKING_RIGHT : self.update_walking_right,
                   Fighter.WALKING_LEFT  : self.update_walking_left,
                   Fighter.DYING         : self.update_dying,
                   Fighter.IMPACTED      : self.update_impacted}
        action = actions[self.state] 
        action()

        self.rect = self.image.get_rect()
        self.rect.midbottom = self.fighter_pos

    def update_dying(self):
        self.image = self.dying_images[int(self.dying_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.fighter_pos
        self.dying_idx += 0.5
        self.dying_idx %= len(self.dying_images)

        if self.dying_idx <= 6:
            x, y = self.fighter_pos
            x -= self.walk_vel
            self.fighter_pos = x, y

        if self.dying_idx == 0:
            self.kill()
            game_state['over'] = True


    def update_impacted(self):
        self.image = self.impacted_images[int(self.impacted_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.fighter_pos
        self.impacted_idx += 0.5
        self.impacted_idx %= len(self.impacted_images)
        if self.impacted_idx == 0:
            self.state = Fighter.IDLING
            self.energy -=1


    def update_walking_right(self):
        self.image = self.walking_images[int(self.walking_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.fighter_pos
        self.walking_idx += 0.5
        self.walking_idx %= len(self.walking_images)
        x, y = self.fighter_pos
        x += self.walk_vel
        self.fighter_pos = x,y

        if abs(x - X_MAX*16.0/18) < 10:
            self.background.scroll_right()
            x, y = self.fighter_pos 
            x -= 100
            self.fighter_pos  = x, y

    def update_walking_left(self):
        self.image = self.walking_images[int(self.walking_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.fighter_pos
        self.walking_idx += 0.5
        self.walking_idx %= len(self.walking_images)
        x, y = self.fighter_pos
        if abs(x - X_MAX*1.0/16) >= 20:
            x += self.walk_vel
            self.fighter_pos = x,y

        # if abs(x - X_MAX*1.0/16) <= 10:
        #     self.background.scroll_left()
        #     x, y = self.fighter_pos 
        #     x += 100
        #     self.fighter_pos  = x, y
        

    def update_punch(self):
        self.image = self.punch_images[int(self.punch_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.fighter_pos
        self.punch_idx += 1
        self.punch_idx %= len(self.punch_images)
        if self.punch_idx == 0:
            self.state = Fighter.IDLING

    def update_kicking(self):
        self.image = self.kicking_images[int(self.kicking_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.fighter_pos
        self.kicking_idx += 1
        self.kicking_idx %= len(self.kicking_images)
        if self.kicking_idx == 0:
            self.state = Fighter.IDLING


    def update_idling(self):
        self.image = self.image
        self.image = self.idle_images[int(self.idle_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.fighter_pos
        self.idle_idx += 0.5
        self.idle_idx %= len(self.idle_images)



class Background(pygame.sprite.Sprite):
    def __init__(self,  bgimage, image, groups):
        super(Background, self).__init__()
        
        self.sheet = pygame.image.load(image).convert_alpha()
        colorkey = self.sheet.get_at((0,0))
        self.sheet.set_colorkey(colorkey)

        self.black = pygame.Surface((X_MAX, Y_MAX)).convert_alpha()
        self.black.fill((0,0,0,255))
        self.alpha = 255

        self.image = pygame.Surface((X_MAX, Y_MAX),pygame.SRCALPHA, 32).convert_alpha()
        self.background = pygame.image.load(bgimage).convert()
        self.image.blit(self.background, dest = (0,0))

        self.rect = self.image.get_rect()

        self.vertical = self.to = 0
        self.vel = 0
        self.fighter = None
        self.add(groups)
        
    def update(self):
        _, _, t, _ = self.sheet.get_rect()
        new_pos = self.vertical + self.vel

        if new_pos >= 0 and new_pos <= t - X_MAX:
            self.vertical = new_pos
        
        if abs(self.vertical - self.to) < 50:
            self.to = self.vertical
            self.vel = 0

        self.image.blit(self.background, dest = (0,0))
        self.image.blit(self.sheet, dest = (0,0), area = (self.vertical,0,X_MAX, Y_MAX))
        self.alpha -= 5
        if self.alpha >= 0:
            self.black.fill((0,0,0,self.alpha))
            self.image.blit(self.black, dest = (0,0))

    def scroll_right(self):
        self.to = self.vertical + 100
        self.vel = 50


    def scroll_left(self):
        self.to = self.vertical - 100
        self.vel = -50

def init_pygame(groups):
    pygame.mixer.init()
    screen = pygame.display.set_mode((X_MAX, Y_MAX), DOUBLEBUF)
    empty = pygame.Surface((X_MAX, Y_MAX))
    return screen, empty

def check_collisions(fighter, enemies, everything):
    enemy = pygame.sprite.spritecollideany(fighter, enemies)

    if enemy:
        rect = pygame.sprite.collide_mask(fighter, enemy)
        if rect:
            # Impact("sprites/explosion.png", rect, everything)
            if fighter.state in [Fighter.PUNCHING, Fighter.KICKING]:
                enemy.impact()
            elif enemy.state == Enemy.ATTACKING:
                fighter.impact()

               
    
    

def main():
    everything = pygame.sprite.OrderedUpdates()
    # hero = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    clock = pygame.time.Clock()

    enemy_count = 3
    screen, empty = init_pygame(everything)
    b = Background("sprites/bg0.png", "sprites/bg1.png", [everything])
    f = Fighter("sprites/fighter-terry.png", everything, (100, 450), b)
    EnergyBar((10,10), everything, f.energy, f)
    death_counter = 20

    while f.walking_in:
        clock.tick(20)
        everything.clear(screen, empty)
        everything.update()
        everything.draw(screen)
        pygame.display.flip()


    while True:
        if 'over' in game_state:
            death_counter -=1
        if not death_counter:
            sys.exit(0)
        if len(enemies) != 1:
            if enemy_count:
                Enemy("sprites/enemy-gato.png", [everything, enemies], (random.choice([-150, 1350]), 450), f)
                enemy_count -= 1
            else:
                print ("Boss")
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_RIGHT:
                    if f.direction == "right":
                        f.walk_right()
                    else:
                        f.walk_vel *= -1
                        f.direction = "right"

                if event.key == K_LEFT:
                    if f.direction == "left":
                        f.walk_left()
                    else:
                        f.walk_vel *= -1
                        f.direction = "left"
                if event.key == K_DOWN:
                    f.energy = 0
                if event.key == K_a:
                    f.punch()

                if event.key == K_s:
                    f.kick()

            if event.type == KEYUP:
                if event.key in [K_RIGHT, K_LEFT]:
                    f.idle()

        check_collisions(f, enemies, everything)

        clock.tick(20)

        everything.clear(screen, empty)
        everything.update()
        everything.draw(screen)
        pygame.display.flip()
            

if __name__ == "__main__":

    main()
