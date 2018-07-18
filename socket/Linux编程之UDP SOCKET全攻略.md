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

参数protocol：置0即可

返回值：

成功：非负的文件描述符

失败：-1
```c           
#include <sys/types.h>
#include <sys/socket.h>
ssize_t sendto(int sockfd, const void *buf, size_t len, int flags,
              const struct sockaddr *dest_addr, socklen_t addrlen);           
```
第一个参数sockfd:正在监听端口的套接口文件描述符，通过socket获得

第二个参数buf：发送缓冲区，往往是使用者定义的数组，该数组装有要发送的数据

第三个参数len:发送缓冲区的大小，单位是字节

第四个参数flags:填0即可

第五个参数dest_addr:指向接收数据的主机地址信息的结构体，也就是该参数指定数据要发送到哪个主机哪个进程

第六个参数addrlen:表示第五个参数所指向内容的长度

返回值：

成功：返回发送成功的数据长度

失败： -1
```c
#include <sys/types.h>
#include <sys/socket.h>
int bind(int sockfd, const struct sockaddr* my_addr, socklen_t addrlen);
```
第一个参数sockfd:正在监听端口的套接口文件描述符，通过socket获得

第二个参数my_addr:需要绑定的IP和端口

第三个参数addrlen：my_addr的结构体的大小

返回值：

成功：0

失败：-1
```c
#include <unistd.h>
int close(int fd);
```
close函数比较简单，只要填入socket产生的fd即可。
##### 3. 搭建UDP通信框架
server：
```c
#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>

#define SERVER_PORT 8888
#define BUFF_LEN 1024

void handle_udp_msg(int fd)
{
    char buf[BUFF_LEN];  //接收缓冲区，1024字节
    socklen_t len;
    int count;
    struct sockaddr_in clent_addr;  //clent_addr用于记录发送方的地址信息
    while(1)
    {
        memset(buf, 0, BUFF_LEN);
        len = sizeof(clent_addr);
        count = recvfrom(fd, buf, BUFF_LEN, 0, (struct sockaddr*)&clent_addr, &len);  //recvfrom是拥塞函数，没有数据就一直拥塞
        if(count == -1)
        {
            printf("recieve data fail!\n");
            return;
        }
        printf("client:%s\n",buf);  //打印client发过来的信息
        memset(buf, 0, BUFF_LEN);
        sprintf(buf, "I have recieved %d bytes data!\n", count);  //回复client
        printf("server:%s\n",buf);  //打印自己发送的信息给
        sendto(fd, buf, BUFF_LEN, 0, (struct sockaddr*)&clent_addr, len);  //发送信息给client，注意使用了clent_addr结构体指针

    }
}


/*
    server:
            socket-->bind-->recvfrom-->sendto-->close
*/

int main(int argc, char* argv[])
{
    int server_fd, ret;
    struct sockaddr_in ser_addr; 

    server_fd = socket(AF_INET, SOCK_DGRAM, 0); //AF_INET:IPV4;SOCK_DGRAM:UDP
    if(server_fd < 0)
    {
        printf("create socket fail!\n");
        return -1;
    }

    memset(&ser_addr, 0, sizeof(ser_addr));
    ser_addr.sin_family = AF_INET;
    ser_addr.sin_addr.s_addr = htonl(INADDR_ANY); //IP地址，需要进行网络序转换，INADDR_ANY：本地地址
    ser_addr.sin_port = htons(SERVER_PORT);  //端口号，需要网络序转换

    ret = bind(server_fd, (struct sockaddr*)&ser_addr, sizeof(ser_addr));
    if(ret < 0)
    {
        printf("socket bind fail!\n");
        return -1;
    }

    handle_udp_msg(server_fd);   //处理接收到的数据

    close(server_fd);
    return 0;
}
```
client：
```c
#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>

#define SERVER_PORT 8888
#define BUFF_LEN 512
#define SERVER_IP "172.0.5.182"


void udp_msg_sender(int fd, struct sockaddr* dst)
{

    socklen_t len;
    struct sockaddr_in src;
    while(1)
    {
        char buf[BUFF_LEN] = "TEST UDP MSG!\n";
        len = sizeof(*dst);
        printf("client:%s\n",buf);  //打印自己发送的信息
        sendto(fd, buf, BUFF_LEN, 0, dst, len);
        memset(buf, 0, BUFF_LEN);
        recvfrom(fd, buf, BUFF_LEN, 0, (struct sockaddr*)&src, &len);  //接收来自server的信息
        printf("server:%s\n",buf);
        sleep(1);  //一秒发送一次消息
    }
}

/*
    client:
            socket-->sendto-->revcfrom-->close
*/

int main(int argc, char* argv[])
{
    int client_fd;
    struct sockaddr_in ser_addr;

    client_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if(client_fd < 0)
    {
        printf("create socket fail!\n");
        return -1;
    }

    memset(&ser_addr, 0, sizeof(ser_addr));
    ser_addr.sin_family = AF_INET;
    //ser_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
    ser_addr.sin_addr.s_addr = htonl(INADDR_ANY);  //注意网络序转换
    ser_addr.sin_port = htons(SERVER_PORT);  //注意网络序转换

    udp_msg_sender(client_fd, (struct sockaddr*)&ser_addr);

    close(client_fd);

    return 0;
}
```
以上的框架用于一台主机不同端口的UDP通信，现象如下：

我们先建立server端，等待服务；然后我们建立client端请求服务。

server端：
![UDP_server_0](https://raw.githubusercontent.com/kaniel/developertools/master/socket/images/udp_server_print.jpg "udp_server_0")
client端：
![UDP_client_0](https://raw.githubusercontent.com/kaniel/developertools/master/socket/images/udp_client_print.jpg "udp_client_0")
自己主机跟自己通信不是很爽，我们想跟其他主机通信怎么搞？很简单，上面client的代码的第49行的注释打开，并注释掉下面那行，在宏定义里填入自己想通信的serverip就可以了。现象如下：

server端：
![UDP_server_1](https://raw.githubusercontent.com/kaniel/developertools/master/socket/images/udp_server_print_1.jpg "udp_server_1")
client端：
![UDP_client_1](https://raw.githubusercontent.com/kaniel/developertools/master/socket/images/udp_client_print_1.jpg "udp_client_1")
这样我们就实现了主机172.0.5.183和172.0.5.182之间的网络通信。

UDP通用框架搭建完成，我们可以利用该框架跟指定主机进行通信了。

如果想学习UDP的基础知识，以上的知识就足够了；如果想继续深入学习一下UDP SOCKET一些高级知识（奇技淫巧），可以花点时间往下看。
