import os
import csv
import sys
import copy
import math
import time
import random
import pygame
import threading
import pandas as pd

os.environ['SDL_VIDEO_CENTERED'] = "True"

Version = '1.0'
Title = 'Natural Selection '+Version
screen_width = 1000
screen_height = 600
Fps = float("inf")

Human_friction = -0.7
Humans_def = 60
Foods_def = 60

Speed_def = 1.0
Speed_max = 2.0

Scale_def = 1.0
Scale_max = 3.0

Humans_scale = 70
Foods_scale = 2/5

simul_speed = 1
simul_data_save = False

vector = pygame.math.Vector2

def loadify(imgname):
	return pygame.image.load(imgname).convert_alpha()

class Human(pygame.sprite.Sprite):

	def __init__(self, game, x, y, speed):
		pygame.sprite.Sprite.__init__(self)
		self.game = game
		self.image = pygame.transform.scale(loadify('data/human.png'), (Humans_scale, Humans_scale))
		self.image.set_colorkey((0, 255, 0))
		self.mask = pygame.mask.from_surface(self.image)
		#self.image = pygame.Surface([70, 70])
		#self.image.fill(pygame.Color(0, 255, 0))
		#self.image.set_colorkey(pygame.Color(0, 255, 0))
		#pygame.draw.circle(self.image, pygame.Color(0, 162, 232), (35, 35), 35)
		self.rect = self.image.get_rect()
		self.rect.midbottom = (x, y)
		self.speed = speed
		self.reach_wall = False
		self.get_food = 0
		self.energy = 200
		self.defcolor = pygame.Color(0, 162, 232)
		self.wall_hover = False
		self.dupli_hover = False

		if not speed == Speed_def:
			speed_color = (speed-Speed_def)
			r = 0+speed_color*random.randrange(39,61)
			g = 162+speed_color*random.randrange(39,61)
			b = 232+speed_color*random.randrange(39,61)
			if r > 255:
				r = 255
			if g > 255:
				g = 255
			if b > 255:
				b = 255
			if r < 0:
				r = 0
			if g < 0:
				g = 162
			if b < 0:
				b = 232
			#print(str(int(r))+", "+str(int(g))+", "+str(int(b)))
			self.defcolor = pygame.Color(int(r), int(g), int(b))
			self.fill(self.image, self.defcolor)

		self.pos = vector(x, y)
		self.vel = vector(0, 0)
		self.acc = vector(0, 0)
		rel_x, rel_y = self.game.screen.get_size()[0]/2 - x, self.game.screen.get_size()[1]/2 - y
		self.current_angle = math.degrees(math.atan2(rel_y, rel_x)) + random.uniform(-15, 15)

	def see_center(self):
		rel_x, rel_y = self.game.screen.get_size()[0]/2 - self.pos.x, self.game.screen.get_size()[1]/2 - self.pos.y
		self.current_angle = math.degrees(math.atan2(rel_y, rel_x))

	def fill(self, surface, color):
		from_color = surface.get_at((35, 35))
		target_color = color
		pygame.transform.threshold(surface,surface,from_color,(0,255,0,0),target_color,1,None,True)
		#pix_array = pygame.PixelArray(surface)
		#pix_array.replace(from_color, target_color)

	def update(self):
		self.acc.x = math.cos(math.radians(self.current_angle)) * self.speed * self.game.dt
		self.acc.y = math.sin(math.radians(self.current_angle)) * self.speed * self.game.dt
		self.current_angle = random.uniform(-10, 10) + self.current_angle

		self.acc += self.vel * Human_friction
		self.vel += self.acc

		if abs(self.vel.x) < 0.1:
			self.vel.x = 0
		if abs(self.vel.y) < 0.1:
			self.vel.y = 0

		#          Y 0
		#
		#
		#
		# X 0                  X self.screen.get_size()[0]
		#
		#
		#
		#          Y self.screen.get_size()[1]
		adding = self.vel + 0.5*self.acc
		self.pos += adding
		if not self.reach_wall:
			self.energy -= abs(((adding[0]**2)+(adding[1]**2))/20*self.speed)/self.game.dt
			#if self.speed > 1:
			print(self.energy)
		if ((self.pos.x < (Humans_scale/2)) or (self.pos.x > self.game.screen.get_size()[0]-(Humans_scale/2)) or (self.pos.y < Humans_scale) or (self.pos.y > self.game.screen.get_size()[1])):
			if self.get_food == 0:
				self.kill()
			else:
				self.reach_wall = True
		self.rect.midbottom = self.pos

		gfoods = pygame.sprite.spritecollide(self, self.game.foods, False, pygame.sprite.collide_mask)
		if gfoods:
			if self.get_food < 2:
				self.get_food += 1
				#self.energy += 500
				#self.fill(self.image, pygame.Color(0, 150, 200))
				gfoods[0].kill()

class Food(pygame.sprite.Sprite):

	def __init__(self, game, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.transform.scale(loadify('data/food.png'), (math.floor(39*Foods_scale), math.floor(49*Foods_scale)))
		self.image.set_colorkey((0, 255, 0))
		self.mask = pygame.mask.from_surface(self.image)
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y

class Simulation:

	def __init__(self):
		pygame.init()
		icon = pygame.image.load('data/icon.png')
		pygame.display.set_icon(icon)
		flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
		self.screen = pygame.display.set_mode((screen_width, screen_height), flags, vsync=1)
		pygame.display.set_caption(Title)
		self.clock = pygame.time.Clock()
		self.running = True
		if simul_data_save:
			self.will_save = {"energy-die-speed": [], "humans": 0, "speed": []}
			self.data = {"energy-die-speed": [], "humans": [], "speed": []}
		self.dt = 0
		self.generation = 1
		self.genchange = 0

	def data_save(self):
		self.data["energy-die-speed"].append(self.will_save["energy-die-speed"])
		self.data["humans"].append(self.will_save["humans"])
		self.data["speed"].append(self.will_save["speed"])
		pd.DataFrame(self.data).to_csv('NSdata.csv')
		self.will_save = {"energy-die-speed": [], "humans": 0, "speed": []}

	def add_human(self, speed):
		if random.randrange(0, 2) == 0:
			x = random.choice([Humans_scale, self.screen.get_size()[0]-Humans_scale])
			y = random.randrange(Humans_scale+(Humans_scale/2), self.screen.get_size()[1]-(Humans_scale/2))
		else:
			x = random.randrange(Humans_scale, self.screen.get_size()[0]-Humans_scale)
			y = random.choice([Humans_scale+(Humans_scale/2), self.screen.get_size()[1]-(Humans_scale/2)])
		hu = Human(self, x, y, speed)
		self.humans.add(hu)
		self.all_sprites.add(hu)

	def add_food(self):
		x = random.randrange(150, self.screen.get_size()[0]-150)
		y = random.randrange(150, self.screen.get_size()[1]-150)
		fu = Food(self, x, y)
		self.foods.add(fu)
		self.all_sprites.add(fu)

	def new(self):
		self.all_sprites = pygame.sprite.Group()
		self.humans = pygame.sprite.Group()
		self.foods = pygame.sprite.Group()

		for x in range(Humans_def):
			self.add_human(Speed_def)

		for x in range(Foods_def):
			self.add_food()

		self.run()

	def run(self):
		self.playing = True
		while self.playing:
			self.dt = (self.clock.tick(Fps)/15)*simul_speed
			self.events()
			up_t = threading.Thread(target=self.update)
			up_t.start()
			up_t.join()
			dr_t = threading.Thread(target=self.draw)
			dr_t.start()
			dr_t.join()
			#self.update()
			#self.draw()

	def update(self):
		if (pygame.time.get_ticks() <= 2200) or (self.genchange > pygame.time.get_ticks()):
			return

		no_food_human = True
		for human in self.humans:
			if human.reach_wall == False:
				no_food_human = False
				break

		#if pygame.time.get_ticks() >= self.generation*60000/simul_speed:
		#	for food in self.foods:
		#		food.kill()

		#print(str(len(self.foods.sprites())) + ", " + str(no_food_human))
		if (len(self.foods.sprites()) == 0) or no_food_human:
			self.genchange = float("inf")
			if simul_data_save:
				self.data_save()
			for food in self.foods:
				food.kill()
			nowhumans = copy.copy(self.humans)
			for human in nowhumans:
				if (human.get_food == 0) or (human.reach_wall == False):
					human.kill()
				else:
					if (human.reach_wall == True) and (human.get_food == 2):
						if random.randrange(0, 5) == 0:
							speed = human.speed + random.uniform(-0.5, 0.5)
							if speed >  Speed_max:
								speed = Speed_max
							if speed < 0:
								speed = 0
							self.add_human(speed)
						else:
							self.add_human(human.speed)
					self.add_human(human.speed)
					human.kill()
			if simul_data_save:
				for human in self.humans:
					self.will_save["speed"].append(human.speed)
			if (len(self.humans.sprites()) == 0):
				for x in range(Humans_def):
					self.add_human(Speed_def)
			for x in range(Foods_def):
				self.add_food()
			if simul_data_save:
				self.will_save["humans"] = len(self.humans.sprites())
			self.generation += 1
			pygame.display.flip()
			self.genchange = pygame.time.get_ticks()+round(1000/simul_speed)
		else:
			for human in self.humans:
				if human.reach_wall == False:
					human.update()
					if human.energy <= 0:
						if simul_data_save:
							self.will_save["energy-die-speed"].append(human.speed)
						human.kill()
				else:
					if human.get_food == 0:
						human.kill()
					if human.energy <= 0:
						if simul_data_save:
							self.will_save["energy-die-speed"].append(human.speed)
						human.kill()
					if human.wall_hover:
						human.fill(human.image, human.defcolor)
						human.wall_hover = False

	def events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				if self.playing:
					self.playing = False
				self.running = False

	def draw(self):
		self.screen.fill((170, 170, 170))
		self.all_sprites.draw(self.screen)
		no_food_humans = 0
		dupli = 0
		for human in self.humans:
			if human.reach_wall == False:
				no_food_humans += 1
			if (human.get_food == 2) and (human.reach_wall == True):
				dupli += 1
		self.draw_text('현재 개체수 : '+str(len(self.humans.sprites()))+'개', 22, (0, 0, 0), self.screen.get_size()[0]/2, 15)
		self.draw_text('현재 먹이 수 : '+str(len(self.foods.sprites()))+'개', 22, (0, 0, 0), self.screen.get_size()[0]/2, 40)
		norw = self.draw_text('벽에 도달하지 못한 개체수 : '+str(no_food_humans)+'개', 22, (0, 0, 0), self.screen.get_size()[0]/2, 65)
		if norw.collidepoint(pygame.mouse.get_pos()):
			for hu in self.humans:
				if (hu.wall_hover == False) and (hu.reach_wall == False):
					hu.fill(hu.image, pygame.Color(255, 100, 100))
					hu.wall_hover = True
		else:
			for hu in self.humans:
				if hu.wall_hover and (hu.reach_wall == False):
					hu.fill(hu.image, hu.defcolor)
					hu.wall_hover = False

		duplica = self.draw_text('복제할 개체수 : '+str(dupli)+'개', 22, (0, 0, 0), self.screen.get_size()[0]/2, 90)
		if duplica.collidepoint(pygame.mouse.get_pos()):
			for hu in self.humans:
				if (hu.dupli_hover == False) and (hu.reach_wall == True) and (hu.get_food == 2):
					hu.fill(hu.image, pygame.Color(255, 100, 100))
					hu.dupli_hover = True
		else:
			for hu in self.humans:
				if hu.dupli_hover and (hu.reach_wall == True) and (hu.get_food == 2):
					hu.fill(hu.image, hu.defcolor)
					hu.dupli_hover = False
		avg = 0
		low = float("inf")
		high = float("-inf")
		for human in self.humans:
			avg += human.speed
			if human.speed < low:
				low = human.speed
			if human.speed > high:
				high = human.speed
		if len(self.humans.sprites()) != 0:
			avg = str(round(avg/len(self.humans.sprites()), 1))
		else:
			avg = "None"
		self.draw_text('속도(평균/최고/최소) : '+avg+'/'+str(round(high, 1))+'/'+str(round(low, 1)), 22, (0, 0, 0), 200, self.screen.get_size()[1]-50)

		self.draw_text('세대 : '+str(self.generation), 22, (77, 77, 255), self.screen.get_size()[0]-100, 15)
		fps = self.clock.get_fps()
		self.draw_text('FPS : '+str(round(fps, 1)), 22, (0, 255, 0), 100, 10)
		if pygame.time.get_ticks() <= 2000:
			self.draw_text('로딩중...', 200, (0, 0, 0), self.screen.get_size()[0]/2, self.screen.get_size()[1]/2-150)
		if self.genchange > pygame.time.get_ticks():
			self.draw_text('세대 변화', 200, (255, 77, 80), self.screen.get_size()[0]/2, self.screen.get_size()[1]/2-150)
		pygame.display.flip()

	def draw_text(self, text, size, color, x, y):
		font = pygame.font.Font(pygame.font.match_font('malgungothic'), size)
		text_surface = font.render(text, True, color)
		text_rect = text_surface.get_rect()
		text_rect.midtop = (x, y)
		self.screen.blit(text_surface, text_rect)
		return text_rect

if __name__ == '__main__':

	try:
		os.chdir(sys._MEIPASS)
	except:
		os.chdir(os.getcwd())

	simul = Simulation()
	while simul.running:
		simul.new()
	pygame.quit()
	sys.exit()