#!/usr/bin/python
from socket import *
import re

s = None

BANNER = "Hi, I heard that you're good in math. Prove it!\n"
YAY = "Yay, that's right!\n"

# solve the equation (taken from http://code.activestate.com/recipes/365013-linear-equations-solver-in-3-lines/)
def solve(eq,var='x'):
	eq1 = eq.replace("=","-(")+")"
	c = eval(eq1,{var:1j})
	return -c.real/c.imag

# connect to the service and fetch the banner
def connect():
	global s
	print "Connect..."
	s = socket(AF_INET, SOCK_STREAM)
	s.connect(("188.166.133.53",11027))
	res = s.recv(len(BANNER))
	print res

# grab the equation from received string
def geteq(msg):
	match = re.search('Level (.*).: (.*)', msg, re.S)

	print "Level    : %s" % match.group(1)
	print "Equation : %s" % match.group(2)

	return match.group(2)
	
# receive equation and send answer back to the service
def solvequestion():
	msg = s.recv(1024)
	print "Received: %s" % msg
	eq = geteq(msg)

	res = solve(eq)
	print "Result : |%s|" % str(int(res))
	
	s.send(str(int(res)))
	res =s.recv(len(YAY))
	print res

connect()

while True:
	solvequestion()
