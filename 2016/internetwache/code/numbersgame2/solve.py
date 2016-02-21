#!/usr/bin/python
import sys
from socket import *
import re

BANNER = "Hi, I like math and cryptography. Can you talk to me?!\n"
YAY = "Yay, that's right!\n"

class Encoder:
	def decode(self, eq):
		result = ""

		parts = eq.split('.')
		out = ""
		for part in parts:
			q = bin(int(part)-3).lstrip("0b")
			q = q.zfill(2)
			out += q

		for i in range(0, len(out),8):
			test = "0b"+out[i:i+8]
			result += chr(self._xor(int(test,2),32))

		return result
			
	def encode(self, eq):
        	out = []
        	for c in eq:
            		q = bin(self._xor(ord(c),32)).lstrip("0b")
            		q = "0" * ((8)-len(q)) + q
            		out.append(q)
        	b = ''.join(out)
        	pr = []
        	for x in range(0,len(b),2):
            		c = chr(int(b[x:x+2],2)+51)
            		pr.append(c)
        	s = '.'.join(pr)
        	return s

	def _xor(self,a,b):
		return a ^ b


s = None
c = Encoder()

def connect():
	global s
	s = socket(AF_INET, SOCK_STREAM)
	s.connect(("188.166.133.53", 11071))
	res = s.recv(len(BANNER))
	print res

def solveeq(eq,var='x'):
	eq1 = eq.replace("=","-(")+")"
	c = eval(eq1,{var:1j})
	return -c.real/c.imag

def solve():
	global s,c

	quest = s.recv(1024)
	print quest
	match = re.search("Level (.*).: (.*)", quest, re.S)
	
	print "Level    : %s" % match.group(1)
	print "Question : %s" % match.group(2)

	eq = c.decode(match.group(2))
	res = solveeq(eq)
	print "Result   : %s" % str(int(res))
	enc = c.encode(str(int(res)))
	s.send(enc)
	res = s.recv(len(YAY))
	print "Response : %s" % res	

connect()

while True:
	solve()
