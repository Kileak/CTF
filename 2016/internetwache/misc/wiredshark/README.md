# IWCTF 2016 - Rock with the wired shark! - 70 pts

> Description: Sniffing traffic is fun. I saw a wired shark. Isn't that strange?
>
> Attachment: [misc70.zip](misc70.zip)

# Write-up

The attachment contains a traffic dump of some http requests.

The first request just returned "unauthorized", while the second one contains an authorization string.

```shell
GET / HTTP/1.1
Host: 192.168.1.41:8080
Connection: keep-alive
Authorization: Basic ZmxhZzphenVsY3JlbWE=
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36
DNT: 1
Accept-Encoding: gzip, deflate, sdch
Accept-Language: en-US,en;q=0.8,ht;q=0.6
```

Decoding the authorization string (base64) leads to:

`flag:azulcrema`

Doesn't match the flag format of Internetwache, but let's keep this in mind.

The capture also contains an archive `flag.zip`

```shell
53	192.168.1.41:8080	text/html					1784 bytes	/
83	192.168.1.41:8080	application/octet-stream	222 bytes	flag.zip
```

Using wireshark we can export the contained request objects, so let's get the archive and try to extract it.

```shell
$ unzip flag.zip 
Archive:  flag.zip
[flag.zip] flag.txt password: 
```

Now the authorization string might come in handy. The password for the http authorization was also used for the flag-archive.

`extracting: flag.txt`

```shell
$ cat flag.txt 
IW{HTTP_BASIC_AUTH_IS_EASY}
```



