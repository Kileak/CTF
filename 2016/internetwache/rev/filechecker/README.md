# IWCTF 2016 - Reversing - File Checker - 60 pts

> Description: My friend sent me this file. He told that if I manage to reverse it, I'll have access to all his devices. My misfortune that I don't know anything about reversing :/
>
> Attachment: [rev60.zip](rev60.zip)

# Write-up

```shell
$ file filechecker 
filechecker: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, 
interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 2.6.32, BuildID[sha1]=564c7e61a18251b57f8c2c3dc205ed3a5b35cca6, 
stripped
```

Executing the binary reveals, that it fails on opening '.password'

```shell
$ ltrace ./filechecker 
__libc_start_main(0x400666, 1, 0x7ffc12dfa718, 0x400850 <unfinished ...>
fopen(".password", "r")                                                     = 0
printf("Fatal error: File does not exist"...)                               = 32
Fatal error: File does not exist+++ exited (status 1) +++
```

Creating the file and input some testing flag like "IW{abcdefg}" makes it run, but it just tells us, that we have the wrong chars.

Time to have a look at the disassembly. It shows, that it opens and read the file and then calls a test function for every character.

```
000000000040079d         mov        rbp, rsp
00000000004007a0         mov        dword [ss:rbp+var_44], edi
00000000004007a3         mov        qword [ss:rbp+var_50], rsi
00000000004007a7         mov        dword [ss:rbp+var_40], 0x12ee
00000000004007ae         mov        dword [ss:rbp+var_3C], 0x12e0
00000000004007b5         mov        dword [ss:rbp+var_38], 0x12bc
00000000004007bc         mov        dword [ss:rbp+var_34], 0x12f1
00000000004007c3         mov        dword [ss:rbp+var_30], 0x12ee
00000000004007ca         mov        dword [ss:rbp+var_2C], 0x12eb
00000000004007d1         mov        dword [ss:rbp+var_28], 0x12f2
00000000004007d8         mov        dword [ss:rbp+var_24], 0x12d8
00000000004007df         mov        dword [ss:rbp+var_20], 0x12f4
00000000004007e6         mov        dword [ss:rbp+var_1C], 0x12ef
00000000004007ed         mov        dword [ss:rbp+var_18], 0x12d2
00000000004007f4         mov        dword [ss:rbp+var_14], 0x12f4
00000000004007fb         mov        dword [ss:rbp+var_10], 0x12ec
0000000000400802         mov        dword [ss:rbp+var_C], 0x12d6
0000000000400809         mov        dword [ss:rbp+var_8], 0x12ba
0000000000400810         mov        eax, dword [ss:rbp+var_44]
0000000000400813         cdqe       
0000000000400815         mov        edx, dword [ss:rbp+rax*4+var_40]
0000000000400819         mov        rax, qword [ss:rbp+var_50]
000000000040081d         mov        eax, dword [ds:rax]
000000000040081f         lea        ecx, dword [ds:rdx+rax]
0000000000400822         mov        edx, 0x354ac933
0000000000400827         mov        eax, ecx
0000000000400829         imul       edx
000000000040082b         sar        edx, 0xa
000000000040082e         mov        eax, ecx
0000000000400830         sar        eax, 0x1f
0000000000400833         sub        edx, eax
0000000000400835         mov        eax, edx
0000000000400837         imul       eax, eax, 0x1337
000000000040083d         sub        ecx, eax
000000000040083f         mov        eax, ecx
0000000000400841         mov        rdx, qword [ss:rbp+var_50]
0000000000400845         mov        dword [ds:rdx], eax
0000000000400847         nop        
0000000000400848         pop        rbp
0000000000400849         ret        
```

Hopper gives the following pseudo code for this:

```
function sub_40079c {
    rcx = *(int32_t *)(rbp + sign_extend_32(arg0) * 0x4 + 0xffffffffffffffc0) + *(int32_t *)arg1;
    rax = rcx - ((SAR(rcx * 0x354ac933, 0xa)) - (SAR(rcx, 0x1f))) * 0x1337;
    *(int32_t *)arg1 = rax;
    return rax;
}
```

Though quite some shifting and calculations there, this boils down to:

`result = 0x1337 - (0x12ee + curchar)`

So in the end, every character gets summed with the value at the same index in the array `[0x12ee, 0x12e0, 0x12bc, 0x12f1, 0x12ee, 0x12eb, 0x12f2, 0x12d8, 0x12f4, 0x12ef, 0x12d2, 0x12f4, 0x12ec, 0x12d6, 0x12ba]`, which should result in `0x1337` to pass the validation.

```python
#!/usr/bin/python

coll = [ 0x12ee, 0x12e0, 0x12bc, 0x12f1, 0x12ee, 0x12eb, 0x12f2, 0x12d8, 0x12f4, 0x12ef, 0x12d2, 0x12f4, 0x12ec, 0x12d6, 0x12ba ]

result = ""

for val in coll:
	res = 0x1337 - val
	result += chr(res)

print result
```

This will calculate the password:

```shell
$ python solver.py 
IW{FILE_CHeCKa}
```
