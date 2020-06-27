import xmlrpc.client
import ssl
import os
import sys
import logging

# logging.basicConfig(level=logging.INFO)

# 设置 ssl 很重要，否则将报 ssl 错
ssl._create_default_https_context = ssl._create_unverified_context

# dict
config = {
    'user_unique_name': 'deppwang',                                    # 你的用户名，用于拼接文章 url
    'url': 'https://rpc.cnblogs.com/metaweblog/deppwang',              # 你的 MetaWeblog 访问地址
    'username': 'DeppWangXQ',                                          # 你的登录用户名，可能跟上面的不一致
    'password': '12345678',                                            # 你的登录密码
    'local_post_path': '/Users/yanjie/GitHub/HexoBlog/source/_posts/'  # 你的本地博文路径
}


class MetaWeblog:
    def __init__(self, url, username, password):
        self.url, self.username, self.password = url, username, password
        self.proxy = xmlrpc.client.ServerProxy(self.url)

    def getRecentPosts(self, count):
        return self.proxy.metaWeblog.getRecentPosts('', self.username, self.password, count)

    def deletePost(self, post_id):
        return self.proxy.blogger.deletePost('', post_id, self.username, self.password, True)

    def newPost(self, article):
        return self.proxy.metaWeblog.newPost('', self.username, self.password,
                                             dict(title=article['title'], description=article['content'],
                                                  mt_keywords=article['tags']),
                                             True)

    def editPost(self, post_id, article):
        return self.proxy.metaWeblog.editPost(post_id, self.username, self.password,
                                              dict(title=article['title'], description=article['content'],
                                                   mt_keywords=article['tags']),
                                              True)


def set_article(article_path: str) -> dict:
    """ 根据文章路径设置文章（标题、标签和内容）"""

    import re
    from markdown_it import MarkdownIt
    from markdown_it.extensions.front_matter import front_matter_plugin
    from markdown_it.extensions.footnote import footnote_plugin

    with open(article_path, 'rb') as f:
        content = f.read().decode('utf-8')

    # 使用分组
    reg = r'(---(.|[\n])*?---)'

    p = re.compile(reg)
    headers = p.findall(content)

    logging.info('headers: %s', headers)
    if len(headers) < 1:
        raise ValueError('文章 %s 不存在 header 信息块「--- ** ---」，请检查！' % article_path)

    # headers[0] 为 tuple
    header_str = headers[0][0]

    lines = header_str.split('\n')

    title, tags_categories = '', []
    for line in lines:
        # 不使用':', 再替换所有空格为 null，因为可能存在中英文空格
        line_ele = line.split(': ')
        if line_ele[0] == 'title':
            title = line_ele[1].rstrip()

        elif line_ele[0] == 'tags':
            tags = line_ele[1].rstrip()
            tags = tags.replace('[', '')
            tags = tags.replace(']', '')
            tags_categories.append(tags)

        # 将分类也作为标签
        elif line_ele[0] == 'categories':
            categories = line_ele[1].rstrip()
            tags_categories.insert(0, categories)

    separator = ', '
    tags = separator.join(tags_categories)
    logging.info("tags: %s", tags)

    # 只替换第一个
    content = content.replace(header_str, '', 1)

    md = (
        MarkdownIt()
            .use(front_matter_plugin)
            .use(footnote_plugin)
            .enable('image')
            .enable('table')
    )

    # markdown 转换为 HTML
    content = md.render(content)

    # cnblogs-markdown 属性用于代码块样式
    content = '<div class=\"cnblogs-markdown\">%s</div>' % content

    if title is '' or content is '' or tags is '':
        raise ValueError('文章 title、content、tags 均不能为空；\': \'后有空格。请检查！')

    article = {'title': title, 'content': content, 'tags': tags}
    return article


def get_local_modified_file(file_count: int):
    """ 获取指定数量的最近修改文章 """

    import stat
    import datetime as dt

    modified = []

    for root, sub_folders, files in os.walk(config['local_post_path']):
        for file in files:
            try:
                unix_modified_time = os.stat(os.path.join(root, file))[stat.ST_MTIME]
                human_modified_time = dt.datetime.fromtimestamp(unix_modified_time).strftime('%Y%m%dT%H:%M:%S')
                filename = os.path.join(root, file)
                if os.path.splitext(filename)[1] == '.md':
                    modified.append((human_modified_time, filename))
            except:
                pass

    modified.sort(key=lambda a: a[0], reverse=True)
    return modified[0: file_count]


def judge_str_equal(str1, str2):
    """ 判断两个字符串是否相等 """

    str1 = str1.replace(' ', '')
    str2 = str2.replace(' ', '')
    return str1 == str2


def edit_or_new(article_path: str) -> None:
    """ 编辑或新增 """

    blog = MetaWeblog(config['url'], config['username'], config['password'])
    posts = blog.getRecentPosts(100)
    article = set_article(article_path)
    title = article['title']

    # 如果存在，更新，否则新增。接口不提供最近修改时间，所以不能跳过
    exist_flag = 0

    for post in posts:
        # 判断是否含有相同的字符，不直接用等号
        if judge_str_equal(post['title'], title):
            status = blog.editPost(post['postid'], article)
            if status is True:
                print("更新文章「%s」成功，文章地址 https://www.cnblogs.com/%s/p/%s.html" % (title, config['user_unique_name'], post['postid']))
            exist_flag = 1
            break

    if exist_flag == 0:
        id = blog.newPost(article)
        if id is not None:
            print("发布文章「%s」成功，文章地址 https://www.cnblogs.com/%s/p/%s.html" % (title, config['user_unique_name'], id))


def post(count: int) -> None:
    """ 发布指定数量的最新修改文章 """

    modified_files = get_local_modified_file(count)
    for modified_file in modified_files:
        edit_or_new(modified_file[1])


def delete() -> None:
    """ 默认删除最新文章 """

    metaWeblog = MetaWeblog(config['url'], config['username'], config['password'])
    posts = metaWeblog.getRecentPosts(100)
    postid = posts[0]['postid']
    title = posts[0]['title']
    status = metaWeblog.deletePost(postid)
    if status is True:
        print('删除「%s」成功！' % title)
    else:
        print('删除「%s」失败，文章不存在。文章 id 为：%s' % (title, postid))


def main():

    try:

        if len(sys.argv) > 1 and sys.argv[1] == 'delete':
            delete()

        elif len(sys.argv) > 1 and isinstance(int(sys.argv[1]), int):
            print('正在发布 ...')
            logging.info("sys.argv[1]: %s", sys.argv[1])
            post(int(sys.argv[1]))

        else:
            post(1)
    except Exception as err:
        print("错误提示：%s", format(err))
        print('发布失败')
        sys.exit(-1)


if __name__ == '__main__':
    main()
