### [Sphinx 的介绍和原理探索](https://segmentfault.com/a/1190000004981463)

#### What/Sphinx是什么
定义：Sphinx是一个全文检索引擎。

特性：
```
索引和性能优异
易于集成SQL和XML数据源，并可使用SphinxAPI、SphinxQL或者SphinxSE搜索接口
易于通过分布式搜索进行扩展
高速的索引建立(在当代CPU上，峰值性能可达到10 ~ 15MB/秒)
高性能的搜索 (在1.2G文本，100万条文档上进行搜索，支持高达每秒150~250次查询)
```
#### Why/为什么使用Sphinx
遇到的使用场景
```
遇到一个类似这样的需求：用户可以通过文章标题和文章搜索到一片文章的内容，而文章的标题和文章的内容分别保存在不同的库，而且是跨机房的。
```
#### 可选方案
```
A、直接在数据库实现跨库LIKE查询
优点：简单操作
缺点：效率较低，会造成较大的网络开销

B、结合Sphinx中文分词搜索引擎
优点：效率较高，具有较高的扩展性
缺点：不负责数据存储
```
#### 其他典型使用场景
1、快速、高效、可扩展和核心的全文检索
```
数据量大的时候，比MyISAM和InnoDB都要快。
能对多个源表的混合数据创建索引，不限于单个表上的字段。
能将来自多个索引的搜索结果进行整合。
能根据属性上的附加条件对全文搜索进行优化。
```
2、高效地使用WHERE子句和LIMIT字句

当在多个WHERE条件做SELECT查询时，索引选择性较差或者根本没有索引支持的字段，性能较差。sphinx可以对关键字做索引。区别是，MySQL中，是内部引擎决定使用索引还是全扫描，而sphinx是让你自己选择使用哪一种访问方法。因为sphinx是把数据保存到RAM中，所以sphinx不会做太多的I/O操作。而mysql有一种叫半随机I/O磁盘读，把记录一行一行地读到排序缓冲区里，然后再进行排序，最后丢弃其中的绝大多数行。所以sphinx使用了更少的内存和磁盘I/O。

3、优化GROUP BY查询

在sphinx中的排序和分组都是用固定的内存，它的效率比类似数据集全部可以放在RAM的MySQL查询要稍微高些。

4、并行地产生结果集

sphinx可以让你从相同数据中同时产生几份结果，同样是使用固定量的内存。作为对比，传统SQL方法要么运行两个查询，要么对每个搜索结果集创建一个临时表。而sphinx用一个multi-query机制来完成这项任务。不是一个接一个地发起查询，而是把几个查询做成一个批处理，然后在一个请求里提交。

5、向上扩展和向外扩展

向上扩展：增加CPU/内核、扩展磁盘I/O
向外扩展：多个机器，即分布式sphinx

6、聚合分片数据

适合用在将数据分布在不同物理MySQL服务器间的情况。
例子：有一个1TB大小的表，其中有10亿篇文章，通过用户ID分片到10个MySQL服务器上，在单个用户的查询下当然很快，如果需要实现一个归档分页功能，展示某个用户的所有朋友发表的文章。那么就要同事访问多台MySQL服务器了。这样会很慢。而sphinx只需要创建几个实例，在每个表里映射出经常访问的文章属性，然后就可以进行分页查询了，总共就三行代码的配置。
#### How/如何使用Sphinx
Sphinx工作流程图：
![Sphinx流程图](/Sphinx/images/sphinx流程图.png)

流程图解释：
```
Database：数据源，是Sphinx做索引的数据来源。因为Sphinx是无关存储引擎、数据库的，所以数据源可以是MySQL、PostgreSQL、XML等数据。
Indexer：索引程序，从数据源中获取数据，并将数据生成全文索引。可以根据需求，定期运行Indexer达到定时更新索引的需求。
Searchd：Searchd直接与客户端程序进行对话，并使用Indexer程序构建好的索引来快速地处理搜索查询。
APP：客户端程序。接收来自用户输入的搜索字符串，发送查询给Searchd程序并显示返回结果。
```
#### Sphinx的工作原理
Sphinx的整个工作流程就是Indexer程序到数据库里面提取数据，对数据进行分词，然后根据生成的分词生成单个或多个索引，并将它们传递给searchd程序。然后客户端可以通过API调用进行搜索。

介绍了Sphinx的工作原理后，那么接下来就要让Sphinx工作起来，先来看看Sphinx的配置。
#### Sphinx的配置
##### 数据源配置
先来看一份数据源的配置文件示例：
```
source test
{
      type                    = mysql
  
      sql_host                = 127.0.0.1
      sql_user                = root
      sql_pass                = root
      sql_db                  = test
      sql_port                = 3306    # optional, default is 3306
  
      sql_query_pre           = SET NAMES utf8
      sql_query       　　　　 = SELECT id, name, add_time FROM tbl_test
  
      sql_attr_timestamp      = add_time
  
 　　　sql_query_info_pre      = SET NAMES utf8
      sql_query_info          = SELECT * FROM tbl_test WHERE id=$id
}
```
其中
```
source后面跟着的是数据源的名字，后面做索引的时候会用到；
type：数据源类型，可以为MySQL，PostreSQL，Oracle等等；
sql_host、sql_user、sql_pass、sql_db、sql_port是连接数据库的认证信息；
sql_query_pre：定义查询时的编码
sql_query：数据源配置核心语句，sphinx使用此语句从数据库中拉取数据；
sql_attr_*：索引属性，附加在每个文档上的额外的信息（值），可以在搜索的时候用于过滤和排序。设置了属性之后，在调用Sphinx搜索API时，Sphinx会返回已设置了的属性；
sql_query_info_pre：设置查询编码，如果在命令行下调试出现问号乱码时，可以设置此项；
sql_query_info：设置命令行下返回的信息。
```
##### 索引配置
```
index test_index
{
     source                    = test
     path                      = /usr/local/coreseek/var/data/test
     docinfo                   = extern
     charset_dictpath          = /usr/local/mmseg3/etc/
     charset_type              = zh_cn.utf-8
     ngram_len                 = 1
     ngram_chars               = U+3000..U+2FA1F 
}
```
其中
```
index后面跟的test_index是索引名称
source：数据源名称；
path：索引文件基本名，indexer程序会将这个路径作为前缀生成出索引文件名。例如，属性集会存在/usr/local/sphinx/data/test1.spa中，等等。
docinfo：索引文档属性值存储模式；
charset_dictpath：中文分词时启用词典文件的目录，该目录下必须要有uni.lib词典文件存在；
charset_type：数据编码类型；
ngram_len：分词长度；
ngram_chars：要进行一元字符切分模式认可的有效字符集。
```
##### 中文分词核心配置
一元分词
```
charset_type = utf8
ngram_len = 1
ngram_chars = U+3000..U+2FA1F
```
mmseg分词
```
charset_type = utf8
charset_dictpath = /usr/local/mmseg3/etc/
ngram_len = 0
```
##### 运行示例
数据库数据

![数据示例](/Sphinx/images/sphinx数据示例.png)

使用indexer程序做索引

![indexer](/Sphinx/images/sphinx indexer.png)

查询

![搜索示例](/Sphinx/images/sphinx 搜索示例.png)

可以看到，配置文件中的add_time被返回了，如上图的1所示。而sql_query_info返回的信息如上图的2所示。
```
Sphinx的配置不是很灵活，此处根据工作流程给出各部分的配置，更多的高级配置可以在使用时查阅文档。
```
介绍了Sphinx的配置之后，继续介绍在Sphinx中，负责做索引的程序Indexer是如何做索引的。

sphinx使用配置文件从数据库读出数据之后，就将数据传递给Indexer程序，然后Indexer就会逐条读取记录，根据分词算法对每条记录建立索引，分词算法可以是一元分词/mmseg分词。下面先介绍Indexer做索引时使用的数据结构和算法。
##### source https://segmentfault.com/a/1190000004981463
