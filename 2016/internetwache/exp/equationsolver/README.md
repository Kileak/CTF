# IWCTF 2016 - Exploit - EquationSolver - 60 pts

>  Description: I created a program for an unsolveable equation system. My friend somehow forced it to solve the equations. Can you tell me how he did it?
>
> Service: 188.166.133.53:12049 

# Write-up

The service shows a static equation (it's always the same) and asks us to solve it.

```shell
$ nc 188.166.133.53 12049
Solve the following equations:
X > 1337
X * 7 + 4 = 1337
Enter the solution X: 
```

Classic overflow challenge here. 

Since X has to be larger than 1337, there's no normal solution for this equation. We'll have to pass a value, which will overflow the 32 bit integer result.

1337 in 32 bit binary:

```shell
00000000000000000000010100111001 (1337)
```

If we now just add 2^32 the value would result to:

```shell
100000000000000000000010100111001 (4294968633)
```

The service will then try to stuff this into the 32 bit integer value, cutting off the leading 1, resulting again in:

```shell
00000000000000000000010100111001 (1337)
```

So we just have to find a value for x that results in 4294968633

```shell
(4294968633 - 4) / 7 = 613566947
```

```shell
$ nc 188.166.133.53 12049
Solve the following equations:
X > 1337
X * 7 + 4 = 1337
Enter the solution X: 613566947
You entered: 613566947
613566947 is bigger than 1337
1337 is equal to 1337
Well done!
IW{Y4Y_0verfl0w}
```

And there's our flag.





