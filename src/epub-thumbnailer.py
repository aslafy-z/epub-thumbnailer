#!/usr/bin/python

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Author: Mariano Simone (http://marianosimone.com)
# Version: 1.0
# Name: epub-thumbnailer
# Description: An implementation of a cover thumbnailer for epub files
# Installation: see 
#

import os
import re
from io import BytesIO
import sys
from xml.dom import minidom
import zipfile
try:
    from PIL import Image
except ImportError:
    import Image

img_ext_regex = re.compile(r'^.*\.(jpg|jpeg|png)$', flags=re.IGNORECASE)
cover_regex = re.compile(r'.*cover.*\.(jpg|jpeg|png)', flags=re.IGNORECASE)

def _get_cover_from_manifest(epub):
    # open the main container
    container = epub.open("META-INF/container.xml")
    container_root = minidom.parseString(container.read())

    # locate the rootfile
    elem = container_root.getElementsByTagName("rootfile")[0]
    rootfile_path = elem.getAttribute("full-path")

    # open the rootfile
    rootfile = epub.open(rootfile_path)
    rootfile_root = minidom.parseString(rootfile.read())

    # find possible cover in meta
    cover_id = None
    for meta in rootfile_root.getElementsByTagName("meta"):
        if meta.getAttribute("name") == "cover":
            cover_id = meta.getAttribute("content")
            break

    # find the manifest element
    manifest = rootfile_root.getElementsByTagName("manifest")[0]
    for item in manifest.getElementsByTagName("item"):
        item_id = item.getAttribute("id")
        item_href = item.getAttribute("href")
        if (item_id == cover_id) or ("cover" in item_id and img_ext_regex.match(item_href.lower())):
            return os.path.join(os.path.dirname(rootfile_path), item_href)

    return None

def _get_cover_by_filename(epub):
    def _choose_best_image(images):
        if images:
            return max(images, key=lambda f: f.file_size)
        return None
    no_matching_images = []
    for fileinfo in epub.filelist:
        if cover_regex.match(fileinfo.filename):
            return fileinfo.filename
        if img_ext_regex.match(fileinfo.filename):
            no_matching_images.append(fileinfo)
    return _choose_best_image(no_matching_images)


extraction_strategies = [
    _get_cover_from_manifest,
    _get_cover_by_filename
]

def _extract_cover(epub, cover_path, output_file, size):
    if cover_path:
        cover = epub.open(cover_path)
        im = Image.open(BytesIO(cover.read()))
        im.thumbnail((size, size), Image.ANTIALIAS)
        if im.mode == "CMYK":
            im = im.convert("RGB")
        im.save(output_file, "PNG")
        return True
    return False


def extract(input_file, output_file, size = 200):
    epub = zipfile.ZipFile(input_file, "r")

    for strategy in extraction_strategies:
        try:
            cover_path = strategy(epub)
            if _extract_cover(epub, cover_path, output_file, size):
                return True
        except Exception as ex:
            print('Failed to 
            return False
