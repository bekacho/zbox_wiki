#!/usr/bin/env python
#-*- coding:utf-8 -*-
import cgi
import os
import re
import shlex
import shutil
import subprocess

import web

import conf
from commons import zhighlight
from commons import zmarkdown_utils
from commons import zsh_util
from commons import zunicode

osp = os.path


urls = (
    '/', 'WikiIndex',
    '/~([a-zA-Z0-9_\-/.]+)', 'SpecialWikiPage',
    ur'/([a-zA-Z0-9_\-/.%s]+)' % zunicode.CJK_RANGE, 'WikiPage',
)

app = web.application(urls, globals())

#
# template & session
#
if web.config.get('_session') == None:
    session = web.session.Session(app, web.session.DiskStore(conf.sessions_path), initializer={"username": None})
    web.config._session = session
else:
    session = web.config._session

t_globals = {
    'utils' : web.utils,
    "session" : session,
    "ctx" : web.ctx
    }
t_render = web.template.render(conf.templates_path, globals=t_globals)

def session_hook():
    web.ctx.session = session
    web.template.Template.globals['session'] = session
app.add_processor(web.loadhook(session_hook))


def get_recent_change_content():
    recent_change = osp.join(conf.pages_path, conf.RECENT_CHANGE_FILENAME)
    f = file(recent_change)
    buf = web.utils.safeunicode(f.read())
    f.close()

    lis = []
    lines = web.utils.strips(buf, "\n").split("\n")
    lines.reverse()
    content = None

    for i in lines:
        url = osp.join("/", i)
        lis.append('- [%s](%s)' % (i, url))
        content = "\n".join(lis)

    return content

def update_recent_change_list(req_path, mode = "add", check = True):
    req_path = web.utils.safeunicode(req_path)
    recent_change_filepath = osp.join(conf.pages_path, conf.RECENT_CHANGE_FILENAME)

    f = file(recent_change_filepath)
    old_pages = web.utils.safeunicode(f.read()).split('\n')
    f.close()

    if check:
        old_pages = [i for i in old_pages if osp.exists(osp.join(conf.pages_path, "%s.md" % i))]

    def remove_item_from_list(a_list, item):
        return [i for i in a_list if i != item]
    old_pages = remove_item_from_list(old_pages, req_path)

    if mode == "add":
        old_pages.append(req_path)

    new_content = web.utils.safestr('\n'.join(old_pages))
    web.utils.safewrite(recent_change_filepath, new_content)


def get_page_file_or_dir_fullpath_by_req_path(req_path):
    if not req_path.endswith("/"):
        return "%s.md" % osp.join(conf.pages_path, req_path)
    else:
        return osp.join(conf.pages_path, req_path)

def get_dot_idx_content_by_fullpath(fullpath):
    dot_idx_fullpath = osp.join(fullpath, ".index.md")
    return zsh_util.cat(dot_idx_fullpath)

def get_page_file_list_by_fullpath(fullpath):
    parent = osp.dirname(fullpath)
    if osp.isdir(parent):
        buf_list = os.listdir(parent)
        return [web.utils.strips(i, ".md")
                for i in buf_list
                    if not i.startswith('.') and i.endswith(".md")]
    return []

def get_page_file_list_content_by_fullpath(fullpath):
    req_path = fullpath.replace(conf.pages_path, "")
    page_file_list = get_page_file_list_by_fullpath(fullpath)
    lis = []
    for i in page_file_list:
        link = osp.join("/", req_path, i)
        title = link
        lis.append('- [%s](%s)' % (title, link))
    page_file_list_content = "\n".join(lis)
    return page_file_list_content

def delete_page_file_by_fullpath(fullpath):
    if osp.isfile(fullpath):
        os.remove(fullpath)
        return True
    elif osp.isdir(fullpath):
        idx_dot_md = osp.join(fullpath, ".index.md")
        os.remove(idx_dot_md)
        return True
    return False


def update_page_file_index():
    max_level = 4
    output_prefix = "''"
    is_md_p = "^([^.]+?)\.md$"
    filters = [is_md_p]
    resp = zsh_util.tree(top = conf.pages_path, filters = filters,
                     max_level = max_level, output_prefix = output_prefix)

    page_file_idx_fullpath = osp.join(conf.pages_path, conf.PAGE_FILE_INDEX_FILENAME)
    web.utils.safewrite(page_file_idx_fullpath, resp)

def get_page_file_index(update=False):
    if update:
        update_page_file_index()

    page_file_idx_fullpath = osp.join(conf.pages_path, conf.PAGE_FILE_INDEX_FILENAME)
    if not osp.exists(page_file_idx_fullpath):
        update_page_file_index()

    content = zsh_util.cat(page_file_idx_fullpath)

    lines = content.split(os.linesep)

    # strip first line
    lines = lines[1:]
    latest_line = lines[-1]

    p = '(\d+)\s+directories, (\d+)\s+files'
    m_obj = re.match(p, latest_line)

    if m_obj:
#        dires, files = m_obj.groups()
        # strip latest line
        lines = lines[:-2]

    lis = []
    for i in lines:
        i = web.utils.strips(i, ".md")
        url = osp.join("/", i)
        lis.append('- [%s](%s)' % (i, url))
        content = "\n".join(lis)

    return zmarkdown_utils.markdown(content)

def search(keywords):
    """
    http://stackoverflow.com/questions/89228/how-to-call-external-command-in-python

    p_obj = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
    p_obj.wait()
    resp = p_obj.stdout.read().strip()
    """
    matched = " \| ".join(keywords.split())
    if keywords.find("\|") != -1:
        cmd = "cd %s; grep ./ -r -e ' \(%s\) ' | awk -F ':' '{print $1}' | uniq" % (conf.pages_path, matched)
    else:
        cmd = "cd %s; grep ./ -r -e ' %s ' | awk -F ':' '{print $1}' | uniq" % (conf.pages_path, matched)

    matched_lines = os.popen(cmd).read().strip().split("\n")
    return matched_lines

special_path_mapping = {
    'index' : get_page_file_index,
    's' : search,
}


class WikiIndex:
    def GET(self):
        title = "Recnet Changes"
        static_file_prefix = "/static/pages"
        content = get_recent_change_content()
        content = zmarkdown_utils.markdown(content, static_file_prefix)
        return t_render.canvas(title=title, content=content, toolbox=False)


class WikiPage:
    def GET(self, req_path):
        req_path = cgi.escape(req_path)
        inputs = web.input()
        action = inputs.get("action", "read")

        if action and action not in ("edit", "read", "rename", "delete"):
            raise web.BadRequest()

        fullpath = get_page_file_or_dir_fullpath_by_req_path(req_path)
        title = req_path

        if action == "read":
            if osp.isfile(fullpath):
                content = zsh_util.cat(fullpath)

                static_file_prefix = osp.join("/static/pages", osp.dirname(req_path))
            elif osp.isdir(fullpath):
                dot_idx_content = get_dot_idx_content_by_fullpath(fullpath)
                page_file_list_content = get_page_file_list_content_by_fullpath(fullpath)
                content = ""

                if dot_idx_content:
                    content = dot_idx_content
                if page_file_list_content:
                    content = "%s\n\n----\n%s" % (content, page_file_list_content)

                static_file_prefix = osp.join("/static/pages", req_path)
            else:
                web.seeother("/%s?action=edit" % req_path)
                return

            content = zmarkdown_utils.markdown(content, static_file_prefix)
            static_files = '<style type="text/css">\n%s\n</style>' % zhighlight.HIGHLIGHT_STYLE

            return t_render.canvas(title=title, content=content, static_files=static_files)
        elif action == "edit":
            if osp.isfile(fullpath):
                content = zsh_util.cat(fullpath)
            elif osp.isdir(fullpath):
                content = get_dot_idx_content_by_fullpath(fullpath)
            elif not osp.exists(fullpath):
                content = ""
            else:
                raise Exception("unknow path")

            return t_render.editor(title, content)
        elif action == "rename":
            if not osp.exists(fullpath):
                raise web.NotFound()

            return t_render.rename(req_path)
        elif action == "delete":
            if delete_page_file_by_fullpath(fullpath):
                update_recent_change_list(req_path, mode="delete")

            web.seeother("/")
            return

        raise web.BadRequest()

    def POST(self, req_path):
        req_path = cgi.escape(req_path)
        inputs = web.input()
        action = inputs.get("action")

        if action and action not in ("edit", "rename"):
            raise web.BadRequest()

        content = inputs.get("content")
        content = web.utils.safestr(content)

        # NOTICE: if req_path == `users/`, fullpath will be `/path/to/users/`,
        # parent will be `/path/to/users`.

        fullpath = get_page_file_or_dir_fullpath_by_req_path(req_path)

        parent = osp.dirname(fullpath)
        if not osp.exists(parent):
            os.makedirs(parent)

        if action == "edit":
            if not osp.isdir(fullpath):
                web.utils.safewrite(fullpath, content)
            else:
                idx_dot_md_fullpath = osp.join(fullpath, ".index.md")
                web.utils.safewrite(idx_dot_md_fullpath, content)

            update_recent_change_list(req_path)
            web.seeother("/%s" % req_path)
        elif action == "rename":
            new_path = inputs.get("new_path")
            if not new_path:
                raise web.BadRequest()

            old_fullpath = get_page_file_or_dir_fullpath_by_req_path(req_path)
            if osp.isfile(old_fullpath):
                new_fullpath = get_page_file_or_dir_fullpath_by_req_path(new_path)
            elif osp.isdir(old_fullpath):
                new_fullpath = osp.join(conf.pages_path, new_path)
            else:
                raise Exception('unknow path')

            if osp.exists(new_fullpath):
                err_info = "Warning: The page foobar already exists."
                return t_render.rename(req_path, err_info)

            parent = osp.dirname(new_fullpath)
            if not osp.exists(parent):
                os.makedirs(parent)

            shutil.move(old_fullpath, new_fullpath)
            update_recent_change_list(req_path, mode="delete")
            update_recent_change_list(new_path)

            if osp.isfile(new_fullpath):
                web.seeother("/%s" % new_path)
            elif osp.isdir(new_fullpath):
                web.seeother("/%s/" % new_path)

            return

        url = osp.join("/", req_path)
        web.redirect(url)


class SpecialWikiPage:
    def GET(self, req_path):
        f = special_path_mapping.get(req_path)
        inputs = web.input()

        if callable(f):
            if req_path == "index":
                action = inputs.get("action")
                if action == "update":
                    content = f(True)
                else:
                    content = f()
                    
                content = web.utils.safeunicode(content)
                return t_render.canvas(title=req_path, content=content, toolbox=False)
    
        raise web.NotFound()

    def POST(self, req_path):
        f = special_path_mapping.get(req_path)
        inputs = web.input()

        if callable(f):
            keywords = inputs.get("k")
            matched_lines = search(keywords)
            matched_file_list = [web.utils.strips(i, "./") for i in matched_lines]

            lis = []
            for i in matched_file_list:
                i = web.utils.strips(i, ".md")
                url = osp.join("/", i)
                lis.append('- [%s](%s)' % (i, url))
                content = "\n".join(lis)

            content = zmarkdown_utils.markdown(content)
            return t_render.search(keywords=keywords, content=content)
        else:
            raise web.NotFound()

if __name__ == "__main__":
    # Notice:
    # you should remove datas/user.sqlite and sessions/* if you want a clean environment

    if not osp.exists(conf.sessions_path):
        os.mkdir(conf.sessions_path)

    if not osp.exists(conf.pages_path):
        os.mkdir(conf.pages_path)

    recent_change_filepath = osp.join(conf.pages_path, conf.RECENT_CHANGE_FILENAME)
    if not osp.exists(recent_change_filepath):
        web.utils.safewrite(recent_change_filepath, "")

#	web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    app.run()
