# Internetwache 2016 - Code - A numbers game II - 70 pts

> Description: Math is used in cryptography, but someone got this wrong. Can you still solve the equations? Hint: You need to encode your answers.
>
> Attachment: [code70.zip](code70.zip)
>
> Service: 188.166.133.53:11071 

# Write-up

Another equation solver challenge, but this time the service has some cryptic output:

```shell
$ nc 188.166.133.53 11071
Hi, I like math and cryptography. Can you talk to me?!
Level 1.: 4.4.5.3.3.3.3.3.3.3.5.6.3.3.3.3.3.4.3.4.3.4.4.4.3.3.3.3.3.4.6.4.3.3.3.3.3.4.3.6.3.4.4.3
```

A look at the README.txt in the attachment reveals the encoding method of the service:

```python
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
```

The first loop takes every char of the equation, xor's it with 32, converts it to binary representation and appends it to a resulting string.

The next loop then takes every 2 bits from the result, converts it back to an integer, adds 51 to it and converts it back to a character. 
Since 51 is the ascii value of '3', this will result in possible values '3', '4', '5' and '6'. Those values will then be concatenated again with a '.' as delimeter.

Well, that explains the numbers in the equation and luckily can easily be reversed:

```python
def decode(self, eq):
	result = ""

	# split all numbers by '.'
	parts = eq.split('.')
	out = ""

	for part in parts:
		# convert back to binary representation (2 bits)
		q = bin(int(part)-3).lstrip("0b")
		q = q.zfill(2)		# fill up, for 00 and 01
		out += q

	# take every 8 bits in the string, convert them back to int, xor with 32 and back to char
	for i in range(0, len(out),8):
		test = "0b"+out[i:i+8]
		result += chr(self._xor(int(test,2),32))

	return result
```

Applying this decode method to the service message results in an equation again:

`x + 15 = 34`

So, we can reuse the code from numbers game to solve the equation and send the result back to the server (since the server likes cryptography so much, we'll have to encode the response also first).

```shell
$ python solve.py 
Hi, I like math and cryptography. Can you talk to me?!

Level 1.: 4.4.5.3.3.3.3.3.3.3.6.4.3.3.3.3.3.4.3.4.3.4.4.6.3.3.3.3.3.4.6.4.3.3.3.3.3.3.6.4.3.4.4.3

Level    : 1
Question : 4.4.5.3.3.3.3.3.3.3.6.4.3.3.3.3.3.4.3.4.3.4.4.6.3.3.3.3.3.4.6.4.3.3.3.3.3.3.6.4.3.4.4.3

Result   : 13
Response : Yay, that's right!

Level 2.: 4.4.5.3.3.3.3.3.3.3.6.4.3.3.3.3.3.4.4.4.3.3.3.3.3.4.6.4.3.3.3.3.3.4.3.5.3.4.4.6

Level    : 2
Question : 4.4.5.3.3.3.3.3.3.3.6.4.3.3.3.3.3.4.4.4.3.3.3.3.3.4.6.4.3.3.3.3.3.4.3.5.3.4.4.6

Result   : 32
Response : Yay, that's right!

[SNIP]

Level 100.: 4.4.5.3.3.3.3.3.3.3.5.5.3.3.3.3.3.4.3.4.3.4.4.4.3.4.4.6.3.4.3.4.3.3.3.3.3.4.6.4.3.3.3.3.3.4.3.6.3.4.3.4.3.4.3.6.3.4.5.3.3.4.5.3.3.4.4.4.3.4.5.3

Level    : 100
Question : 4.4.5.3.3.3.3.3.3.3.5.5.3.3.3.3.3.4.3.4.3.4.4.4.3.4.4.6.3.4.3.4.3.3.3.3.3.4.6.4.3.3.3.3.3.4.3.6.3.4.3.4.3.4.3.6.3.4.5.3.3.4.5.3.3.4.4.4.3.4.5.3

Result   : 1998
Response : Yay, that's right!

IW{Crypt0_c0d3}
```
