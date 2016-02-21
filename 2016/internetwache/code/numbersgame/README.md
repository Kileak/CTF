# IWCTF 2016 - Code - A numbers game - 50 pts

> Description: People either love or hate math. Do you love it? Prove it! You just need to solve a bunch of equations without a mistake.
>
> Service: 188.166.133.53:11027 

# Write-up

The service greets us with some equation to solve (Level 1). Surely this won't be the only one, so it would be tedious to solve them manually (and it wouldn't be in the coding section if it would be intended to do so ;))

So here's another quick&dirty ctf script:

```python
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
```

At least it does its job:

```shell
$ python solve.py 
Connect...
Hi, I heard that you're good in math. Prove it!

Received: Level 1.: x + 9 = 12

Level    : 1
Equation : x + 9 = 12

Result : |3|
Yay, that's right!

Received: Level 2.: x - 3 = 10

Level    : 2
Equation : x - 3 = 10

Result : |13|
Yay, that's right!

[SNIP]

Received: Level 100.: x - 1582 = -1251

Level    : 100
Equation : x - 1582 = -1251

Result : |331|
Yay, that's right!

Received: IW{M4TH_1S_34SY}
```

and rewards us with the next flag: `IW{M4TH_1S_34SY}`
