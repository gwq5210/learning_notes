# Nginx 惊群的原因和解决方案

所谓惊群现象,简单的来说就是当多个进程或线程在同时阻塞等待同一个事件时,如果该事件发生,会唤醒在等待的所有的进程/线程,但最终只可能有一个进程/线程对该事件进行处理,其他进程/线程会在失败后重新休眠,唤醒多个进程/线程这种不必要的行为会造成系统资源的浪费(涉及到进程的上下文切换)。而常见的惊群问题有accept惊群、epoll惊群。

## accept 导致的惊群问题

当多个进程/线程调用accept监听同一个socket上时,一个新连接的到来就会导致所有阻塞在该socket上的进程/线程都被唤醒,但是最后只有一个进程/线程可以accept成功,其余的又会重新休眠,这样就产生了惊群现象。

这个问题其实在linux2.6内核版本就已经解决了,它维护了一个等待队列(队列的元素为进程),并且使用了WQ_FLAG_EXCLUSIVE标志位(互斥标志位),非exclusive元素会加在等待队列的前面,而exclusive元素会加在等待队列的末尾,当有新连接到来时,会遍历等待队列,并且只唤醒第一个exclusive进程(非互斥的进程由于排在队列前面也会被唤醒)就退出遍历。

阻塞在accept上的进程都是互斥的(也就是WQ_FLAG_EXCLUSIVE标志位会被置位),因此现在的linux内核调用accept时,多个进程/线程只有一个会被唤醒并建立新连接。

而nginx中处理的主要是另外一种,epoll导致的惊群问题(确切的来说,是解决多个epfd(epfd是指调用epoll_create获取的描述符)共同监听同一个socket造成的惊群问题)。

## epoll 导致的惊群问题

虽然accept上已经不存在惊群问题了,但是以目前的服务器架构,都不会简单的使用accept阻塞等待新的连接了,而是使用epoll等I/O多路复用机制。早期的linux,调用epoll_wait后,当有读/写事件发生时,会唤醒阻塞在epoll_wait上的所有进程/线程,造成惊群现象。不过这个问题已经被修复了,使用类似于处理accpet导致的惊群问题的方法,当有事件发生时,只会唤醒等待队列中的第一个exclusive进程来处理。不过随后就可以看到,这种方法并不能完全解决惊群问题。

这里需要区分一下两种不同的情况(这两种情况,目前linux内核都有处理的办法)。

1. 多个进程/线程使用同一个epfd然后调用epoll_wait
2. 多个进程/线程有自己的epfd,然后监听同一个socket

其实也就是epoll_create和fork这两个函数调用的先后顺序问题(下面都以进程为例)。第一种情况,先调用epoll_create获取epfd,再使用fork,各进程共用同一个epfd;第二种情况,先fork,再调用epoll_create,各进程独享自己的epfd。

而nginx面对的是第二种情况,这点需要分清楚(网上有很多用第一种情况来引入nginx处理惊群问题的方法,不要被混淆了)。因为nginx的每个worker进程相互独立,拥有自己的epfd,不过根据配置文件中的listen指令都监听了同一个端口,调用epoll_wait时,若共同监听的套接字有事件发生,就会造成每个worker进程都被唤醒。

## Nginx 惊群问题的解决方法

Nginx 目前有几种方法解决惊群问题：

### accept_mutex

如果开启了accept_mutex 锁，每个 worker 都会先去抢自旋锁，只有抢占成功了，才把 socket 加入到 epoll 中，accept 请求，然后释放锁。accept_mutex 锁也有负载均衡的作用。

### EPOLLEXCLUSIVE

EPOLLEXCLUSIVE 是 Linux 4.5+ 内核新添加的一个 epoll 的标识，Nginx 在 1.11.3 之后添加了 NGX_EXCLUSIVE_EVENT。EPOLLEXCLUSIVE 标识会保证一个事件发生时候只有一个线程会被唤醒，以避免多个进程监听下的“惊群”问题。不过任一时候只能有一个工作线程调用 accept，限制了真正并行的吞吐量。

### SO_REUSEPORT

SO_REUSEPORT 是惊群最好的解决方法，Nginx 在 1.9.1 中加入了这个选项，每个 worker 进程都有自己的 socket，这些 socket 都 bind 同一个端口。当新请求到来时，内核根据四元组信息进行负载均衡，非常高效。

## 参考

- [Nginx 惊群的原因和解决方案](https://mp.weixin.qq.com/s/UQOptQg-RD8U7GIi0RqRAg)
