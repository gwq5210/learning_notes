# 浅谈 socket 的关闭和 socket lingering

## socket 的关闭

在 `Unix` 上，`socket` 是一个 `fd`，`sockfd = socket(int socket_family, int socket_type, int protocol)` ，因此 `socket` 可以使用 `close()` 调用，将其当作一个普通 `fd` 进行关闭，也可以使用 `shutdown()` 系统调用，将其当作一个全双工连接进行关闭。

首先来看一个正常的 `socket` 关闭流程，`close()` 调用时，主动关闭端内核会首先检查 `read buffer` 中有没有未被应用层程序处理的内容， 如果有，则此时主动关闭端内核会丢弃这段 `buffer` 并直接向对端发送 `RST` 并关闭 `socket`，这将导致之前已经发送但尚未送达的、或是已经进入对端 `receive buffer` 但还未被对端应用程序处理的正常响应数据被对端无条件丢弃，对端应用程序可能出现异常。

如果 `close()` 时 `read buffer` 为空，则 `close()` 立刻返回，`write buffer` 中的数据马上写入 `socket`，`socket` 在发送完毕数据后进行正常的四次挥手关闭并进入 `TIME WAIT`。虽然应用程序将不会在此阻塞并立刻认为数据已经成功发出，然而实际上 `buffer` 中剩余数据的发送在后台进行，且对端有没有正确收到 `buffer` 中的这段数据，主动关闭端应用层程序是不知道的（因为它认为 `socket` 已经关闭了，不会继续对这个 `socket` 作任何响应）。

而 `shutdown()` 调用则可以半关闭连接（只关闭读方向或者写方向），其完整定义为 `int shutdown(int sockfd, int how)` ，其中 `how` 参数可以为 `SHUT_WR` / `SHUT_RD` / `SHUT_RDWR` 控制关闭写方向/读方向/读写双向，比如发送方调用 `shutdown(fd, SHUT_WR)` 关闭写方向，任何时候都只会发出 `FIN`，而不会和 `close()` 一样可能发出 `RST`。发送方关闭收方向时，实际上连接已然是 `ESTABLISH` 状态。

题外话，`nginx` 的一个 `http2 bug` 正是 `close()` 和 `shutdown()` 的区别导致, `https://trac.nginx.org/nginx/ticket/1250#comment:4` ，评论中引用了这么一篇文章 `https://blog.netherlabs.nl/articles/2009/01/18/the-ultimate-so_linger-page-or-why-is-my-tcp-not-reliable` 吐槽“TCP 也不可靠传输嘛”

## TIME_WAIT 问题

被 `close()` 的 `socket` 在四次挥手结束后将进入 `TIME_WAIT` 状态，这个状态原本是为避免连接没有可靠断开而和后续新建的连接的数据混淆，`TIME_WAIT` 中的 `peer` 会给所有来包回 `RST`，具体见参考资料1等，对于 `Windows`，`TIME_WAIT` 状态持续的 `2MSL` 可以通过注册表配置，而 `Linux` 则是写死在内核源码里的 `60` 秒。`TIME_WAIT` 出现在主动关闭连接一方，而反向代理服务器需要以较高的速率向 `upstream server` 主动发起连接并通常由反向代理服务器主动关闭，`TIME_WAIT socket` 的堆积会影响主动建立连接，因此消灭 `TIME_WAIT` 一直是高并发反向代理服务需要解决的一个问题（实际上也是我关注 `lingering` 的起因，曾经妄图借助 `lingering` 消灭 `TIME_WAIT`）。

## SO_LINGER

> 注意是 linger（暂留） 不是 linear / linearize（线性），不要眼瞎

参考资料1中提到，一种避免 `TIME_WAIT` 的方式是使用 `socket lingering`；另一方面，正常的 `socket` 被 `close()` 调用关闭时，应用层进程时无法得知 `buffer` 中的数据发出后对端有没有正确 `ACK`，且有可能向对端发送 `RST` 造成对端应用丢弃数据引起异常。`Socket lingering` 一定程度上可以解决这个问题。

先来看 `lingering` 在 `Linux` 中的实现，`lingering` 的配置方法是在创建 `socket` 时通过 `setsocketopt()` 调用设置 `SO_LINGER option`，而 `SO_LINGER` 有两个相关参数，源码定义是：

```cpp
#include <sys/socket.h>
struct linger {  
  int l_onoff //0=off, nonzero=on (开关)
  int l_linger //linger time (延迟时间)
}
```

从行为上说，如果有程序尝试 `close()` 一个设置了 `SO_LINGER` 的 `socket`，则有以下可能：

- 启用 `l_onoff` 且设置 `l_linger=0` 时，将直接使用 `RST` 进行关闭 `socket`；
- 启用 `l_onoff` 且设置 `l_linger` 为非零值时，内核将阻塞应用程序，并以 `l_linger` 设定的延迟时间为周期不断尝试将 `buffer` 中的数据发出并等待对端 `ACK`，如果对端 `ACK`，则使用正常四次挥手流程关闭 `socket` 同时退出应用程序；

需注意，在 `Linux` 上，设置 `SO_LINGER` 且使用非零值延迟时间会导致应用程序阻塞，即使程序创建的是一个 `non-blocking socket`。

## Nginx 对 socket lingering 的处理

首先看看 `Nginx` 的相关配置项：

| | |
| - | - |
| SYNTAX: | LINGERING_CLOSE OFF \| ON \| ALWAYS; |
| Default: | lingering_close on; |

默认值为 `on`，`nginx` 会根据下面两个参数的值进行等待，配置为 `always` 则无条件等待，配置为 `off` 则 `nginx` 将不会等待数据发送完毕且永远会立刻关闭 `socket`，这一行为可能导致协议出现意外问题。

| | |
| - | - |
| SYNTAX: | LINGERING_TIME TIME; |
| Default: | lingering_time 30s; |

默认为 `30` 秒，在 `lingering_close` 生效的情况下，这个参数指定 `nginx` 会等待 `client` 回复 `ACK` 的最长时间，超过这个时间后，`socket` 将被关闭，无论 `client` 是否还在回复数据。

| | |
| - | - |
| SYNTAX: | LINGERING_TIMEOUT TIME; |
| Default: | lingering_timeout 5s; |

默认为 `5`秒，`client` 若 `5` 秒没有发送 `ACK`，`socket` 将被关闭，若 `client` 持续发送数据，`lingering_timeout` 将不会生效，`nginx` 将持续进行收包-丢弃的循环，但这一循环重复多次后如果超过 `lingering_time` 的时间，则 `nginx` 依旧会关闭连接。

会发现 `nginx` 是默认打开 `lingering` 的，但是从 `nginx` 源码可知 `nginx` 会视情况对 `socket` 的 `SO_LINGER` 参数进行设置，因此实际上并不是所有 `socket` 都会和上一节分析的行为一致，详细的源码见参考资料3，简单的讲在以下情况 `nginx` 会对 `socket` 进行延迟关闭：

- 配置 `lingering_close` 为 `always` ，此时无条件延迟关闭。
- 配置 `lingering_close` 为 `on` ，并且接收缓冲区中收到了来自客户端的数据，或读事件就绪准备接收客户端发送来的数据时。

需要延迟关闭时，`nginx` 会调用 `ngx_http_set_lingering_close` 函数，而该函数主要做的事情有：从全局配置结构体 `clcf` 中解析 `lingering_time` 和 `lingering_timeout` 并设置定时器，调用 `shutdown()` 对 `socket` 写方向进行关闭 ，将 `rev->handler` 的回调设置为`ngx_http_lingering_close_handler`，而这个 `handler` 函数在三种情况下会返回：

1. `rev->timedout` 即一次 `lingering_timeout` 没有收到任何数据
2. `(r->lingering_time - ngx_time()) <= 0` 即超过设置的 `lingering_time` 总超时时间
3. `do-while` 调用 `recv()` 阻塞地接收来自客户端的数据，直到 `recv()` 返回即收完所有数据

`handler` 函数超时后，`nginx` 将进入 `ngx_http_close_request` 函数，调用两个函数分别用于释放 `HTTP` 请求和关闭 `TCP` 连接，先调用 `ngx_http_free_request` 设置 `l_linger=0` ，然后进入 `ngx_close_connection`，通过 `ngx_close_socket(fd)` 关闭这个 `socketfd`，此时会发送 `RST` 给客户端。

从上述流程可以发现，`nginx` 在使用 `socket lingering` 的时候没有自始至终都设置 `SO_LINGER`，只有在真正需要借助 `SO_LINGER` 的特性 `Reset` 连接的瞬间才设置 `SO_LINGER option` 直接令 `l_linger=0`，因此 `nginx` 的行为理应是平台/操作系统无关的，参考资料2中 `BSD` 和 `Linux` 的具体行为区别都不影响 `nginx` 的行为，这操作真骚。

## To linger or not, that is the question

虽然，使用 `RST` 关闭连接确实不会有 `TIME_WAIT`，原理上说“`socket lingering` 可以避免 `TIME_WAIT`”是正确的，但是即便如此我也不知道这个设置有什么实际应用，因为在大部分场合下使用 `RST` 关闭连接会造成对端异常；另一方面，由于 `Linux` 的实现问题，即使程序使用的 `non-blocking sockets`，`lingering` 也会导致程序阻塞（4.9 TLS 分支的代码和参考资料2中是一样的，这个行为应该没有改变）。从这些信息来看，自行编写 `socket` 程序使用 `lingering` 的配置应当慎重，至少不应该为了避免 `TIME_WAIT` 堆积而使用 `lingering`。

## 参考

- [浅谈 socket 的关闭和 socket lingering](https://www.starduster.me/2019/07/06/socket-lingering-and-closing/)
