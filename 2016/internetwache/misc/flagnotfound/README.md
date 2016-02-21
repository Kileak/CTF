# Internetwache 2016 - Misc - 404 Flag not found - 80 pts

> Description: I tried to download the flag, but somehow received only 404 errors :( Hint: The last step is to look for flag pattern.
>
> Attachment: [misc80.zip](misc80.zip)

# Write-up

The attachment contained a traffic capture with multiple DNS requests to the ctf site (with changing hexadecimal prefixes).

Obviously there's some information hidden in the dns queries. 

I used `chaosreader` to extract the requests and then wrote a script to extract the hex-strings and convert them into ascii.

```python
#!/usr/bin/python
import os
import re
import binascii

for fn in os.listdir('read'):
	with open(fn) as f:
		for line in f:
			if line.startswith("Host: "):
				print fn
				match = re.search('Host: (.*).2015.ctf.internetwache.org', line, re.S)

				s = str(match.group(1))
				print s.decode('hex')
```

Executing it made the requests more readable:

```
session_0002.http.html
In the end, it's all about fla
session_0004.http.html
gs.
Whether you win or lose do
session_0006.http.html
esn't matter.
{Ofc, winning is
session_0008.http.html
 cooler
Did you find other fla
session_0010.http.html
gs?
Noboby finds other flags!
session_0012.http.html
Superman is my hero.
_HERO!!!_
session_0014.http.html
Help me my friend, I'm lost i
session_0016.http.html
n my own mind.
Always, always,
session_0018.http.html
 for ever alone.
Crying until 
session_0020.http.html
I'm dying.
Kings never die.
So
session_0022.http.html
 do I.
}!

```

After stripping the filenames and formatting the text a little bit, we'll get:

```
In the end, it's all about flags.
Whether you win or lose doesn't matter.
{Ofc, winning is cooler
Did you find other flags?
Noboby finds other flags!
Superman is my hero.
_HERO!!!_
Help me my friend, I'm lost in my own mind.
Always, always, for ever alone.
Crying until I'm dying.
Kings never die. So do I.
}!
```

Taking only the first characters of each line reveals the flag:

`IW{DNS_HACK}`



