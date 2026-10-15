[我把公司的 Redis 打爆了！_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1uPixBVEfC?spm_id_from=333.788.videopod.sections&vd_source=68074f1132646c64dff4aca26e69ae02)

用故事讲Redis误区的视频，把常见坑过了一遍。

**破坏连接池**：频繁新建TCP连接（三次握手+四次挥手）→CPU飙升，Redis连接数被占满。

**取消批处理**：`m`set和pipeline不用，改for循环逐条set→网络往返时间暴增，但Redis处理能力没变。

**大Key与慢查询**：大list用`del`删除，或`keys *`遍历全量Key→单线程阻塞，其他命令排队。更隐蔽的是让大量Key同时过期，触发主动删除机制持续扫描，同样占满主线程。

**破坏缓存**：穿透（查不存在数据）、击穿（热点Key突然过期）、雪崩（大批Key同时失效）→压力全打到数据库。

**内存写满**：不设过期时间，淘汰策略设`noeviction`→内存吃满后拒绝写入，业务报错。

**结局**：Redis挂掉→请求全打数据库→响应变慢请求堆积→业务崩溃。

Tags: #Redis #连接池 #批处理 #大Key #慢查询 #穿透 #击穿 #雪崩 #noeviction 
