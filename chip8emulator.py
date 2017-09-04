import sys
import random
import time
import pygame
pygame.init()

class Screen:
	def __init__(self, color, width, height, scalingFactor):
		self.color = color
		self.width = width
		self.height = height
		self.data = [[0]*width for y in range(height)]
		self.scalingFactor = scalingFactor

	def drawImage(self, x, y, rawopcode):
		mainSurface = pygame.display.set_mode((self.width * self.scalingFactor,self.height * self.scalingFactor))
		imageLength = 8 #chip8 pixel length is fixed at 8 pixels
		imageHeight = (rawopcode & 0x000f) & 0xffff #chip8 pixel height can range from 1 to 15 pixels
		mainImage = pygame.draw.rect(mainSurface, self.color, (x * self.scalingFactor, y * self.scalingFactor, imageLength * self.scalingFactor, imageHeight * self.scalingFactor))

		for i in range(0, len(self.data)):
			for z in range (0, len(self.data[i])):
				if self.data[i][z] == 1:
					mainImage
		pygame.display.flip()
		
	def setCoordinate(self, x, y, draw):
		self.data[y][x] = draw

	def getCoordinate(self, x, y):
		return self.data[y][x]
  
class Emulator:
	def __init__(self):
		self.keyinput = [0]*16 #keyboard input 16-button keyboard
		self.display = Screen((255,255,255),64,32, 20)
		self.memory = [0]*4096 #memory of interpreter, fonts and rom details
		self.stack = [0]*16
		self.stackpointer = 0
		self.soundtimer = 0
		self.delaytimer = 0
		self.programcounter = 0x200
		self.v = [0]*16
		self.i = 0

	def load_rom(self):
		loadedrom = open("TANK", "rb").read() #take in input from rom
		
		i = 0
		while i < len(loadedrom):
			self.memory[0x200 + i] = loadedrom[i] #put rom input into memory
			i += 1

	def _0NNN(self, rawopcode): #used to correctly identify which 0 opcode is being used
		decodedopcode = (rawopcode & 0xf0ff)
		if decodedopcode == 0x00e0:
			self._00E0()

		elif decodedopcode == 0x00ee:
			self._00EE()

		else:
			print("Unknown _0NNN instruction " + hex(rawopcode))

	def _00E0(self): #Clears the screen
		self.display = [0]*64*32
		self.programcounter += 2

	def _00EE(self): #Returns from a subroutine
		self.programcounter = self.stack[self.stackpointer]
		self.stackpointer -= 1
		self.programcounter += 2

	def _1NNN(self, rawopcode): #Jumps to the address NNN
		self.programcounter = (rawopcode & 0x0fff)

	def _2NNN(self, rawopcode):
		self.stackpointer += 1
		self.stack[self.stackpointer] = self.programcounter
		self.programcounter = (rawopcode & 0x0fff)

	def _3XKK(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		if self.v[source] == (rawopcode & 0x00ff):
			self.programcounter += 4
		else:
			self.programcounter += 2

	def _4XKK(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		if self.v[source] != (rawopcode & 0x00ff):
			self.programcounter += 4
		else:
			self.programcounter += 2

	def _5XY0(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		target = (rawopcode & 0x00f0) >> 4
		if self.v[source] == self.v[target]:
			self.programcounter += 4
		else:
			self.programcounter += 2

	def _6XKK(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		self.v[target] = (rawopcode & 0x00ff)
		self.programcounter += 2

	def _7XKK(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		self.v[target] = (self.v[target] + (rawopcode & 0x00ff)) & 0xff
		self.programcounter += 2

	def _8XYN(self, rawopcode): #used to correctly identify which 8 opcode is being used
		decodedopcode = (rawopcode & 0xf00f)
		if decodedopcode == 0x8000:
			self._8XY0(rawopcode)

		elif decodedopcode == 0x8001:
			self._8XY1(rawopcode)

		elif decodedopcode == 0x8002:
			self._8XY2(rawopcode)

		elif decodedopcode == 0x8003:
			self._8XY3(rawopcode)

		elif decodedopcode == 0x8004:
			self._8XY4(rawopcode)

		elif decodedopcode == 0x8005:
			self._8XY5(rawopcode)

		elif decodedopcode == 0x8006:
			self._8XY6(rawopcode)

		elif decodedopcode == 0x8007:
			self._8XY7(rawopcode)

		elif decodedopcode == 0x800e:
			self._8XYE(rawopcode)

		else:
			print("Unknown _8XYN instruction " + hex(rawopcode))

	def _8XY0(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		source = (rawopcode & 0x00f0) >> 4
		self.v[target] = self.v[source]
		self.programcounter += 2

	def _8XY1(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		source = (rawopcode & 0x00f0) >> 4
		self.v[target] = self.v[target] | self.v[source]
		self.programcounter += 2

	def _8XY2(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		source = (rawopcode & 0x00f0) >> 4
		self.v[target] = self.v[target] & self.v[source]
		self.programcounter += 2

	def _8XY3(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		source = (rawopcode & 0x00f0) >> 4
		self.v[target] = self.v[target] ^ self.v[source]
		self.programcounter += 2

	def _8XY4(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		source = (rawopcode & 0x00f0) >> 4
		temporary = self.v[target] + self.v[source]
		if temporary > 255:
			self.v[0xf] = 1
		else:
			self.v[0xf] = 0
		self.v[target] = (self.v[target] + self.v[source]) & 0xff
		self.programcounter += 2

	def _8XY5(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		source = (rawopcode & 0x00f0) >> 4
		targetRegister = self.v[target]
		sourceRegister = self.v[source]
		if targetRegister > sourceRegister:
			self.v[0xf] = 1
		else:
			self.v[0xf] = 0
		self.v[target] = (self.v[target] - self.v[source]) & 0xff
		self.programcounter += 2

	def _8XY6(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		leastSignificantBit = self.v[source] & 1
		self.v[0xf] = leastSignificantBit
		self.v[source] = (self.v[source]/2)
		self.programcounter += 2

	def _8XY7(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		source = (rawopcode & 0x00f0) >> 4
		targetRegister = self.v[target]
		sourceRegister = self.v[source]
		if sourceRegister > targetRegister:
			self.v[0xf] = 1
		else:
			self.v[0xf] = 0
		self.v[target] = (self.v[source] - self.v[target]) & 0xff

	def _8XYE(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		mostSignificantBit = self.v[source] >> 7
		self.v[0xf] = mostSignificantBit
		self.v[source] = (self.v[source]*2)
		self.programcounter += 2


	def _9XY0(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		target = (rawopcode & 0x00f0) >> 4

		if self.v[source] != self.v[target]:
			self.programcounter += 4
		else:
			self.programcounter += 2

	def _ANNN(self, rawopcode):
		self.i = (rawopcode & 0x0fff)
		self.programcounter += 2

	def _DXYN(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		target = (rawopcode & 0x00f0) >> 4
		height = (rawopcode & 0x000f)
		xcoordinate = (self.v[source] % 65)
		ycoordinate = (self.v[target] % 33)
		self.v[0xf] = 0
		for yoffset in range(0, height):
			sprite = self.memory[yoffset + self.i]
			for xoffset in range(0, 8):
				if (sprite & (0x80 >> xoffset)) is not 0:
					xpixelpos = xcoordinate + xoffset
					ypixelpos = (ycoordinate + yoffset)
					bitfromscreen = self.display.getCoordinate(xpixelpos, ypixelpos)
					if bitfromscreen == 1:
						self.v[0xf] = 1
					self.display.setCoordinate(xpixelpos, ypixelpos, bitfromscreen ^ 1)
					self.display.drawImage(xcoordinate, ycoordinate, rawopcode)
		self.programcounter += 2

	def _CXKK(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		self.v[target] = ((random.randint(0,255)) & (rawopcode & 0x00ff))
		self.programcounter += 2

	def _F000(self, rawopcode):

		decodedopcode = (rawopcode & 0xf0ff)
		if decodedopcode == 0xf01e:
			self._FX1E(rawopcode)

		elif decodedopcode == 0xf015:
			self._FX15(rawopcode)

		elif decodedopcode == 0xf007:
			self._FX07(rawopcode)

		elif decodedopcode == 0xf055:
			self._FX55(rawopcode)

		elif decodedopcode == 0xf033:
			self._FX33(rawopcode)

		elif decodedopcode == 0xf065:
			self._FX65(rawopcode)

		elif decodedopcode == 0xf029:
			self._FX29(rawopcode)

		elif decodedopcode == 0xf018:
			self._FX18(rawopcode)

		elif decodedopcode == 0xf00a:
			self._FX0A(rawopcode)

		else:
			print("Unknown _F000 instruction " + hex(rawopcode))

	def _FX1E(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		sourceRegister = self.v[source]
		if (sourceRegister + self.i) > 0xfff:
			self.v[0xf] = 1
		else:
			self.v[0xf] = 0
		self.i = (self.i + self.v[source]) & 0xffff
		self.programcounter += 2

	def _FX15(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		self.delaytimer = self.v[source]
		self.programcounter += 2

	def _FX07(self, rawopcode):
		target = (rawopcode & 0x0f00) >> 8
		self.v[target] = self.delaytimer
		self.programcounter += 2

	def _FX55(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		for x in range(0, source):
			self.memory[self.i + x] = self.v[x]
		self.programcounter += 2

	def _FX33(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		vxdecimal = self.v[source]
		self.memory[self.i] = int(vxdecimal/100)
		self.memory[self.i + 1] = int((vxdecimal/10) % 10)
		self.memory[self.i + 2] = int((vxdecimal%100) % 10)
		self.programcounter += 2

	def _FX65(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		for x in range(0, source):
			self.v[x] = self.memory[self.i + x]
		self.programcounter += 2

	def _FX29(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		self.i = self.v[source] * 5
		self.programcounter += 2

	def _FX18(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		self.soundtimer = self.v[source]
		self.programcounter += 2

	def _E000(self, rawopcode):
		decodedopcode = (rawopcode & 0xf0ff)
		if decodedopcode == 0xe0a1:
			self._EXA1(rawopcode)
		elif decodedopcode == 0xe09e:
			self._EX9E(rawopcode)

		else:
			print("Unknown _E000 instruction " + hex(rawopcode))

	def _EXA1(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		if self.keyinput[self.v[source]] is 0:
			self.programcounter += 4
		else:
			self.programcounter += 2

	def _EX9E(self, rawopcode):
		source = (rawopcode & 0x0f00) >> 8
		if self.keyinput[self.v[source]] is not 0:
			self.programcounter += 4
		else:
			self.programcounter += 2

	def run_opcode(self, rawopcode):
		decodedopcode = (rawopcode & 0xf000)

		if decodedopcode == 0x0000:
			self._0NNN(rawopcode)

		elif decodedopcode == 0x1000:
			self._1NNN(rawopcode)

		elif decodedopcode == 0x2000:
			self._2NNN(rawopcode)

		elif decodedopcode == 0x3000:
			self._3XKK(rawopcode)

		elif decodedopcode == 0x4000:
			self._4XKK(rawopcode)

		elif decodedopcode == 0x5000:
			self._5XYO(rawopcode)

		elif decodedopcode == 0x6000:
			self._6XKK(rawopcode)

		elif decodedopcode == 0x7000:
			self._7XKK(rawopcode)

		elif decodedopcode == 0x8000:
			self._8XYN(rawopcode)

		elif decodedopcode == 0x9000:
			self._9XY0(rawopcode)

		elif decodedopcode == 0xa000:
			self._ANNN(rawopcode)

		elif decodedopcode == 0xd000:
			self._DXYN(rawopcode)

		elif decodedopcode == 0xc000:
			self._CXKK(rawopcode)

		elif decodedopcode == 0xf000:
			self._F000(rawopcode)

		elif decodedopcode == 0xe000:
			self._E000(rawopcode)

		else:
			raise Exception("Unknown Opcode: " + hex(rawopcode))

	def emulation_loop(self):
		exit = False
		while exit is False:
			rawopcode = (self.memory[self.programcounter] << 8) | self.memory[self.programcounter + 1] # check opcode against programcounter
			self.print_emulation_loop(rawopcode)
			self.run_opcode(rawopcode)
			if self.delaytimer > 0:
				self.delaytimer = self.delaytimer - 1
				time.sleep(1/60)

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					exit = True

	def print_emulation_loop(self, rawopcode):
		print(" PC: " + str(hex(self.programcounter)) + " stack: " + str(self.stack) + " i: " + str(hex(self.i)) + " registers:" + str(self.v) + " delaytimer: " + str(self.delaytimer) + " Vf: " + str(self.v[0xf]) + " rawopcode: " + str(hex(rawopcode)))



runemulator = Emulator()
runemulator.load_rom()
runemulator.emulation_loop()
pygame.quit()