### Linux编程之UDP SOCKET全攻略
这篇文章将对linux下udp socket编程重要知识点进行总结，无论是开发人员应知应会的，还是说udp socket的一些偏僻知识点，本文都会讲到。尽可能做到，读了一篇文章之后，大家对udp socket有一个比较全面的认识。本文分为两个专题，第一个是常用的upd socket框架，第二个是一些udp socket并不常用但又相当重要的知识点。

#### 一、基本的udp socket编程
##### 1. UDP编程框架
  要使用UDP协议进行程序开发，我们必须首先得理解什么是什么是UDP？这里简单概括一下。
  
  UDP（user datagram protocol）的中文叫用户数据报协议，属于传输层。UDP是面向非连接的协议，它不与对方建立连接，而是直接把我要发的数据报发给对方。所以UDP适用于一次传输数据量很少、对可靠性要求不高的或对实时性要求高的应用场景。正因为UDP无需建立类如三次握手的连接，而使得通信效率很高。
  
  UDP的应用非常广泛，比如一些知名的应用层协议（SNMP、DNS）都是基于UDP的，想一想，如果SNMP使用的是TCP的话，每次查询请求都得进行三次握手，这个花费的时间估计是使用者不能忍受的，因为这会产生明显的卡顿。所以UDP就是SNMP的一个很好的选择了，要是查询过程发生丢包错包也没关系的，我们再发起一个查询就好了，因为丢包的情况不多，这样总比每次查询都卡顿一下更容易让人接受吧。

UDP通信的流程比较简单，因此要搭建这么一个常用的UDP通信框架也是比较简单的。以下是UDP的框架图。
![UDP](https://raw.githubusercontent.com/kaniel/developertools/master/socket/images/udp_1.jpg "udp_1")

由以上框图可以看出，客户端要发起一次请求，仅仅需要两个步骤（socket和sendto），而服务器端也仅仅需要三个步骤即可接收到来自客户端的消息（socket、bind、recvfrom）。

##### 2. UDP程序设计常用函数
```c
#include <sys/types.h>          
#include <sys/socket.h>
int socket(int domain, int type, int protocol);
```
参数domain:用于设置网络通信的域，socket根据这个参数选择信息协议的族

|Name   |  Purpose |
|-------|----------------------|
|AF_UNIX, AF_LOCAL  |Local communication  |            
|AF_INET   | IPv4 Internet protocols          //用于IPV4|
|AF_INET6  | IPv6 Internet protocols          //用于IPV6|
|AF_IPX  | IPX - Novell protocols|
|AF_NETLINK | Kernel user interface device|
|AF_X25 | ITU-T X.25 / ISO-8208 protocol |
|AF_AX25  | Amateur radio AX.25 protocol|
|AF_ATMPVC | Access to raw ATM PVCs|
|AF_APPLETALK | AppleTalk |                
|AF_PACKET | Low level packet interface |     
|AF_ALG | Interface to kernel crypto API|

 
***对于该参数我们仅需熟记AF_INET和AF_INET6即可***
##### 小插曲：PF_XXX和AF_XXX
我们在看Linux网络编程相关代码时会发现PF_XXX和AF_XXX会混着用，他们俩有什么区别呢？以下内容摘自《UNP》。

AF_前缀表示地址族（Address Family），而PF_前缀表示协议族（Protocol Family）。历史上曾有这样的想法：单个协议族可以支持多个地址族，PF_的值可以用来创建套接字，而AF_值用于套接字的地址结构。但实际上，支持多个地址族的协议族从来就没实现过，而头文件<sys/socket.h>中为一给定的协议定义的PF_值总是与此协议的AF_值相同。

所以我在实际编程时还是偏向于使用AF_XXX。

参数type（只列出最重要的三个）:

|        |                |
|--------|----------------|
|SOCK_STREAM  | Provides sequenced, reliable, two-way, connection-based byte streams.   //用于TCP|
|SOCK_DGRAM | Supports datagrams (connectionless, unreliable messages ). //用于UDP|
|SOCK_RAW | rovides raw network protocol access.  //RAW类型，用于提供原始网络访问|
