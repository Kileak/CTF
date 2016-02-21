# Internetwache 2016 - Web - The Secret Store - 70 pts

> Description: We all love secrets. Without them, our lives would be dull. A student wrote a secure secret store, however he was babbling about problems with the database. Maybe I shouldn't use the 'admin' account.
>
>  Service: https://the-secret-store.ctf.internetwache.org/ 

# Write-up

The challenge page has a login and register page. Sure enough, we need to login as admin. Though trying to register as an admin results in "User already exists". But the register page fails to check the length of the username correctly when storing it.

So if we create a username with a length > 500, the check, if the user already exists will pass, but it will cut off the last characters when "storing" it.

So creating a user like:

```
User: "admin(lots of spaces => 495)a"

Password: abc
```

will result in creating the account, so changing the password for the admin account to our specified password.

We're then able to login as `admin/abc` resulting in the page spitting out the flag:

```
Welcome

Here is your secret: IW{TRUNCATION_IS_MY_FRIEND}
```
