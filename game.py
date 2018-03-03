import time
import sys
import random

import pygame
from pygame.locals import Rect, DOUBLEBUF, QUIT, K_ESCAPE, KEYDOWN, K_DOWN, \
    K_LEFT, K_UP, K_RIGHT, KEYUP, K_LCTRL, K_RETURN, FULLSCREEN, RLEACCEL, K_a, K_s, HWSURFACE


X_MAX = 1280
Y_MAX = 480

character_sprites = {}


def load_sheet(sheet, top_left, bottom_right, clear_col, debug = False):
    images = []
    s_x, s_y = top_left
    e_x, e_y = bottom_right
    assert s_x < e_x and s_y < e_y
    data_in_col = False
    start_col = end_col = False
    # print ("From :: ", top_left, bottom_right)
    # print ("Outer loop will move from {} to {}".format(s_x, e_x))
    # print ("Inner loop will move from {} to {}".format(s_y, e_y))
    for x in range(s_x, e_x):
        # for q in range(s_y, e_y):
        #     col = sheet.get_at((x,q))
        #     print ("({},{}) ".format(x,q), col, " :: ", clear_col, " :: ", col == clear_col)
        # print ("----")
        data_in_col = any(sheet.get_at((x,y)) != clear_col for y in range(s_y, e_y)) #Starting line
        # print ("Data in col is ", data_in_col)
        if not start_col and data_in_col:
            # print ("Sprite starts at {}".format(x))
            start_col = x
        if start_col and not data_in_col:
            end_col = x
            r = (start_col, s_y, end_col, e_y)
            if debug:
                print ("Loading {}".format(r))
            img = pygame.Surface((end_col - start_col, e_y - s_y), pygame.SRCALPHA, 32).convert_alpha()
            img.blit(sheet, dest=(0,0), area = r)
            images.append(img)
            start_col = end_col = False
    return images

        


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
    sprite_cache = None

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

        if Enemy.sprite_cache:
             (self.idle_images_right,
              self.idle_images_left,
              self.walking_images_right,
              self.walking_images_left,
              self.attack_images_right,
              self.attack_images_left,
              self.impact_images_right,
              self.impact_images_left,
              self.dying_images_right,
              self.dying_images_left) = Enemy.sprite_cache
             
             self.idle_idx = self.walking_idx = self.impact_idx = self.attack_idx = self.dying_idx = 0

        else:

            # Load idle images
            self.idle_images = []
            self.idle_idx = 0
            self.idle_images = load_sheet(self.sheet, (12, 478), (1962, 672), self.sheet.get_at((0,0)))
            self.idle_images += list(reversed(self.idle_images))
            self.idle_images_right = self.idle_images
            self.idle_images_left = [pygame.transform.flip(x, True, False) for x in self.idle_images_right]

            # Load walking images
            self.walking_images = load_sheet(self.sheet, (0, 894), (1652, 1106), self.sheet.get_at((0,0)))
            self.walking_idx = 0
            self.walking_images_right = self.walking_images
            self.walking_images_left = [pygame.transform.flip(x, True, False) for x in self.walking_images_right]

            # Load kicking images
            self.attack_images = load_sheet(self.sheet, (0, 2984), (1652, 3186 ), self.sheet.get_at((0,0)))
            self.attack_idx = 0
            self.attack_images_right = self.attack_images
            self.attack_images_left = [pygame.transform.flip(x, True, False) for x in self.attack_images_right]

            # Load impact images
            self.impact_images = load_sheet(self.sheet, (1721, 1143), (2279, 1338), self.sheet.get_at((0,0)))
            self.impact_idx = 0
            self.impact_images_right = self.impact_images
            self.impact_images_left = [pygame.transform.flip(x, True, False) for x in self.impact_images_right]

            #Load dying images
            self.dying_images = load_sheet(self.sheet, (1734, 728), (3420, 898), self.sheet.get_at((0,0)))
            self.dying_idx = 0
            img2 = pygame.Surface((262, 170), pygame.SRCALPHA, 32).convert_alpha()
            # For a flickering effect after death
            self.dying_images.extend([self.dying_images[-1], img2]*4)
            self.dying_images_right = self.dying_images
            self.dying_images_left = [pygame.transform.flip(x, True, False) for x in self.dying_images_right]

            Enemy.sprite_cache  = (self.idle_images_right,
                                   self.idle_images_left,
                                   self.walking_images_right,
                                   self.walking_images_left,
                                   self.attack_images_right,
                                   self.attack_images_left,
                                   self.impact_images_right,
                                   self.impact_images_left,
                                   self.dying_images_right,
                                   self.dying_images_left)


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
        self.dying_idx += 0.25
        self.dying_idx %= len(self.dying_images)
        if self.dying_idx <= 6:
            x, y = self.enemy_pos
            x -= (self.walk_vel * 1)
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


class Boss(Enemy):
    INTRO = "intro"
    def __repr__(self):
        return "Boss ({}, {})".format(self.state, self.energy)

    def __init__(self, image, groups, pos, fighter):
        s = time.time()
        super(Boss, self).__init__(image, groups, pos, fighter)
        self.state = Boss.INTRO
        self.energy = 50
        self.death_sound = pygame.mixer.Sound("audio/boss-scream.wav")
        self.death_sound.set_volume(2)
        self.direction = "right"
        e = time.time()
        # print ("Time taken ", e - s)
        

    def load_images(self):
        # Load idling images
        self.idle_images = load_sheet(self.sheet, (0, 0), (2125, 288), self.sheet.get_at((0,0)))
        self.idle_idx = 0
        self.idle_images_right = self.idle_images
        self.idle_images_left = [pygame.transform.flip(x, True, False) for x in self.idle_images_right]

        # Load intro images
        self.intro_images = list(reversed(load_sheet(self.sheet, (0, 1921), (2344, 2442), self.sheet.get_at((0,0)))))
        self.intro_idx = 0

        # Load walking images
        self.walking_images = load_sheet(self.sheet, (0,1280), (3135, 1568), self.sheet.get_at((0,0)))
        self.walking_idx = 0
        self.walking_images_right = self.walking_images
        self.walking_images_left = [pygame.transform.flip(x, True, False) for x in self.walking_images_right]

        # Load dying images
        self.dying_images = load_sheet(self.sheet, (0, 5017), (2965, 5309), self.sheet.get_at((0,0)))
        self.dying_images.extend(load_sheet(self.sheet, (3039, 5228), (4755, 5335), self.sheet.get_at((0,0))))
        self.dying_images.extend([self.dying_images[-1]]*4)
        self.dying_idx = 0
        self.dying_images_right = self.dying_images
        self.dying_images_left = [pygame.transform.flip(x, True, False) for x in self.dying_images_right]

        # Load impacted images
        self.impact_images = []
        self.impact_idx = 0
        img = load_sprite(self.sheet, (188, 282), (12, 5017, 12+188, 5017+282))
        self.impact_images.append(img)
        img = load_sprite(self.sheet, (196, 282), (282, 5017, 282+196, 5017+282))
        self.impact_images.append(img)
        img = load_sprite(self.sheet, (229, 282), (567, 5017, 567+229, 5017+282))
        self.impact_images.append(img)
        img = load_sprite(self.sheet, (215, 282), (844, 5017, 844+215, 5017+282))
        self.impact_images.append(img)
        self.impact_images_right = self.impact_images
        self.impact_images_left = [pygame.transform.flip(x, True, False) for x in self.impact_images_right]

        # Load attack images
        self.attack_images = []
        self.attack_idx = 0
        img = load_sprite(self.sheet, (176, 284), (54, 4014, 54+176    ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (190, 284), (340, 4014, 340+190     ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (209, 284), (622, 4014, 622+209     ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (204, 284), (895, 4014, 895+204      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (224, 284), (1165, 4014,1165+224      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (239, 284), (1442, 4014, 1442+239      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (255, 284), (1755, 4014, 1755+255      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (381, 284), (2065, 4014, 2065+381      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (371, 284), (2490, 4014, 2490+371      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (348, 284), (2917, 4014, 2917+348      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (265, 284), (3324, 4014, 3324+265      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (277, 284), (3639, 4014, 3639+277      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (291, 284), (3975, 4014, 3975+291      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (268, 284), (4311, 4014, 4311+268      ,4014+284))
        self.attack_images.append(img)
        img = load_sprite(self.sheet, (244, 284), (4632, 4014, 4632+244      ,4014+284))
        self.attack_images.append(img)
        self.attack_images_right = self.attack_images
        self.attack_images_left = [pygame.transform.flip(x, True, False) for x in self.attack_images_right]

    def update_dying(self):
        self.image = self.image
        self.image = self.dying_images[int(self.dying_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.enemy_pos
        self.dying_idx += 0.25
        self.dying_idx %= len(self.dying_images)
        if self.dying_idx == 8:
            self.death_sound.play()
        if self.dying_idx == 0:
            self.kill()
            game_state['success'] = True


    def update_walking(self):
        self.image = self.walking_images[int(self.walking_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.enemy_pos
        self.walking_idx += 1
        self.walking_idx %= len(self.walking_images)
        x, y = self.enemy_pos
        x += self.walk_vel
        self.enemy_pos = x,y

    def update(self):
        if self.state == Boss.INTRO:
            self.update_intro()
        else:
            super(Boss, self).update()

    def update_intro(self):
        self.image = self.intro_images[int(self.intro_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.enemy_pos
        self.intro_idx += 1
        self.intro_idx %= len(self.intro_images)
        x, y = self.enemy_pos
        y += self.walk_vel/2
        self.enemy_pos = x,y
        if self.intro_idx == 0:
            self.state = Enemy.IDLING
            self.enemy_pos = x,450
    




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
    SUCCESS = "success"
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
        self.walk_vel = 20
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
        self.idle_idx = 0
        self.idle_images = load_sheet(self.sheet, (0,0), (1280, 224), self.sheet.get_at((0,0)))
        self.idle_images += list(reversed(self.idle_images))
        self.idle_images_right = self.idle_images
        self.idle_images_left = [pygame.transform.flip(x, True, False) for x in self.idle_images_right]

        # Load punching images
        self.punch_idx = 0
        self.punch_images = load_sheet(self.sheet, (1380,432), (1985, 646), self.sheet.get_at((0,0)))
        self.punch_images_right = self.punch_images
        self.punch_images_left = [pygame.transform.flip(x, True, False) for x in self.punch_images_right]

        # Load kick images
        self.kicking_images = load_sheet(self.sheet, (1380, 2954), (2600, 3162) , self.sheet.get_at((0,0)))
        self.kicking_idx = 0
        self.kicking_images_right = self.kicking_images
        self.kicking_images_left = [pygame.transform.flip(x, True, False) for x in self.kicking_images_right]

        # Load walking images
        self.walking_images = load_sheet(self.sheet, (2, 689), (983, 915) , self.sheet.get_at((0,0)))
        self.walking_idx = 0
        self.walking_images_right = self.walking_images
        self.walking_images_left = [pygame.transform.flip(x, True, False) for x in self.walking_images_right]

        # Load impacted images
        self.impacted_images = load_sheet(self.sheet, (381, 1390), (1126, 1601) , self.sheet.get_at((0,0)))
        self.impacted_idx = 0
        self.impacted_images_right = self.impacted_images
        self.impacted_images_left = [pygame.transform.flip(x, True, False) for x in self.impacted_images_right]

        # Load dying images
        self.dying_images = load_sheet(self.sheet, (1311, 0), (1955, 242) , self.sheet.get_at((0,0)))
        self.dying_images += load_sheet(self.sheet, (1311, 274), (2041, 419) , self.sheet.get_at((0,0)))
        self.dying_idx = 0
        self.dying_images_right = self.dying_images
        self.dying_images_left = [pygame.transform.flip(x, True, False) for x in self.dying_images_right]

        # Load success images
        self.success_images = load_sheet(self.sheet, (0, 2581), (960, 2839), self.sheet.get_at((0,0)))
        self.success_images.extend([self.success_images[-1]]*10)
        self.success_idx = 0


    def success(self):
        self.state = Fighter.SUCCESS

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
                   Fighter.SUCCESS       : self.update_success,
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

    def update_success(self):
        self.image = self.success_images[int(self.success_idx)]
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.fighter_pos
        if 'done' not in game_state:
            self.success_idx += 0.25
            self.success_idx %= len(self.success_images)

        if self.success_idx == 0:
            self.state = Fighter.IDLING
            game_state['done'] = True
            self.image = self.success_images[-1]

            self.rect = self.image.get_rect()
            x, y = self.fighter_pos
            middle = X_MAX/2

            if abs (x - middle) > 5:
                d = abs(x-middle)/(x-middle)
                x -= 3*d
                self.fighter_pos = x,y
        



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
        self.black_alpha = 0

        self.image = pygame.Surface((X_MAX, Y_MAX),pygame.SRCALPHA, 32).convert_alpha()
        self.background = pygame.image.load(bgimage).convert()
        self.image.blit(self.background, dest = (0,0))

        self.rect = self.image.get_rect()

        self.vertical = self.to = 0
        self.vel = 0
        self.image.blit(self.sheet, dest = (0,0), area = (self.vertical,0,X_MAX, Y_MAX))
        self.add(groups)
        
    def update(self):

        _, _, t, _ = self.sheet.get_rect()
        new_pos = self.vertical + self.vel

        if new_pos >= 0 and new_pos <= t - X_MAX:
            self.vertical = new_pos
        
        if abs(self.vertical - self.to) < 50:
            self.to = self.vertical
            self.vel = 0
        else:
            self.image.blit(self.background, dest = (0,0))
            self.image.blit(self.sheet, dest = (0,0), area = (self.vertical,0,X_MAX, Y_MAX))

        if 'done' in game_state and self.black_alpha < 255:
            self.image.blit(self.sheet, dest = (0,0), area = (self.vertical,0,X_MAX, Y_MAX))
            self.black.fill((0,0,0,self.black_alpha))
            self.image.blit(self.black, dest = (0,0))
            self.black_alpha += 20
            


    def scroll_right(self):
        self.to = self.vertical + 150
        self.vel = 50

    def scroll_left(self):
        self.to = self.vertical - 150
        self.vel = -50

def init_pygame(groups):
    pygame.mixer.init()
    screen = pygame.display.set_mode((X_MAX, Y_MAX), DOUBLEBUF|HWSURFACE|FULLSCREEN)
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

    boss = False
    boss_counter = 100
    screen, empty = init_pygame(everything)
    b = Background("sprites/bg0.png", "sprites/bg1.png", [everything])
    f = Fighter("sprites/fighter-terry.png", everything, (100, 450), b)
    EnergyBar((10,10), everything, f.energy, f)
    death_counter = 75

    while f.walking_in:
        clock.tick(20)
        everything.clear(screen, empty)
        everything.update()
        everything.draw(screen)
        pygame.display.flip()

    while True:
        if death_counter == 0:
            sys.exit(0)
        if 'over' in game_state:
            death_counter -=1
        if 'success' in game_state:
            f.success()
        
        if b.vertical > 3000 and not boss:
            if boss_counter == 100:
                if pygame.mixer.get_init():
                    pygame.mixer.fadeout(100)
                for i in enemies:
                    i.state = Enemy.DYING
            elif boss_counter == 70:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load("music/boss-2.mp3")
                    pygame.mixer.music.set_volume(0.4)
                    pygame.mixer.music.play(-1)
            elif boss_counter == 0:
                boss = Boss("sprites/boss.png", [everything, enemies], (850, 450), f)
                EnergyBar((10,40), everything, boss.energy, boss)
            boss_counter -= 1
        else:
            if len(enemies) != 1 and 'over' not in game_state and 'success' not in game_state:
                Enemy("sprites/enemy-gato.png", [everything, enemies], (random.choice([-150, 1350]), 450), f)


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
                    f.success()
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
    print ("""
    <- to move left
    -> to move right

    a to hit
    s to kick
    """)
    main()
