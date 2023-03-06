# tcp_tw_reuse和tcp_tw_recycle使用场景及注意事项

`linux TIME_WAIT` 相关参数

```text
net.ipv4.tcp_tw_reuse = 0    表示开启重用。允许将TIME-WAIT sockets重新用于新的TCP连接，默认为0，表示关闭
net.ipv4.tcp_tw_recycle = 0  表示开启TCP连接中TIME-WAIT sockets的快速回收，默认为0，表示关闭
net.ipv4.tcp_fin_timeout = 60  表示如果套接字由本端要求关闭，这个参数决定了它保持在FIN-WAIT-2状态的时间
```

注意：

- 不像 `Windows` 可以修改注册表修改 `2MSL` 的值，`linux` 需要修改内核宏定义重新编译，`tcp_fin_timeou`t 不是 `2MSL` 而是 `Fin-WAIT-2` 状态超时时间.
- `tcp_tw_reuse` 和 `SO_REUSEADDR` 是两个完全不同的东西
  - `SO_REUSEADDR` 允许同时绑定 `127.0.0.1` 和 `0.0.0.0` 同一个端口
  - `SO_RESUSEPORT` `linux 3.7` 才支持，用于绑定相同 `ip:port`，像 `nginx` 那样 `fork` 方式也能实现
- `tw_reuse`，`tw_recycle` 必须在客户端和服务端 `timestamps` 开启时才管用（默认打开）
- `tw_reuse` 只对客户端起作用，开启后客户端在1s内回收
- `tw_recycle` 对客户端和服务器同时起作用，开启后在 `3.5*RTO` 内回收，`RTO 200ms~ 120s` 具体时间视网络状况。
  - 内网状况比 `tw_reuse` 稍快，公网尤其移动网络大多要比 `tw_reuse` 慢，优点就是能够回收服务端的 `TIME_WAIT` 数量

## 客户端

- 作为客户端因为有端口 `65535` `问题，TIME_OUT` 过多直接影响处理能力，打开 `tw_reuse` 即可解决，不建议同时打开 `tw_recycle`，帮助不大；
- `tw_reuse` 帮助客户端 `1s` 完成连接回收，基本可实现单机 `6w/s` 短连接请求，需要再高就增加 `IP` 数量；
- 如果内网压测场景，且客户端不需要接收连接，同时 `tw_recycle` 会有一点点好处；
- 业务上也可以设计由服务端主动关闭连接。

## 服务端

- 打开tw_reuse无效
- 线上环境 `tw_recycle` 不要打开
  - 服务器处于 `NAT` 负载后，或者客户端处于 `NAT` 后（基本公司家庭网络基本都走 `NAT`）；
  - 公网服务打开就可能造成部分连接失败，内网的话到时可以视情况打开；
  - 像我所在公司对外服务都放在负载后面，负载会把 `timestamp` 都给清空，就算你打开也不起作用。
- 服务器 `TIME_WAIT` 高怎么办
  - 不像客户端有端口限制，处理大量 `TIME_WAIT` `Linux` 已经优化很好了，每个处于 `TIME_WAIT` 状态下连接内存消耗很少，
  - 而且也能通过 `tcp_max_tw_buckets = 262144` 配置最大上限，现代机器一般也不缺这点内存。
- 业务上也可以设计由客户端主动关闭连接

## 原理分析

- MSL 由来
  - 发起连接关闭方回复最后一个 `fin` 的 `ack`，为避免对方 `ack` 收不到、重发的或还在中间路由上的 `fin` 把新连接给丢掉了，等个 `2MSL`（`linux` 默认 `1min`）。
  - 也就是连接有谁关闭的那一方有 `time_wait` 问题，被关那方无此问题。
- reuse、recycle
  - 通过 `timestamp` 的递增性来区分是否新连接，新连接的 `timestamp` 更大，那么保证小的 `timestamp` 的 `fin` 不会 `fin` 掉新连接，不用等 `2MSL`。
- reuse
  - 通过 `timestamp` 递增性，客户端、服务器能够处理 `outofbind fin`包
- recycle
  - 对于服务端，同一个 `src ip`，可能会是 `NAT` 后很多机器，这些机器 `timestamp` 递增性无可保证，服务器会拒绝非递增请求连接。

## 参考

- [tcp_tw_reuse和tcp_tw_recycle使用场景及注意事项](https://www.cnblogs.com/lulu/p/4149312.html)
