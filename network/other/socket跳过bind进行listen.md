# socket跳过bind进行listen

尝试用 `C` 写 `FTP` 服务端的 `PASV` 指令处理时，需要服务器打开一个随机端口进行监听，然后就去对 `bind()` 函数进行了搜索，发现相关的介绍大多比较笼统。不过最后总算是找到了自己想要的东西。

```text
socket() > bind() > listen() > accept() > read()/write() > close()
```

在使用 socket 进行通信时，大多数讲解中的服务器端都是上面这种模式：先给监听用的socket绑定一个指定的端口，然后客户端通过这个指定的端口与服务器通信。

而 `FTP` 中的 `PASV` 是在服务端已经与客户端建立了一条命令通道的情况下，服务端再随机监听一个大于 `1024` 的端口用于数据传输，通过命令通道告诉客户端自己监听的端口，然后客户端连接建立数据通道。并不需要人为指定一个数据端口。`bind()` 的作用是把 `socket` 绑定到一个指定的端口上，然后进行下一步，那么能否设置让 `bind()` 自己确定一个随机端口或者跳过 `bind()` 环节呢？

在 `Google` 上没找到自己想要的，于是尝试到手册中寻找，在 `bind()` 的手册中只发现了这个：

```text
It is normally necessary to assign a local address using bind() before a SOCK_STREAM socket may receive connections (see accept(2)).
```

然后就去看了 `accept()`：

```text
The argument sockfd is a socket that has been created with socket(2), bound to a local address with bind(2), and is listening for connections after a listen(2).
```

都是按照的 `bind() > listen() > accept()` 的流程，于是又去看了一下 `listen()`，在里面可以看到这样的一个错误信息：

```text
The listen() function shall fail if:
EDESTADDRREQ
The socket is not bound to a local address, and the protocol does not support listening on an unbound socket.
```

那么要是跳过 `bind()` 直接进行 `listen()` 会发生什么呢？在 `man 2 listen` 中看到了

```text
EADDRINUSE
(Internet domain sockets) The socket referred to by sockfd had not previously been bound to an address and, upon attempting to bind it to an ephemeral port, it was determined that all port numbers in the ephemeral port range are currently in use. See the discussion of /proc/sys/net/ipv4/ip_local_port_range in ip(7).
```

貌似 `listen()` 一个未进行过 `bind()` 的 `socket`，会将这个 `socket` 绑定到一个临时端口上？`man 7 ip` 后，总算是找到了比较详细的解释：

```text
When a process wants to receive new incoming packets or connections, it should bind a socket to a local interface address using bind(2). In this case, only one IP socket may be bound to any given local (address, port) pair. When INADDR_ANY is specified in the bind call, the socket will be bound to all local interfaces. When listen(2) is called on an unbound socket, the socket is automatically bound to a random free port with the local address set to INADDR_ANY. When connect(2) is called on an unbound socket, the socket is automatically bound to a random free port or to a usable shared port with the local address set to INADDR_ANY.
```

当对一个未进行绑定的 `socket` 使用 `listen()` 时，`socket` 会被自动绑定到一个随机的空闲端口上，绑定的IP地址会被设定为 `INADDR_ANY`，即(`0.0.0.0`)，此时`listen()` 会监听本地所有 `IP` 的这一端口。这正是 `PASV` 需要的，终于可以放心地跳过 `bind()` 进行 `listen()` 了。

```cpp
//监听本地随机端口
struct sockaddr_in local_addr;
socklen_t local_addr_len;
local_addr_len = sizeof(local_addr);
memset(&local_addr, 0, sizeof(local_addr));
int local_socket = socket(AF_INET, SOCK_STREAM, 0);
listen(local_socket, 10);

//获取监听的IP和端口
char IP[50];
getsockname(local_socket, (struct sockaddr *)&local_addr, &local_addr_len);
strcpy(IP, inet_ntoa(local_addr.sin_addr));
int data_port = ntohs(local_addr.sin_port);
    
//接受客户端连接
struct sockaddr_in client_addr;
socklen_t client_addr_len;
client_addr_len = sizeof(client_addr);
memset(&client_addr, 0, sizeof(client_addr));
int data_socket = accept(local_socket, (struct sockaddr*)&client_addr, &client_addr_len);
```

## 参考

- [socket跳过bind进行listen](https://whoisnian.com/2018/02/02/Socket-%E8%B7%B3%E8%BF%87bind%E8%BF%9B%E8%A1%8Clisten/)
