# cnblogs-post

一个发布文章到博客园的 Python 脚本

## 功能

1. 无需页面操作，不止新增，还可更新
2. 可一次发布多篇文章
3. 可删除文章

## 使用

### 配置

博客园 -> 管理 -> 设置 -> 允许 MetaWeblog 博客客户端访问

![image-20200620185444059](https://deppwang.oss-cn-beijing.aliyuncs.com/blog/2020-06-20-105444.png)

在 `cnblogs-post.py` 中配置：

```Python
config = {
    'user_unique_name': 'deppwang',                                     # 你的用户名，用于拼接文章 url
    'url': 'https://rpc.cnblogs.com/metaweblog/deppwang',               # 你的 MetaWeblog 访问地址
    'username': 'DeppWangXQ',                                           # 你的登录用户名，可能跟上面的用户名不一致
    'password': '12345678'                                              # 你的登录密码
    'local_post_path': '/Users/yanjie/GitHub/HexoBlog/source/_posts/'   # 你的本地博文路径
}
```

在文章开头，添加文章信息块，至少需要包括 `title` 和 `tags`，格式如下：

```Markdown
---
title: 一个可编辑与新增博客园文章的 Python 脚本
english_title: a-python-script-to-edit-and-add-cnblogs-posts
date: 2020-06-20 20:48:37
tags: 博客园
categories: Tools
---
正文开始 ...
```

安装 [markdown-it-py](https://github.com/executablebooks/markdown-it-py)，用于将 Markdown 转换为 HTML

```shell
pip install markdown-it-py
```

### 运行脚本发布或更新

```shell
python3 cnblogs-post.py [count]   # macOS/Linux
python cnblogs-post.py [count]    # Windows
```

- 默认只操作最近修改文章，但也可以指定文章数量（count）
- 脚本根据文章名称来判断是否已经发布，如果已经发布，更新，否则新增。

![image-20200627223237894](https://deppwang.oss-cn-beijing.aliyuncs.com/blog/2020-06-27-143238.png)

### 运行脚本删除

```shell
python3 cnblogs-post.py delete    # macOS/Linux
python cnblogs-post.py delete     # Windows
```

- 默认删除最近发布文章

## 核心代码

```Python
import xmlrpc.client
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

config = {
    'url': 'https://rpc.cnblogs.com/metaweblog/deppwang',
    'username': '',  # username 为登录用户名
    'password': ''
}

class MetaWeblog:
    def __init__(self, url, username, password):
        self.url, self.username, self.password = url, username, password
        self.proxy = xmlrpc.client.ServerProxy(self.url)

    def getRecentPosts(self, count):
        return self.proxy.metaWeblog.getRecentPosts('', self.username, self.password, count)

def main():
    metaWeblog = MetaWeblog(config['url'], config['username'], config['password'])
    posts = metaWeblog.getRecentPosts(100)
```

## 一文多发

脚本只实现发布、更新文章到博客园。如果想实现一文多发，可自己开发相应脚本，方法为[找到相应接口](https://depp.wang/2020/06/11/how-to-find-the-api-of-a-website-eg-note-youdao-com/)，使用模拟操作接口的方式实现

我个人没有一文多发的需求，感兴趣的同学可以做做

## 出发点

我的[个人独立博客](https//depp.wang)是基于 Hexo 搭建的，因为小站，Google 搜索引擎收录文章比较慢，还搜不到

为了解决这个问题，希望把文章也顺便发布到博客平台[博客园](https://www.cnblogs.com/deppwang)上。但不想每次手动复制粘贴，打算利用脚本实现，希望除了发布，并且还能更新文章。原来打算[找到博客园接口](https://depp.wang/2020/06/11/how-to-find-the-api-of-a-website-eg-note-youdao-com/)，模拟操作接口实现。搜索发现博客园提供了 [MetaWeblog 接口](https://rpc.cnblogs.com/metaweblog/deppwang)，所以利用接口，开发了这个脚本。

