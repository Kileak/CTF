# Internetwache 2016 - Reversing - SPIM - 50 pts

> Description: My friend keeps telling me, that real hackers speak assembly fluently. Are you a real hacker? Decode this string: "IVyN5U3X)ZUMYCs"
>
>Attachment: [rev50.zip](rev50.zip)

# Write-up

The attachment contains a MIPS disassembly of the decoding algorithm:

```shell
$ cat README.txt 
User Text Segment [00400000]..[00440000]
[00400000] 8fa40000  lw $4, 0($29)            ; 183: lw $a0 0($sp) # argc 
[00400004] 27a50004  addiu $5, $29, 4         ; 184: addiu $a1 $sp 4 # argv 
[00400008] 24a60004  addiu $6, $5, 4          ; 185: addiu $a2 $a1 4 # envp 
[0040000c] 00041080  sll $2, $4, 2            ; 186: sll $v0 $a0 2 
[00400010] 00c23021  addu $6, $6, $2          ; 187: addu $a2 $a2 $v0 
[00400014] 0c100009  jal 0x00400024 [main]    ; 188: jal main 
[00400018] 00000000  nop                      ; 189: nop 
[0040001c] 3402000a  ori $2, $0, 10           ; 191: li $v0 10 
[00400020] 0000000c  syscall                  ; 192: syscall # syscall 10 (exit) 
[00400024] 3c081001  lui $8, 4097 [flag]      ; 7: la $t0, flag 
[00400028] 00004821  addu $9, $0, $0          ; 8: move $t1, $0 
[0040002c] 3401000f  ori $1, $0, 15           ; 11: sgt $t2, $t1, 15 
[00400030] 0029502a  slt $10, $1, $9          
[00400034] 34010001  ori $1, $0, 1            ; 12: beq $t2, 1, exit 
[00400038] 102a0007  beq $1, $10, 28 [exit-0x00400038] 
[0040003c] 01095020  add $10, $8, $9          ; 14: add $t2, $t0, $t1 
[00400040] 81440000  lb $4, 0($10)            ; 15: lb $a0, ($t2) 
[00400044] 00892026  xor $4, $4, $9           ; 16: xor $a0, $a0, $t1 
[00400048] a1440000  sb $4, 0($10)            ; 17: sb $a0, 0($t2) 
[0040004c] 21290001  addi $9, $9, 1           ; 19: add $t1, $t1, 1 
[00400050] 0810000b  j 0x0040002c [for]       ; 20: j for 
[00400054] 00082021  addu $4, $0, $8          ; 24: move $a0, $t0 
[00400058] 0c100019  jal 0x00400064 [printstring]; 25: jal printstring 
[0040005c] 3402000a  ori $2, $0, 10           ; 26: li $v0, 10 
[00400060] 0000000c  syscall                  ; 27: syscall 
[00400064] 34020004  ori $2, $0, 4            ; 30: li $v0, 4 
[00400068] 0000000c  syscall                  ; 31: syscall 
[0040006c] 03e00008  jr $31                   ; 32: jr $ra 
```

The decoding part starts at 0x00400024, so let's check what it does:

```
[00400024] 3c081001  lui $8, 4097 [flag]      ; 7: la $t0, flag			(t0 <= flag)
[00400028] 00004821  addu $9, $0, $0          ; 8: move $t1, $0 		(t1 = 0)
[0040002c] 3401000f  ori $1, $0, 15           ; 11: sgt $t2, $t1, 15 	(t2 = t1 | 15)
[00400030] 0029502a  slt $10, $1, $9          
[00400034] 34010001  ori $1, $0, 1            ; 12: beq $t2, 1, exit 	
[00400038] 102a0007  beq $1, $10, 28 [exit-0x00400038] 
[0040003c] 01095020  add $10, $8, $9          ; 14: add $t2, $t0, $t1 	(t2 = t0 + t1)
[00400040] 81440000  lb $4, 0($10)            ; 15: lb $a0, ($t2) 		(a0 = [t2])
[00400044] 00892026  xor $4, $4, $9           ; 16: xor $a0, $a0, $t1   (a0 = a0 ^ t1)
[00400048] a1440000  sb $4, 0($10)            ; 17: sb $a0, 0($t2) 		(t2 = a0)
[0040004c] 21290001  addi $9, $9, 1           ; 19: add $t1, $t1, 1 	(t1 = t1 + 1)
[00400050] 0810000b  j 0x0040002c [for]       ; 20: j for 
```

`t1` is a counter variable, and the encoding stops when it reaches 15. `t2` is a pointer to the current char in the loop, and the char at that position get's xored with the current index.

This boils down to a simple xor encryption:

```python
#!/usr/bin/python
import sys

encoded = "IVyN5U3X)ZUMYCs"

for i in range(0,len(encoded)):
	sys.stdout.write(str(chr(ord(encoded[i])^i)))
```

This should do the decoding for us:

```shell
$ python dec.py 
IW{M1P5_!S_FUN}
```


