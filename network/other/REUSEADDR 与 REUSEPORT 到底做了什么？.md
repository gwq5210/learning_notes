# REUSEADDR 与 REUSEPORT 到底做了什么？

在 `linux` 下的服务器开发中，`REUSEADDR` 与 `REUSEPORT` 是我们经常会用到的两个套接字选项。但很多时候只是简单的使用，而没有深究其原理。甚至有些搞不懂两者之间的区别和联系。网上关于这两个的文章一大堆，但是看上去好像都没有说透，甚至有些是错误的理解。

`Stackoverflow` 上有一篇关于这个的高赞回答写得很好，有兴趣的读者可以自行查询[how-do-so-reuseaddr-and-so-reuseport-differ](https://stackoverflow.com/questions/14388706/how-do-so-reuseaddr-and-so-reuseport-differ)

本文试图通过阅读 `linux` 内核的部分源码来分析这两者的本质，文中观点并不一定完全正确，仅供各位参考了。本文只分析 `TCP` 的 `bind` 过程，不涉及 `UDP` 或其他。

## Man文档描述

首先抬出那个男人（Man文档），看看是怎么描述的这两个套接字选项的:

```text
SO_REUSEADDR: Indicates that the rules used in validating addresses supplied in a bind(2) call should allow reuse of local addresses. For AF_INET sockets this means that a socket may bind, except when there is an active listening socket bound to the address. When the listening socket is bound to INADDR_ANY with a specific port then it is not possible to bind to this port for any local address. Argument is an integer boolean flag。
```

简单翻译一下：`SO_REUSEADDR` 提供了一套复用地址的规则。对于 `AF_INET` 套接字，这意味着一个套接字可以绑定，除非有一个活动的监听套接字绑定到该地址。当监听套接字使用特定端口绑定到 `INADDR_ANY` 时，就不可能为任何本地地址重新绑定到该端口。

```text
SO_REUSEPORT:
Permits multiple AF_INET or AF_INET6 sockets to be bound to an identical socket address. This option must be set on each socket (including the first socket) prior to calling bind(2) on the socket. To prevent port hijacking, all of the processes binding to the same address must have the same effective UID. This option can be employed with both TCP and UDP sockets.

For TCP sockets, this option allows accept(2) load distribution in a multi-threaded server to be improved by using a distinct listener socket for each thread. This provides improved load distribution as compared to traditional techniques such using a single accept(2)ing thread that distributes connections, or having multiple threads that compete to accept(2) from the same socket.

For UDP sockets, the use of this option can provide better distribution of incoming datagrams to multiple processes (or threads) as compared to the traditional technique of having multiple processes compete to receive datagrams on the same socket.
```

此选项允许多个 `AF_INET` 或者 `AF_INET6` 的套接字绑定到同一个 `socket` 地址上。必须每一个调用 `bind` 函数的 `socket` 套接字都要设置这个选项(包括第一个)才能生效。为了防止端口劫持，所有绑定到相同地址的进程必须是同一个 `UID`。 这个选项适用于 `TCP` 和 `UDP` 套接字。

对于 `TCP` 套接字而言，这个选项通过每个监听线程使用不同的 `listen fd` 来改进 `accpet` 的负载分配。相对于传统的做法如只有一个 `accept` 线程在处理连接，或者是多个线程使用同一个 `listen fd` 进行 `accept`，`REUSEPORT` 有助于负载均衡的改进。

对于 `UDP` 而言，相比如以前多个进程(或线程)都在同一个 `socket` 上接收数据报的情况的传统做法, 此选项能够提供一种更好的负载均衡能力。

## 几个简单的 bind 测试

首先做几个测试，我的测试虚拟机是 `centos8`，基于 `Linux version 4.18.0-305.3.1.el8.x86_64` 版本。

两个简单地测试用例如下，有兴趣的同学可以自行测试一遍

[reuse_addr_test.cc](https://github.com/gwq5210/gtl/blob/main/examples/net/reuse_addr_test.cc)

### 测试1

不开启 `REUSEADDR`，也不调用 `listen` 函数，两个使用相同的 `ip:port` 进行 `bind`，结果如下

很遗憾，第二次试图 `bind` 时候得到了错误

```text
./reuse_addr_test --server_address1="127.0.0.1:9999" --server_address2="127.0.0.1:9999" --reuse_addr=false --listen_first=false --reuse_port=false

[2023-03-07 20:15:46.767] [info] [reuse_addr_test.cc:12] first BindAndListen 127.0.0.1:9999 started
[2023-03-07 20:15:46.767] [info] [reuse_addr_test.cc:21] bind server address 127.0.0.1:9999 sucessfully
[2023-03-07 20:15:46.767] [info] [reuse_addr_test.cc:12] second BindAndListen 127.0.0.1:9999 started
[2023-03-07 20:15:46.767] [error] [socket.cc:114] bind address(127.0.0.1:9999) failed! errno:98, errmsg:Address already in use
```

### 测试2

开启 `REUSEADDR`，不进行 `listen`，两个使用相同 `ip:port` 进行 `bind`

可以看到，开启 `REUSEADDR` 并且没有 `listen` 的情况下，两次 `bind` 都成功了。

```text
./reuse_addr_test --server_address1="127.0.0.1:9999" --server_address2="127.0.0.1:9999" --reuse_addr=true --listen_first=false --reuse_port=false

[2023-03-07 20:16:41.511] [info] [reuse_addr_test.cc:12] first BindAndListen 127.0.0.1:9999 started
[2023-03-07 20:16:41.511] [info] [reuse_addr_test.cc:21] bind server address 127.0.0.1:9999 sucessfully
[2023-03-07 20:16:41.511] [info] [reuse_addr_test.cc:12] second BindAndListen 127.0.0.1:9999 started
[2023-03-07 20:16:41.511] [info] [reuse_addr_test.cc:21] bind server address 127.0.0.1:9999 sucessfully
```

### 测试3

开启 `REUSEADDR`，并且调用 `listen` 使套接字称为监听状态，两个使用相同 `ip:port` 进行`bind`，结果如下：

可以看到，尽管开启了 `REUSEADDR` ，但是由于套接字调用了 `listen` 函数，变为了 `TCP_LISTEN` 状态，第二次 `bind` 就会失败。

```text
./reuse_addr_test --server_address1="127.0.0.1:9999" --server_address2="127.0.0.1:9999" --reuse_addr=true --listen_first=true --reuse_port=false

[2023-03-07 20:17:50.022] [info] [reuse_addr_test.cc:12] first BindAndListen 127.0.0.1:9999 started
[2023-03-07 20:17:50.022] [info] [reuse_addr_test.cc:21] bind server address 127.0.0.1:9999 sucessfully
[2023-03-07 20:17:50.022] [info] [reuse_addr_test.cc:28] listen server address 127.0.0.1:9999 sucessfully
[2023-03-07 20:17:50.022] [info] [reuse_addr_test.cc:12] second BindAndListen 127.0.0.1:9999 started
[2023-03-07 20:17:50.022] [error] [socket.cc:114] bind address(127.0.0.1:9999) failed! errno:98, errmsg:Address already in use
```

### 测试4

与测试3相同，只是不开启 `REUSEADDR`，开启 `REUSEPORT`。

可以看到，虽然没开启 `REUSEADDR` ，但是开启了 `REUSEPORT`。套接字调用了 `listen` 函数，变为了 `TCP_LISTEN` 状态，但是第二次 `bind` 还是成功的，并且调用 `listen` 也成功了

并且可以看到两个进程在监听同一个地址和端口

```text
./reuse_addr_test --server_address1="127.0.0.1:9999" --server_address2="127.0.0.1:9999" --reuse_addr=false --listen_first=true --reuse_port=true

[2023-03-07 20:39:56.490] [info] [reuse_addr_test.cc:13] first BindAndListen 127.0.0.1:9999 started
[2023-03-07 20:39:56.490] [info] [reuse_addr_test.cc:29] bind server address 127.0.0.1:9999 sucessfully
[2023-03-07 20:39:56.490] [info] [reuse_addr_test.cc:36] listen server address 127.0.0.1:9999 sucessfully
[2023-03-07 20:39:56.490] [info] [reuse_addr_test.cc:13] second BindAndListen 127.0.0.1:9999 started
[2023-03-07 20:39:56.490] [info] [reuse_addr_test.cc:29] bind server address 127.0.0.1:9999 sucessfully
[2023-03-07 20:39:56.490] [info] [reuse_addr_test.cc:36] listen server address 127.0.0.1:9999 sucessfully
```

## 参考

- [REUSEADDR 与 REUSEPORT 到底做了什么？](https://zhuanlan.zhihu.com/p/492644204)
