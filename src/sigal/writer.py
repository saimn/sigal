# Copyright (c) 2009-2020 - Simon Conseil
# Copyright (c)      2013 - Christophe-Marie Duquesne
# Copyright (c)      2018 - Edwin Steele

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import importlib
import logging
import os
import shutil
import stat
import sys
import types

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, PrefixLoader
from jinja2.exceptions import TemplateNotFound

from . import signals
from .utils import url_from_path

THEMES_PATH = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "themes")
)


class AbstractWriter:
    template_file = None

    def __init__(self, settings, index_title=""):
        self.settings = settings
        self.output_dir = settings["destination"]
        self.theme = settings["theme"]
        self.index_title = index_title
        self.logger = logging.getLogger(__name__)

        # search the theme in sigal/theme if the given one does not exists
        if not os.path.exists(self.theme) or not os.path.exists(
            os.path.join(self.theme, "templates")
        ):
            self.theme = os.path.join(THEMES_PATH, self.theme)
            if not os.path.exists(self.theme):
                raise Exception("Impossible to find the theme %s" % self.theme)

        self.logger.info("Theme  : %s", self.theme)
        theme_relpath = os.path.join(self.theme, "templates")
        default_loader = FileSystemLoader(
            os.path.join(THEMES_PATH, "default", "templates")
        )

        # setup jinja env
        env_options = {"trim_blocks": True, "autoescape": True, "lstrip_blocks": True}

        loaders = [
            FileSystemLoader(theme_relpath),
            default_loader,  # implicit inheritance
            PrefixLoader({"!default": default_loader}),  # explicit one
        ]
        env = Environment(loader=ChoiceLoader(loaders), **env_options)

        # handle optional filters.py
        filters_py = os.path.join(self.theme, "filters.py")
        if os.path.exists(filters_py):
            self.logger.info('Loading filters file: %s', filters_py)
            module_spec = importlib.util.spec_from_file_location('filters', filters_py)
            mod = importlib.util.module_from_spec(module_spec)
            sys.modules['filters'] = mod
            module_spec.loader.exec_module(mod)
            for name in dir(mod):
                if isinstance(getattr(mod, name), types.FunctionType):
                    env.filters[name] = getattr(mod, name)

        try:
            self.template = env.get_template(self.template_file)
        except TemplateNotFound:
            self.logger.error(
                "The template %s was not found in template folder %s.",
                self.template_file,
                theme_relpath,
            )
            sys.exit(1)

        # Copy the theme files in the output dir
        self.theme_path = os.path.join(self.output_dir, "static")
        if os.path.isdir(self.theme_path):
            shutil.rmtree(self.theme_path)

        for static_path in (
            os.path.join(THEMES_PATH, 'default', 'static'),
            os.path.join(self.theme, 'static'),
        ):
            shutil.copytree(static_path, self.theme_path, dirs_exist_ok=True)

            # Ensure that the theme dir is writeable
            for root, _, files in os.walk(self.theme_path):
                st = os.stat(root)
                os.chmod(root, st.st_mode | stat.S_IWUSR)
                for name in files:
                    path = os.path.join(root, name)
                    st = os.stat(path)
                    os.chmod(path, st.st_mode | stat.S_IWUSR)

        if self.settings["user_css"]:
            if not os.path.exists(self.settings["user_css"]):
                self.logger.error(
                    "CSS file %s could not be found", self.settings["user_css"]
                )
            else:
                shutil.copy(self.settings["user_css"], self.theme_path)

    def generate_context(self, album):
        """Generate the context dict for the given path."""

        from . import __url__ as sigal_link

        self.logger.info("Output album : %r", album)
        ctx = {
            "album": album,
            "index_title": self.index_title,
            "settings": self.settings,
            "sigal_link": sigal_link,
            "theme": {
                "name": os.path.basename(self.theme),
                "url": url_from_path(os.path.relpath(self.theme_path, album.dst_path)),
            },
        }
        if self.settings["user_css"]:
            ctx["user_css"] = os.path.basename(self.settings["user_css"])
        return ctx

    def write(self, album):
        """Generate the HTML page and save it."""
        context = self.generate_context(album)
        signals.before_render.send(context)
        page = self.template.render(**context)
        output_file = os.path.join(album.dst_path, album.output_file)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(page)


class AlbumListPageWriter(AbstractWriter):
    """Generate an html page for a directory of albums"""

    template_file = "album_list.html"


class AlbumPageWriter(AbstractWriter):
    """Generate html pages for a directory of images."""

    template_file = "album.html"
