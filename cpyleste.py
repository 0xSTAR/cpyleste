#!/usr/bin/env python3

import hagia
from hagia.utils import *
from functools import cached_property, lru_cache
from numba import jit,njit,int8,float32,int32
from numba.experimental import jitclass
from numba.experimental.jitclass import boxing
import math

h = hagia.Engine()

room:Vec2i = Vec2i(0,0)
objects:list = []
types:list = []
freeze:int = 0
shake:int = 0
will_restart:int = False
delay_restart:int = 0
got_fruit:list = []
has_dashed:int = False
sfx_timer:int = 0
has_key:bool = False
pause_player:bool = False
flash_bg:bool= False
music_timer:int = 0

new_bg = None

seconds = 0
frames = 0
minutes = 0

k_left:int = 2
k_right:int = 3
k_up:int = 0
k_down:int = 1
k_jump:int = 4
k_dash:int = 5

# HELPERS
#-------------------

#def get_player(self):
#  for o in objects:
#    if type(o) == player_spawn or type(o) == player:
#      return o

@njit
def clamp(val:float32,a:float32,b:float32) -> float32:
    return max(a,min(b,val))

@njit
def appr(val:float32,target:float32,amount:float32) -> float32:
    return (
        val > target and
        max(val - amount, target) or
        min(val + amount,target)
    )

@njit
def sign(v:float32) -> int8:
    return v > 0 and 1 or v < 0 and -1 or 0

@njit
def maybe() -> bool:
    return rnd(1) < 0.5

@njit
def dmaybe() -> int:
    x = rnd(2)
    return (
        x == 0 and -1 or x > 0 and 1
    )
def solid_at(x:int,y:int,w:int,_h:int) -> bool:
    return tile_flag_at(x,y,w,_h,0)

def ice_at(x:int,y:int,w:int,_h:int) -> bool:
    return tile_flag_at(x,y,w,_h,4)

def tile_flag_at(x:int,y:int,w:int,_h:int,flag:int) -> bool:
    """for i in range(
            max(0,flr(x/8)+1),min(15,flr((x+w-1)/8)+1)
    ):
        for j in range(
            max(0,flr(y/8)+1),min(15,flr((y+_h-1)/8)+1)
        ):
            if h.fget(tile_at(i,j),flag):
                return True
    return False"""
    for i in range(max(0, int(x / 8)), int(min(15, (x + w - 1) / 8)) + 1):
      for j in range(max(0, int(y / 8)), int(min(15, (y + _h - 1) / 8)) + 1):
        if h.fget(tile_at(i, j), flag):
          return True
    return False

def tile_at(x:int,y:int) -> int:
    return h.mget(room.x * 16 + x, room.y * 16 + y)

def spikes_at(
    x:int,
    y:int,
    w:int,
    _h:int,
    xspd:float,
    yspd:float
) -> bool:
    """for i in range(
        max(0,flr(x/8)+1),min(15,flr((x+w-1)/8)+1)
    ):
        for j in range(
            max(0,flr(y/8)+1),min(15,flr((y+h-1)/8)+1)
        ):
            tile = tile_at(i,j)
            if (
                tile==17 and
                ((y+h-1)%8>=6 or y+h==j*8+8) and
                yspd >= 0
            ):
                return True
            elif tile==27 and y%8<=2 and yspd<=0:
                return True
            elif tile==43 and x%8<=2 and yspd<=0:
                return True
            elif (
                tile==59 and
                ((x+w-1)%8>=6 or x+w==i*8+8) and
                xspd>= 0
            ):
                return True
    return False"""
    for i in range(max(0, int(x / 8)), int(min(15, (x + w - 1) / 8)) + 1):
      for j in range(max(0, int(y / 8)), int(min(15, (y + _h - 1) / 8)) + 1):
        tile = tile_at(i, j)
        if (
            (tile == 17 and ((y + _h - 1) % 8 >= 6 or y + _h == j * 8 + 8) and yspd >= 0) or
             (tile == 27 and y % 8 <= 2 and yspd <= 0) or
             (tile == 43 and x % 8 <= 2 and xspd <= 0) or
             (tile == 59 and ((x + w - 1) % 8 >= 6 or x + w == i * 8 + 8) and xspd >= 0)
        ):
          return True
    return False

# ----------------

#@njit # EQU jit(nopython=True)
def title_screen():
    global got_fruit
    global frames
    global deaths
    global max_djump
    global start_game
    global start_game_flash

    def RESET_GLOBALS():
        global room, objects, types, freeze, shake
        global will_restart, delay_restart, got_fruit
        global has_dashed, sfx_timer, has_key, pause_player
        global flash_bg, music_timer, new_bg, seconds, frames, minutes
        #room:Vec2i = Vec2i(0,0)
        room = Vec2i(0,0)
        objects = []
        #types = []
        freeze = 0
        shake = 0
        will_restart = False
        delay_restart = 0
        got_fruit = []
        has_dashed = False
        sfx_timer = 0
        has_key = False
        pause_player = False
        flash_bg= False
        music_timer = 0

        new_bg = None

        seconds = 0
        frames = 0
        minutes = 0

    RESET_GLOBALS()

    got_fruit = []
    for i in range(32):
        add(got_fruit,False)
    frames = 0
    deaths = 0
    max_djump = 1
    start_game = False
    start_game_flash = 0
    h.music(4,0)
    load_room(7,3)

def begin_game():
    global frames, seconds, minutes
    global music_timer, start_game
    frames = 0
    seconds = 0
    minutes = 0
    music_timer = 0
    start_game = False
    h.music(0,0)
    load_room(0,0)

#@njit
def level_index() -> int:
    return room.x%8 + room.y*8

#@njit
def is_title() -> bool:
    return level_index()==31

def restart_room():
    global will_restart
    global delay_restart
    will_restart = True
    delay_restart = 15

#@njit
def next_room():
    global objects
    #objects = []
    if room.x == 2 and room.y == 1:
        h.music(3)
    elif room.x == 3 and room.y == 1:
        h.music(2)
    elif room.x == 4 and room.y == 2:
        h.music(3)
    elif room.x == 5 and room.y == 2:
        h.music(1)
    elif room.x == 5 and room.y == 3:
        h.music(3)

    #print(f"x:{room.x}\ny:{room.y}")

    if room.x == 7:
        load_room(0,room.y+1)
    else:
        load_room(room.x+1,room.y)



def load_room(x,y):
    global has_dashed, has_key
    global objects
    has_dashed=False
    has_key = False

    # remove existing objects
    #for o in objects:
    #    destroy_object(o)
    objects.clear()

    # current room
    global room
    room.x = x
    room.y = y

    # entities
    for tx in range(16):
        for ty in range(16):
            tile = h.mget(room.x*16+tx,room.y*16+ty)
            if tile == 11:
                init_object(platform,tx*8,ty*8).dir=-1
            elif tile==12:
                init_object(platform,tx*8,ty*8).dir=1
            else:
                for t in types:
                    if t.tile == tile:
                        init_object(t,tx*8,ty*8)
    #print([ob._type for ob in objects])

    if not is_title():
        #init_object(room_title,0,0)
        pass


# -----------------------------------------

particle_spec = [
    ('x',float32),
    ('y',float32),
    ('s',int8),
    ('spd',float32),
    ('off',int8),
    ('c',int8)
]
@jitclass(particle_spec)
class particle:
    def __init__(
        self,
        x,
        y,
        s,
        spd,
        off,
        c
    ) -> None:
        self.x = x
        self.y = y
        self.s = s
        self.spd = spd
        self.off = off
        self.c = c

particles = []
for i in range(19):
    add(particles,
        particle(
            rnd(128),
            rndrng(110,250),
            1,#0+flr(rnd(5)/4),,
            0.25+rnd(5),
            rndrng(-128,128),
            6+flr(0.5+rnd(1))
        )
    )

cloud_spec = [
    ("x",int8),
    ("y",int8),
    ("spd",int8),
    ("w",int8)
]
@jitclass(cloud_spec)
class cloud:
    def __init__(
        self,
        x,
        y,
        spd,
        w
    ) -> None:
        self.x = x
        self.y = y
        self.spd = spd
        self.w = w

clouds = []
for i in range(17):
    add(
        clouds,
        cloud(
            rnd(128),
            rnd(128),
            1+rnd(4),
            32+rnd(32)
        )
    )

dead_particles = []

#dead_particle_spec = [
#    ("x",int8),
#    ("y",int8),
#    ("t",int8),
#    #("spd",Vec2f)
#]
#@jitclass(dead_particle_spec)
@dataclass
class dead_particle:
    x:int
    y:int
    t:int
    spd:Vec2f
    #def __init__(
    #    self,
    #    x:int8,
    #    y:int8,
    #    t:int8,
    #    spd:Vec2f
    #):
    #    self.x:int8 = x
    #    self.y:int8 = y
    #    self.t:int8 = t
    #    self.spd:Vec2f = spd

# ----------------------------------------

#b_object_spec = [
    #("_type",JitClassType),
#    ("collideable",int8),
#    ("solids",int8),
#    ("spr",int8),
    #("flip",JitClassType),
#    ("x",float32),
#    ("y",float32),
    #("hitbox",JitClassType),
    #("spd",JitClassType),
    #("rem",JitClassType)
#]
#@jitclass(b_object_spec)
class b_object:
    def __init__(
        self,
        _type:object,
        collideable:bool,
        solids:bool,
        spr:int8,
        flip:Vec2b,
        x:float32,
        y:float32,
        hitbox:Vec4i,
        spd:Vec2f,
        rem:Vec2f
    ) -> None:
        self._type = _type
        self.collideable = collideable
        self.solids = solids
        self.spr = spr
        self.flip = flip
        self.x = x
        self.y = y
        self.hitbox = hitbox
        self.spd = spd
        self.rem = rem

    def is_solid(self,ox,oy) -> bool:
        if oy>0 and not self.check(platform,ox,0) and self.check(platform,ox,oy):
            return True
        """return (
            solid_at(self.x+self.hitbox.x+ox,self.y+self.hitbox.y+oy,self.hitbox.w,self.hitbox.h) or
            self.check(fall_floor,ox,oy) or
            self.check(fake_wall,ox,oy)
        )"""
        return tile_flag_at(self.x + self.hitbox.x + ox, self.y + self.hitbox.y + oy, self.hitbox.w, self.hitbox.h, 0)\
          or self.check(fall_floor, ox, oy)\
          or self.check(fake_wall, ox, oy)

    def is_ice(self,ox,oy) -> bool:
        return tile_flag_at(self.x+self.hitbox.x+ox,self.y+self.hitbox.y+oy,self.hitbox.w,self.hitbox.h,4)

    def collide(self,_typ,ox,oy) -> bool:
        for i in range(count(objects)): # used to be in range (1,count(objects))
            other = objects[i]
            if (other != None and other._type == _typ and other != self and other.collideable and
                other.x+other.hitbox.x+other.hitbox.w > self.x+self.hitbox.x+ox and
                other.y+other.hitbox.y+other.hitbox.h > self.y+self.hitbox.y+oy and
                other.x+other.hitbox.x < self.x+self.hitbox.x+self.hitbox.w+ox and
                other.y + other.hitbox.y < self.y + self.hitbox.y + self.hitbox.h+oy
            ):
                return other
        return None

    def check(self,_typ,ox,oy) -> bool:
        """return self.collide(_typ,ox,oy)"""
        for other in objects:
          if type(other) == _typ and other != self and other.collideable and \
           other.x + other.hitbox.x + other.hitbox.w > self.x + self.hitbox.x + ox and \
           other.y + other.hitbox.y + other.hitbox.h > self.y + self.hitbox.y + oy and \
           other.x + other.hitbox.x < self.x + self.hitbox.x + self.hitbox.w + ox and \
           other.y + other.hitbox.y < self.y + self.hitbox.y + self.hitbox.h + oy:
            return other
        return None


    def move(self,ox,oy) -> None:
        """# [x]
        self.rem.x += ox
        amount = xround(self.rem.x)
        self.rem.x -= amount
        self.move_x(amount,0)

        # [y]
        self.rem.y += oy
        amount = xround(self.rem.y)
        self.rem.y -= amount
        self.move_y(amount)"""
        self.rem.x += ox
        amt = math.floor(self.rem.x + 0.5)
        self.rem.x -= amt
        self.move_x(amt, 0)
        self.rem.y += oy
        amt = math.floor(self.rem.y + 0.5)
        self.rem.y -= amt
        self.move_y(amt)

    def move_x(self,amount,start) -> None:
        if self.solids:
            step = sign(amount)
            for i in range(start,abs(amount) + 1):#+1):
                if not self.is_solid(step,0):
                    self.x += step
                else:
                    self.spd.x = 0
                    self.rem.x = 0
                    break
        else:
            self.x += amount

    def move_y(self,amount) -> None:
        if self.solids:
            step = sign(amount)
            for i in range(abs(amount) + 1):
                if not self.is_solid(0,step):
                    self.y += step
                else:
                    self.spd.y = 0
                    self.rem.y = 0
                    break
        else:
            self.y += amount



def init_object(_type,x:int,y:int) -> object:
    if _type.if_not_fruit != None and got_fruit[1+level_index()]:
        return
    o = b_object(
        _type,
        True,
        True,
        _type.tile,
        Vec2b(False,False),
        x,
        y,
        Vec4i(0,0,8,8),
        Vec2f(0,0),
        Vec2f(0,0)
    )

    add(objects,o)
    if hasattr(o._type,"init"):
        o._type.init(o)
    return o

hair_spec = [
    ("x",float32),
    ("y",float32),
    ("size",int8),
]
@jitclass(hair_spec)
class hair_obj:
    def __init__(self,x,y,size) -> None:
        self.x = x
        self.y = y
        self.size = size

def create_hair(this):
    this.hair = []
    for i in range(5):
        add(this.hair,
            hair_obj(
                this.x,
                this.y,
                max(1,min(2,3-i))
            )
        )

def set_hair_color(djump):
    h.pal(
        8,
        (djump==1 and 8 or djump==2 and
            (7+flr((frames/3)%2)*4) or 12
        )
    )

def draw_hair(o,facing):
    last = Vec2f(
        o.x+4-facing*2,
        o.y+(h.btn(k_down) and 4 or 3)
    )
    for hr in o.hair:
        hr.x += (last.x-hr.x)/1.5
        hr.y += (last.y + 0.5 - hr.y)/1.5
        h.circfill(hr.x,hr.y,hr.size,8)
        last = hr

def unset_hair_color():
    h.pal(8,8)
    #h.rpal()

def destroy_object(o):
    delete(objects,o)
    #del objects[list.index(type(o))]
    #del o
    #for _o in objects:
    #    if _o == o:
    #        del _o

def kill_player(o):
    global sfx_timer, deaths, shake, dead_particles
    sfx_timer = 12
    h.sfx(0)
    deaths+=1
    shake=10
    destroy_object(o)
    dead_particles = []
    for dir in range(8):
        angle = dir/8
        add(
            dead_particles,
            dead_particle(
                o.x+4,
                o.y+4,
                10,
                Vec2f(
                    sin(angle)*3 * dmaybe(),
                    cos(angle)*3 * dmaybe()
                )
            )
        )
    restart_room()

#@njit
def psfx(n):
    if sfx_timer <= 0:
        h.sfx(n)

# -----------------------------------------

class player_spawn:
    tile=1
    if_not_fruit = None
    def init(self):
        h.sfx(4)
        self.spr = 3
        self.target = Vec2f(self.x,self.y)
        self.y = 128
        self.spd.y = -4
        self.state = 0
        self.delay = 0
        self.solids = False
        create_hair(self)

    def update(self):
        global shake
        # jumping up
        if self.state == 0:
            if self.y < self.target.y+16:
                self.state = 1
                self.delay = 3
        # falling
        elif self.state==1:
            self.spd.y+=0.5
            if self.spd.y > 0 and self.delay > 0:
                self.spd.y = 0
                self.delay -= 1
            if self.spd.y > 0 and self.y > self.target.y:
                self.y = self.target.y
                self.spd = Vec2f(0,0)
                self.state = 2
                self.delay = 5
                shake = 5
                init_object(smoke,self.x,self.y+4)
                h.sfx(5)
        # landing
        elif self.state == 2:
            self.delay -= 1
            self.spr = 6
            if self.delay < 0:
                destroy_object(self)
                init_object(player,self.x,self.y)

    def draw(self):
        global max_djump
        set_hair_color(max_djump)
        draw_hair(self,1)
        h.spr(self.spr,self.x,self.y,1,1,self.flip.x,self.flip.y)
        unset_hair_color()

add(types,player_spawn)

class spring:
    tile=18
    if_not_fruit = None
    def init(self):
        self.hide_in = 0
        self.hide_for = 0

    def update(self):
        global max_djump
        if self.hide_for > 0:
            self.hide_for -= 1
            if self.hide_for <= 0:
                self.spr = 18
                self.delay = 0
        elif self.spr == 18:
            hit = self.collide(player,0,0)
            if hit != None and hit.spd.y >= 0:
                self.spr = 19
                hit.y = self.y-4
                hit.spd.x *= 0.2
                hit.spd.y = -3
                hit.djump = max_djump
                self.delay = 10
                init_object(smoke,self.x,self.y)

                # breakable below us
                below = self.collide(fall_floor,0,1)
                if below != None:
                    break_fall_floor(below)

                psfx(8)
        elif self.delay > 0:
            self.delay -= 1
            if self.delay <= 0:
                self.spr = 18

        # begin hiding
        if self.hide_in > 0:
            self.hide_in -= 1
            if self.hide_in <= 0:
                self.hide_for = 60
                self.spr = 0

add(types,spring)

def break_spring(o):
    o.hide_in=15

class balloon:
    if_not_fruit = None
    tile = 22
    def init(self):
        self.offset = rnd(1)
        self.start = self.y
        self.timer = 0
        self.hitbox = Vec4i(-1,-1,10,10)

    def update(self):
        global max_djump
        if self.spr == 22:
            self.offset += 0.01
            self.y = self.start+sin(self.offset)*2
            hit = self.collide(player,0,0)
            if hit != None and hit.djump < max_djump:
                psfx(6)
                init_object(smoke,self.x,self.y)
                hit.djump = max_djump
                self.spr = 0
                self.timer = 60
        elif self.timer > 0:
            self.timer -= 1
        else:
            psfx(7)
            init_object(smoke,self.x,self.y)
            self.spr = 22

    def draw(self):
        if self.spr == 22:
            h.spr(13+(self.offset*8)%3,self.x,self.y+6)
            h.spr(self.spr,self.x,self.y)

add(types,balloon)

class fall_floor:
    tile=23
    if_not_fruit = None
    def init(self):
        self.state = 0
        self.solid = True
        #self.hitbox.w = 8
        #self.hitbox.h = 8

    def update(self):
        # idling
        if self.state == 0:
            if self.check(player,0,-1) or self.check(player,-1,0) or self.check(player,1,0):
                break_fall_floor(self)
        # shaking
        elif self.state == 1:
            self.delay -= 1
            if self.delay <= 0:
                self.state = 2
                self.delay = 60 # how long it hides for
                self.collideable = False
        #invisible waiting to reset
        elif self.state == 2:
            self.delay -= 1
            if self.delay <= 0 and not self.check(player,0,0):
                psfx(7)
                self.state = 0
                self.collideable = True
                init_object(smoke,self.x,self.y)

    def draw(self):
        if self.state != 2:
            if self.state != 1:
                h.spr(23,self.x,self.y)
            else:
                h.spr(23+(15-self.delay)//5,self.x,self.y)

add(types,fall_floor)

def break_fall_floor(o):
    if o.state == 0:
        psfx(15)
        o.state = 1
        o.delay = 15 # how long until it falls
        init_object(smoke,o.x,o.y)
        hit = o.collide(spring,0,-1)
        if hit != None:
            break_spring(hit)

class smoke:
    tile = None
    if_not_fruit = None
    def init(self):
        self.spr = 29
        self.spd.y = -0.1
        self.spd.x = 0.3+rnd(0.2)
        self.x += -1+rnd(2)
        self.y += -1 + rnd(2)
        self.flip.x = maybe()
        self.flip.y = maybe()
        self.solids = False

    def update(self):
        self.spr+=0.2
        if self.spr >= 32:
            destroy_object(self)


class fruit:
    tile=26
    if_not_fruit=True

    def init(self):
        self.start = self.y
        self.off = 0

    def update(self):
        global max_djump,sfx_timer,got_fruit
        hit = self.collide(player,0,0)
        if hit != None:
            hit.djump = max_djump
            sfx_timer = 20
            h.sfx(13)
            got_fruit[1+level_index()] = True
            init_object(lifeup,self.x,self.y)
            destroy_object(self)
        self.off += 1
        self.y = self.start+sin(self.off/40)*2.5

add(types,fruit)

class fly_fruit:
    tile=28
    if_not_fruit=True
    def init(self):
        self.start = self.y
        self.fly = False
        self.step = 0.5
        self.solids = False
        self.sfx_delay = 8

    def update(self):
        global sfx_timer
        global has_dashed,max_djump,got_fruit
        # fly away
        if self.fly:
            if self.sfx_delay > 0:
                self.sfx_delay -= 1
                if self.sfx_delay <= 0:
                    sfx_timer = 20
                    h.sfx(14)
            self.spd.y = appr(self.spd.y,-3.5,0.25)
            if self.y < -16:
                destroy_object(self)
        # wait
        else:
            if has_dashed:
                self.fly = True
            self.step += 0.05
            self.spd.y = sin(self.step) * 0.5

        # collect
        hit = self.collide(player,0,0)
        if hit != None:
            hit.djump = max_djump
            sfx_timer = 20
            h.sfx(13)
            got_fruit[1+level_index()] = True
            init_object(lifeup,self.x,self.y)
            destroy_object(self)

    def draw(self):
        off = 0
        if not self.fly:
            dir = sin(self.step )
            if dir < 0:
                off = 1+max(0,sign(self.y-self.start))
        else:
            off = (off+0.25)%3

        h.spr(45+off,self.x-6,self.y-2,1,1,True,False)
        h.spr(self.spr,self.x,self.y)
        h.spr(45+off,self.x+6,self.y-2)

add(types,fly_fruit)

class lifeup:
    tile = None
    if_not_fruit = None
    def init(self):
        self.spd.y = -0.25
        self.duration = 30
        self.x -= 2
        self.y -= 4
        self.flash = 0
        self.solids = False

    def update(self):
        self.duration -= 1
        if self.duration <= 0:
            destroy_object(self)

    def draw(self):
        self.flash += 0.5

        h.hprint("1000",self.x-2,self.y,7+self.flash%2)

class fake_wall:
    tile=64
    if_not_fruit=True
    def update(self):
        global sfx_timer
        self.hitbox = Vec4i(-1,-1,18,18)
        hit = self.collide(player,0,0)
        if hit != None and hit.dash_effect_time > 0:
            hit.spd.x = -sign(hit.spd.x)*1.5
            hit.spd.y = -1.5
            hit.dash_time = -1
            sfx_timer = 20
            h.sfx(16)
            destroy_object(self)
            init_object(smoke,self.x,self.y)
            init_object(smoke,self.x+8,self.y)
            init_object(smoke,self.x,self.y+8)
            init_object(smoke,self.x+8,self.y+8)
            init_object(fruit,self.x+4,self.y+4)
        self.hitbox = Vec4i(0,0,16,16)

    def draw(self):
        h.spr(64,self.x,self.y)
        h.spr(65,self.x+8,self.y)
        h.spr(80,self.x,self.y+8)
        h.spr(81,self.x+8,self.y+8)

add(types,fake_wall)

class key:
    tile=8
    if_not_fruit=True
    def update(self):
        global sfx_timer,has_key
        was = flr(self.spr)
        self.spr = 9+(sin(frames/30)+0.5)*1
        _is = flr(self.spr)
        if _is == 10 and _is != was:
            self.flip.x = not self.flip.x
        if self.check(player,0,0):
            h.sfx(23)
            sfx_timer = 10
            has_key = True
            destroy_object(self)

add(types,key)

class chest:
    tile = 20
    if_not_fruit = True
    def init(self):
        self.x -= 4
        self.start = self.x
        self.timer = 20

    def update(self):
        global has_key,sfx_timer
        if has_key:
            self.timer -= 1
            self.x = self.start - 1 +rnd(3)
            if self.timer <= 0:
                sfx_timer = 20
                h.sfx(16)
                init_object(fruit,self.x,self.y-4)
                destroy_object(self)

add(types,chest)

class platform:
    tile = None
    if_not_fruit = None
    def init(self):
        self.x -= 4
        self.solids = False
        self.hitbox.w = 16
        #self.hitbox.h = 8
        self.last = self.x

    def update(self):
        self.spd.x = self.dir*0.65
        if self.x < -16:self.x = 128
        elif self.x>128:
            self.x=-16
        if not self.check(player,0,0):
            hit = self.collide(player,0,-1)
            if hit != None:
                hit.move_x(self.x-self.last,1)
        self.last = self.x

    def draw(self):
        h.spr(11,self.x,self.y-1)
        h.spr(12,self.x+8,self.y-1)

# no messages in this version just yet
#class message:
#    tile=86
#    last = 0
#    def draw(self):
bc_pc_spec = [
    ("x",int8),
    ("y",int8),
    ("h",int8),
    ("spd",float32)
]
@jitclass(bc_pc_spec)
class big_chest_particle:
    def __init__(self,x,y,h,spd):
        self.x = x
        self.y = y
        self.h = h
        self.spd = spd


class big_chest:
    tile = 96
    if_not_fruit = None
    def init(self):
        self.state = 0
        self.hitbox.w = 16
    def draw(self):
        global pause_player,shake,flash_bg,new_bg
        if self.state == 0:
            hit = self.collide(player,0,8)
            if hit != None and hit.is_solid(0,1):
                h.music(-1,500)
                h.sfx(16)
                pause_player = True
                hit.spd.x = 0
                hit.spd.y = 0
                self.state = 1
                init_object(smoke,self.x,self.y)
                init_object(smoke,self.x+8,self.y)
                self.timer = 60
                self.particles  = []
            h.spr(96,self.x,self.y)
            h.spr(97,self.x+8,self.y)
        elif self.state == 1:
            self.timer -= 1
            shake = 5
            flash_bg = True
            if self.timer <= 45 and count(self.particles)<50:
                add(self.particles,big_chest_particle(
                    1+rnd(14),
                    0,
                    32+rnd(32),
                    8+rnd(8)
                ))
            if self.timer < 0:
                self.state = 2
                self.particles = []
                flash_bg = False
                new_bg = True
                init_object(orb,self.x+4,self.y+4)
                pause_player=False
            for p in self.particles:
                p.y+=p.spd
                h.line(self.x+p.x,self.y+8-p.y,self.x+p.x,min(self.y+8-p.y+p.h,self.y+8),7)
        h.spr(112,self.x,self.y+8)
        h.spr(113,self.x+8,self.y+8)

add(types,big_chest)

class orb:
    tile = None
    if_not_fruit = None
    def init(self):
        self.spd.y = -4
        self.solids = False
        self.particles = []

    def draw(self):
        global freeze,shake
        global max_djump
        self.spd.y = appr(self.spd.y,0,0.5)
        hit = self.collide(player,0,0)
        if self.spd.y == 0 and hit != None:
            music_timer = 45
            h.sfx(20)
            freeze = 10
            shake = 10
            destroy_object(self)
            max_djump = 2
            hit.djump = 2

        h.spr(102,self.x,self.y)
        off = frames/30
        for i in range(8):
            h.circfill(
                self.x+4+cos(off+i/8)*8,self.y+4+sin(off+i/8)*8,1,7
            )

class flag:
    tile=118
    if_not_fruit = None
    def init(self):
        global got_fruit
        self.x += 5
        self.score = 0
        self.show = False
        for i in range(1,count(got_fruit)):
            if got_fruit[i]:
                self.score += 1

    def draw(self):
        global frames, deaths, sfx_timer
        self.spr = 118+(frames/5)%3
        h.spr(self.spr,self.x,self.y)
        if self.show:
            h.rectfill(32,2,96,31,0)
            h.spr(26,55,6)
            h.hprint("x"+self.score,64,9,7)
            #draw_time(49,16)
            h.hprint("deaths:"+deaths)
        elif self.check(player,0,0):
            h.sfx(55)
            sfx_timer = 30
            self.show = True

add(types,flag)

# no room title just yet
#class room_tile:

class player:
    tile = None
    if_not_fruit = None
    def init(self):
        self.p_jump = False
        self.p_dash = False
        self.grace = 0
        self.jbuffer = 0
        self.djump = max_djump
        self.dash_time = 0
        self.dash_effect_time = 0
        self.dash_target = Vec2f(0,0)
        self.dash_accel = Vec2f(0,0)
        self.hitbox = Vec4i(1,3,6,5)
        self.spr_off = 0
        self.was_on_ground = False
        create_hair(self)

    def update(self):
        global pause_player, has_dashed, max_djump
        global freeze, shake

        if pause_player:return

        input = h.btn(k_right) and 1 or (h.btn(k_left) and -1 or 0)

        # spikes collide
        if spikes_at(
            self.x+self.hitbox.x,
            self.y+self.hitbox.y,
            self.hitbox.w,self.hitbox.h,
            self.spd.x,self.spd.y
        ):
            kill_player(self)

        # bottom death
        if self.y > 128:
            kill_player(self)

        on_ground:bool = self.is_solid(0,1)
        on_ice:bool = self.is_ice(0,1)

        # smoke particles
        if on_ground and not self.was_on_ground:
            init_object(smoke,self.x,self.y+4)

        jump:bool = h.btn(k_jump) and not self.p_jump
        self.p_jump:bool = h.btn(k_jump)
        if jump:
            self.jbuffer = 4
        elif self.jbuffer > 0:
            self.jbuffer -= 1

        dash = h.btn(k_dash) and not self.p_dash
        self.p_dash = h.btn(k_dash)

        if on_ground:
            self.grace = 6
            if self.djump < max_djump:
                psfx(21)
                self.djump = max_djump
        elif self.grace > 0:
            self.grace -= 1

        self.dash_effect_time -= 1

        if self.dash_time > 0:
            init_object(smoke,self.x,self.y)
            self.dash_time -= 1
            self.spd.x = appr(
                self.spd.x, self.dash_target.x,
                self.dash_accel.x
            )
            self.spd.y = appr(
                self.spd.y,self.dash_target.y,
                self.dash_accel.y
            )

        else:
            # move
            maxrun = 1
            accel = 0.6
            deccel = 0.15
            if not on_ground:
                accel = 0.4
            elif on_ice:
                accel = 0.05
                if input == (self.flip.x and -1 or 1):
                    accel = 0.05

            if abs(self.spd.x) > maxrun:
                self.spd.x = appr(self.spd.x,sign(self.spd.x)*maxrun,deccel)
            else:
                self.spd.x = appr(self.spd.x,input*maxrun,accel)

            if self.spd.x != 0:
                self.flip.x = self.spd.x < 0

            # gravity

            maxfall = 2
            gravity = 0.21

            if abs(self.spd.y) <= 0.15:
                gravity *=0.5

            # wall slide
            if input != 0 and self.is_solid(input,0) and not self.is_ice(input,0):
                maxfall = 0.4
                if rnd(10) < 2:
                    init_object(smoke,self.x+input*6,self.y)

            if not on_ground:
                self.spd.y = appr(self.spd.y,maxfall,gravity)

            # jump
            if self.jbuffer > 0:
                if self.grace > 0:
                    # normal jump
                    psfx(1)
                    self.jbuffer = 0
                    self.grace = 0
                    self.spd.y = -2
                    init_object(smoke,self.x,self.y+4)
                else:
                    # wall jump
                    wall_dir = (self.is_solid(-3,0) and -1 or self.is_solid(3,0) and 1 or 0)
                    if wall_dir != 0:
                        psfx(2)
                        self.jbuffer = 0
                        self.spd.y = -2
                        self.spd.x = -wall_dir*(maxrun+1)
                        if not self.is_ice(wall_dir*3,0):
                            init_object(smoke,self.x+wall_dir*6,self.y)

            # dash
            d_full = 5
            d_half = d_full * 0.70710678118

            if self.djump > 0 and dash:
                init_object(smoke,self.x,self.y)
                self.djump -= 1
                self.dash_time = 4
                has_dashed = True
                self.dash_effect_time = 10
                v_input = (h.btn(k_up) and -1 or (h.btn(k_down) and 1 or 0))
                if input != 0:
                    if v_input != 0:
                        self.spd.x = input*d_half
                        self.spd.y = v_input*d_half
                    else:
                        self.spd.x = input*d_full
                        self.spd.y = 0
                elif v_input != 0:
                    self.spd.x = 0
                    self.spd.y = v_input * d_full
                else:
                    self.spd.x = (self.flip.x and -1 or 1)

                psfx(3)
                freeze = 2
                shake = 6
                self.dash_target.x = 2*sign(self.spd.x)
                self.dash_target.y = 2*sign(self.spd.y)
                self.dash_accel.x = 1.5
                self.dash_accel.y = 1.5

                if self.spd.y < 0:
                    self.dash_target.y *= 0.75

                if self.spd.y != 0:
                    self.dash_accel.x *= 0.70710678118

                if self.spd.x != 0:
                    self.dash_accel.y*=0.70710678118

                elif dash and self.djump <= 0:
                    psfx(9)
                    init_object(smoke,self.x,self.y)

            # animation
            self.spr_off += 0.25
            if not on_ground:
                if self.is_solid(input,0):
                    self.spr = 5
                else:
                    self.spr = 3
            elif h.btn(k_down):
                self.spr = 6
            elif h.btn(k_up):
                self.spr = 7
            elif (self.spd.x==0) or (not h.btn(k_left) and not h.btn(k_right)):
                self.spr = 1
            else:
                self.spr = 1+self.spr_off%4

            # next level
            if self.y < -4 and level_index() < 30:next_room()

            # was on the ground
            self.was_on_ground = on_ground


    def draw(self):

        # clamp in screen
        if self.x < -1 or self.x > 121:
            self.x = clamp(self.x,-1,121)
            self.spd.x = 0

        set_hair_color(self.djump)
        draw_hair(self,self.flip.x and -1 or 1)
        h.spr(
            self.spr,
            self.x,
            self.y,
            1,1,
            self.flip.x,self.flip.y
        )
        unset_hair_color()



# -----------------------------------------

def _update():
    global frames, seconds, minutes
    global music_timer, sfx_timer
    global freeze,shake
    global delay_restart,will_restart
    global start_game,start_game_flash

    frames = (frames+1)%30
    if frames == 0 and level_index() < 30:
        seconds = (seconds+1)%60
        if seconds == 0:
            minutes += 1

    if music_timer > 0:
        music_timer -= 1
        if music_timer <= 0:
            h.music(1,0)

    if sfx_timer > 0:
        sfx_timer -= 1

    # cancel if freeze
    if freeze > 0: freeze -= 1; return

    # screenshake
    if shake > 0:
        shake -= 1
        h.camera()
        if shake > 0:
            h.camera(-2+rnd(5),-2+rnd(5))

    # restart(soon)
    if will_restart and delay_restart>0:
        delay_restart -= 1
        if delay_restart<=0:
            will_restart = False
            load_room(room.x,room.y)

    # object the game objects
    for obj in objects:
        obj.move(obj.spd.x,obj.spd.y)
        if hasattr(obj._type,"update"):
            obj._type.update(obj)

    # start the game!
    if is_title():
        if (
            not start_game and
            (h.btn(k_jump) or h.btn(k_dash))
        ):
            h.music(-1)
            start_game_flash = 50
            start_game = True
            h.sfx(17)

        if start_game:
            start_game_flash -= 1
            if start_game_flash <= -30:
                begin_game()

def _draw():
    global freeze, start_game, start_game_flash
    global flash_bg,new_bg,frames
    if freeze>0:return
    h.cls(0)

    h.rpal()

    # start game flash
    if start_game:
        c = 10
        if start_game_flash > 10:
            if frames%10<5:
                c = 7
        elif start_game_flash > 5:
            c =2
        elif start_game_flash>0:
            c = 1
        else:
            c= 0

        #c += 1

        if c<10:
            h.pal(6,c)
            h.pal(12,c)
            h.pal(13,c)
            h.pal(5,c)
            h.pal(1,c)
            h.pal(7,c)

    # clear screen
    bg_col = 0
    if flash_bg:
        bg_col = frames//5
    elif new_bg != None:
        bg_col = 2
    h.rectfill(0,0,128,128,bg_col)

    # clouds
    if not is_title():
        for c in clouds:
            c.x += c.spd
            h.rectfill(c.x,c.y,c.x+c.w,c.y+4+(1-c.w/64)*12,new_bg != None and 14 or 1)
            if c.x <= -100:
                c.x = -c.w
                c.y = rnd(128-8)

    # draw bg terrain
    h.mapdraw(room.x * 16,room.y * 16,0,0,16,16,2)

    # platforms / big chest
    for o in objects:
        if o._type == platform or o._type == big_chest:
            draw_object(o)

    # draw terrain
    off = is_title() and -4 or 0
    h.mapdraw(room.x*16,room.y * 16, 0, 0,16,16,1)

    # draw objects
    for o in objects:
        if o._type != platform and o._type != big_chest:
            draw_object(o)

    # draw fg terrain
    h.mapdraw(room.x * 16,room.y * 16,0,0,16,16,7)

    # particles
    for p in particles:
        p.x += p.spd
        p.y -= sin(p.off)
        p.off += min(0.05,p.spd/32)
        h.rectfill(p.x,p.y,p.x+p.s,p.y+p.s,p.c)
        #h.circfill(p.x,p.y,2,p.c)
        if p.x > 128 or p.y < 0 or p.y > 128:
            p.x = rndrng(-20,-10)
            p.y = rnd(128)
            p.off = rnd(128)

    # dead particles
    for i,p in enumerate(dead_particles,start=0):
        p.x += p.spd.x
        p.y += p.spd.y
        p.t -= 1
        h.rectfill(
            p.x-p.t//5,
            p.y-p.t//5,
            p.x+p.t//5,
            p.y+p.t//5,
            14+p.t%2
        )
        if p.t <= 0:
            del dead_particles[i]

    # draw outside of the screen for screenshake
    h.rectfill(-5,-5,-1,133,0)
    h.rectfill(-5,-5,133,-1,0)
    h.rectfill(-5,128,133,133,0)
    h.rectfill(128,-5,133,133,0)

    # credits
    if is_title():
        h.hprint("x+c",58,80,5)
        h.hprint("matt thorson",42,96,5)
        h.hprint("noel berry",46,102,5)

    if level_index() == 30:
        p = None
        for i in range(1,count(objects)):
            if objects[i]._type == player:
                p = objects[i]
                break
        if p != None:
            diff = min(24,40-abs(p.x+4-64))
            h.rectfill(0,0,diff,128,0)
            h.rectfill(128-diff,0,128,128,0)

def draw_object(o):
    if hasattr(o._type,"draw"):
        o._type.draw(o)
    elif hasattr(o,"spr") and o.spr > 0:
        h.spr(o.spr,o.x,o.y,1,1,o.flip.x,o.flip.y)


# -----------------------------------------

tiles = {
  1: player_spawn,
  8: key,
  11: platform,
  12: platform,
  18: spring,
  20: chest,
  22: balloon,
  23: fall_floor,
  26: fruit,
  28: fly_fruit,
  64: fake_wall,
  #86: self.message,
  96: big_chest,
  118: flag
}

class Celeste(hagia.Cart):
    def __init__(self):
        super().__init__()
        self.c_name = "Celeste Classic"
        self.c_icon_img = "celeste.png"

    def init(self):
        global title_screen
        title_screen()

    def update(self):
        _update()

    def draw(self):
        #h.mapdraw(0,0,0,0,16,16)
        #h.camera(rnd(randrange(-5,5)),rnd(randrange(-5,5)))
        #bam = mid(6,3,12)
        #print(bam)

        _draw()

    @cached_property
    def gfx(self) -> str:
        return "gfx.data"

    @cached_property
    def sfx(self) -> list:
        return [
            "snd0.wav",
            "snd1.wav",
            "snd2.wav",
            "snd3.wav",
            "snd4.wav",
            "snd5.wav",
            "snd6.wav",
            "snd7.wav",
            "snd8.wav",
            "snd9.wav",
            "snd13.wav",
            "snd14.wav",
            "snd15.wav",
            "snd16.wav",
            "snd23.wav",
            "snd35.wav",
            "snd37.wav",
            "snd38.wav",
            "snd40.wav",
            "snd50.wav",
            "snd51.wav",
            "snd54.wav",
            "snd55.wav"
        ]

    @cached_property
    def music(self) -> list:
        return [
            "mus0.ogg",
            "mus10.ogg",
            "mus20.ogg",
            "mus30.ogg",
            "mus40.ogg"
        ]

    @cached_property
    def flags(self) -> str:
        return "flags.data"

    @cached_property
    def map(self) -> str:
        return "map.data"

h.load_cart(Celeste)
