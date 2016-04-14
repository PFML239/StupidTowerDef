import pyglet
from pyglet.gl import *
from functools import partial
from cocos import scene
from cocos import sprite
from cocos import layer
from cocos import text
from itertools import product
from cocos.collision_model import CircleShape
from cocos.director import director
from cocos.actions.interval_actions import MoveTo
from cocos.actions.interval_actions import FadeIn
from cocos.actions.interval_actions import FadeOut
from cocos.actions.interval_actions import MoveBy
from cocos.actions.interval_actions import Delay
from cocos.actions.interval_actions import Speed
from cocos.actions.interval_actions import RotateBy
from cocos.actions.base_actions import Repeat
from cocos.actions.instant_actions import CallFunc
from cocos.layer.util_layers import ColorLayer
from cocos.scenes.transitions import JumpZoomTransition
from pyglet.window.mouse import LEFT, RIGHT
from cocos.collision_model import CollisionManager
import cocos.euclid as eu

path = [ (-64, 487),
         (257, 457), 
         (503, 391),
         (431, 310),
         (266, 239),
         (473, 90), 
         (800, 85),
         ]
path = [ (x,600-y) for x,y in path]
         
enemy_action = MoveTo(path[1])
for x in path[2:]:         
    enemy_action = enemy_action + MoveTo(x) 

enemy_img = pyglet.resource.image('enemy.png')

class Enemy(sprite.Sprite):
    def __init__(self, delay, death_callback,speed):
        super().__init__('enemy.png', path[0])
        self.do(Speed(delay + enemy_action + CallFunc(partial(death_callback, self)), speed))        
        x,y = path[0]
        self.cshape = CircleShape(eu.Vector2(x,y), 32)

class Tower(sprite.Sprite):
    def __init__(self,x,y):
        super().__init__("tower.png",(x,y))
    def shoot(self, x,y):
        return Bullet(self.x, self.y, x, y)
        
class Bullet(sprite.Sprite):
    def __init__(self,x,y,x1,y1):
        super().__init__("tower.png",(x,y), scale=0.1, color=(255,0,0))
        self.cshape = CircleShape(eu.Vector2(x,y), 3)
        a = ((x-x1)**2 + (y-y1)**2)**0.5
        speed = 1500
        x1, y1 = (x1-x)/a*speed, (y1-y)/a*speed
        self.do(Repeat(RotateBy(360, 0.5)) | Repeat(MoveBy((x1,y1))))

class Splat(sprite.Sprite):
    def __init__(self, ):
        x, y = director.get_window_size()
        super().__init__("splat.png",(x/2,y/2))
        self.do(FadeIn(0.2) + FadeOut(3) + CallFunc(self.kill))
        
        
        
class Background(layer.Layer):
    def __init__(self):
        super().__init__()
        self.img = pyglet.resource.image('bg.png')
    
    def draw( self ):
        glPushMatrix()
        self.transform()
        self.img.blit(0,0)
        glPopMatrix()
        
class MainScene(scene.Scene):
    def __init__(self):
        super().__init__()
        self.add(Background(), z=-1)
        self.add(MainLayer())
        
class MainLayer(layer.Layer):
    is_event_handler = True
    def __init__(self):
        super().__init__()
        self.lives = 5
        self.money = 25
        self.towers = []
        self.bullets = []
        self.enemies = []
        self.wave_number = 0
        self.speed = 2.0
        self.new_wave()
        self.add(text.Label("Lives: " + str(self.lives), (0, 600-52),font_size=42, color=(255,255,0,255)),name="lives")
        self.add(text.Label("Money: " + str(self.money), (0, 600-104),font_size=42, color=(255,255,0,255)), name="money")
        self.do(Repeat(Delay(0.01) + CallFunc(self.update)))
        
        
    def new_wave(self):
        self.money += 50
        self.wave_number += 1
        for i in range(5):
            e = Enemy(Delay(i*3), self.enemy_dies, self.speed)
            self.add(e)
            self.enemies.append(e)
        self.speed *=1.5
    
    def update(self):
        self.get("lives").element.text = "Lives: " + str(self.lives)
        self.get("money").element.text = "Money: " + str(self.money)
        remove_bullet = set()
        remove_enemy = set()
        for b in self.bullets:
            if b.position[0] < 0 or b.position[0] >= 800 or \
                b.position[1] < 0 or b.position[1] >= 600:
                remove_bullet.add(b)
            b.cshape.center = eu.Vector2(b.position[0],b.position[1])
        for e in self.enemies:
            e.cshape.center = eu.Vector2(e.position[0],e.position[1])
        for a,b in product(self.bullets, self.enemies):
            if a.cshape.overlaps(b.cshape):
                self.money += 5
                remove_bullet.add(a)
                remove_enemy.add(b)
        for item in remove_bullet:
            self.remove(item)
            self.bullets.remove(item)
        for item in remove_enemy:
            self.remove(item)
            self.enemies.remove(item)
        if len(self.enemies)==0:
            self.new_wave()
        
    def enemy_dies(self, enemy):
        self.add(Splat())
        self.remove(enemy)
        self.enemies.remove(enemy)
        self.lives -= 1
        if self.lives <= 0:
            director.replace(JumpZoomTransition(GameOver(), 2.0))
            
    def on_mouse_press(self, x, y, buttons, modifiers):
        x, y = director.get_virtual_coordinates(x, y)
        if buttons & LEFT and self.money>=75:
            self.money -= 75
            t = Tower(x,y)
            self.towers.append(t)
            self.add(t)
        if buttons & RIGHT :
            for t in self.towers:
                b = t.shoot(x,y)
                self.bullets.append(b)
                self.add(b)
                
class GameOver(scene.Scene):
    def __init__(self):
        super().__init__()
        x, y = director.get_window_size()
        title = text.Label("GAME OVER", (x/2, y/2), anchor_x="center", \
                           anchor_y="center", font_size=52, color=(255,255,0,255))
        clayer = ColorLayer(0, 128, 128, 128)
        clayer.add(title)
        self.add(clayer)
        
def main():
    director.init(width=800, height=600, autoscale=True)
    director.run(MainScene())

       
if __name__ == "__main__":
    main()