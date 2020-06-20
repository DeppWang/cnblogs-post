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
    'url': 'https://rpc.cnblogs.com/metaweblog/deppwang',
    'username': 'DeppWangXQ',  # username 为登录用户名，可能跟上面的不一致
    'password': '12345678',
    'local_post_path': '/Users/yanjie/GitHub/HexoBlog/source/_posts/'
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


def set_article(article_path):
    import re
    from markdown_it import MarkdownIt
    from markdown_it.extensions.front_matter import front_matter_plugin
    from markdown_it.extensions.footnote import footnote_plugin

    # logging.info(article_path)

    with open(article_path, 'rb') as f:
        content = f.read().decode('utf-8')

    reg = r'(---(.|[\n])*?---)'
    p = re.compile(reg)
    headers = p.findall(content)
    if len(headers) < 1:
        raise ValueError('文章不存在 header --- ** ---，请检查！')

    header_str = headers[0][0]

    lines = header_str.split('\n')

    title, tags_categories = '', []
    for line in lines:
        line_ele = line.split(':')
        if line_ele[0] == 'title':
            title = line_ele[1].replace(' ', '')
            # logging.info(title)

        elif line_ele[0] == 'tags':
            tags = line_ele[1].replace(' ', '')
            tags = tags.replace('[', '')
            tags = tags.replace(']', '')
            # logging.info(tags)
            tags_categories.append(tags)

        # 将分类也作为标签
        elif line_ele[0] == 'categories':
            categories = line_ele[1].replace(' ', '')
            tags_categories.insert(0, categories)

    separator = ', '
    tags = separator.join(tags_categories)
    # logging.info(tags)

    content = content.replace(header_str, '')

    md = (
        MarkdownIt()
            .use(front_matter_plugin)
            .use(footnote_plugin)
            .enable('image')
            .enable('table')
    )

    content = md.render(content)
    # cnblogs-markdown 属性用于代码块样式
    content = '<div class=\"cnblogs-markdown\">%s</div>' % content
    # print(content)
    if title is '' or content is '' or tags is '':
        raise ValueError('文章 title 或 content 或 tags 为空，请检查！')

    article = {'title': title, 'content': content, 'tags': tags}
    return article


def find_last_modified_file(file_count):
    import stat
    import datetime as dt

    modified = []

    for root, sub_folders, files in os.walk(config['local_post_path']):
        for file in files:
            try:
                unix_modified_time = os.stat(os.path.join(root, file))[stat.ST_MTIME]
                human_modified_time = dt.datetime.fromtimestamp(unix_modified_time).strftime('%Y%m%dT%H:%M:%S')
                filename = os.path.join(root, file)
                # logging.info(os.path.splitext(filename)[1])
                if os.path.splitext(filename)[1] == '.md':
                    modified.append((human_modified_time, filename))
            except:
                pass

    modified.sort(key=lambda a: a[0], reverse=True)
    # logging.info(modified[0: file_count])
    return modified[0: file_count]


def edit_or_new(metaWeblog, posts, filename):
    try:
        article = set_article(filename)
    except Exception as err:
        print(format(err))
        sys.exit(-1)

    # 如果存在，更新，否则新增
    exist_flag = 0

    for post in posts:
        if post['title'] == article['title']:
            status = metaWeblog.editPost(post['postid'], article)
            if status is True:
                # logging.info(article['title'])
                print("更新文章「%s」成功" % article['title'])
            # logging.info(status)
            exist_flag = 1
            break

    if exist_flag == 0:
        id = metaWeblog.newPost(article)
        if id is not None:
            print("发布文章成功，文章 id 为 %s" % id)


def main():

    metaWeblog = MetaWeblog(config['url'], config['username'], config['password'])

    posts = metaWeblog.getRecentPosts(100)

    if len(sys.argv) > 1 and sys.argv[1] == 'delete':
        postid = posts[0]['postid']
        title = posts[0]['title']
        status = metaWeblog.deletePost(postid)
        if status is True:
            print('删除 %s 成功！' % title)
        else:
            print('删除 %s 失败，不存在。文章 id 为：%s' % (title, postid))
        sys.exit(-1)

    if len(sys.argv) > 1 and isinstance(int(sys.argv[1]), int):
        logging.info("sys.argv[1]: %s", sys.argv[1])
        modified_files = find_last_modified_file(int(sys.argv[1]))
        for modified_file in modified_files:
            edit_or_new(metaWeblog, posts, modified_file[1])

        sys.exit(-1)

    filename = find_last_modified_file(1)[0][1]
    edit_or_new(metaWeblog, posts, filename)


if __name__ == '__main__':
    main()
