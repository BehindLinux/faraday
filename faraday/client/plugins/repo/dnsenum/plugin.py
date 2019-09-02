#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

'''
from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement
from faraday.client.plugins import core
from faraday.client.model import api
import re
import os
import sys

try:
    import xml.etree.cElementTree as ET
    import xml.etree.ElementTree as ET_ORIG
    ETREE_VERSION = ET_ORIG.VERSION
except ImportError:
    import xml.etree.ElementTree as ET
    ETREE_VERSION = ET.VERSION

ETREE_VERSION = [int(i) for i in ETREE_VERSION.split(".")]

current_path = os.path.abspath(os.getcwd())

__author__ = "Francisco Amato"
__copyright__ = "Copyright (c) 2013, Infobyte LLC"
__credits__ = ["Francisco Amato"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"


class DnsenumXmlParser:
    """
    The objective of this class is to parse an xml file generated by the dnsenum tool.

    TODO: Handle errors.
    TODO: Test dnsenum output version. Handle what happens if the parser doesn't support it.
    TODO: Test cases.

    @param dnsenum_xml_filepath A proper xml generated by dnsenum
    """

    def __init__(self, xml_output):
        tree = self.parse_xml(xml_output)

        if tree:
            self.items = [data for data in self.get_items(tree)]
        else:
            self.items = []

    def parse_xml(self, xml_output):
        """
        Open and parse an xml file.

        TODO: Write custom parser to just read the nodes that we need instead of
        reading the whole file.

        @return xml_tree An xml tree instance. None if error.
        """
        try:
            tree = ET.fromstring(xml_output)
        except SyntaxError as err:
            print("SyntaxError: %s. %s" % (err, xml_output))
            return None

        return tree

    def get_items(self, tree):
        """
        @return items A list of Host instances
        """
        bugtype = ''

        node = tree.findall('testdata')[0]
        for hostnode in node.findall('host'):
            yield Item(hostnode)


def get_attrib_from_subnode(xml_node, subnode_xpath_expr, attrib_name):
    """
    Finds a subnode in the item node and the retrieves a value from it

    @return An attribute value
    """
    global ETREE_VERSION
    node = None

    if ETREE_VERSION[0] <= 1 and ETREE_VERSION[1] < 3:

        match_obj = re.search(
            "([^\@]+?)\[\@([^=]*?)=\'([^\']*?)\'", subnode_xpath_expr)
        if match_obj is not None:
            node_to_find = match_obj.group(1)
            xpath_attrib = match_obj.group(2)
            xpath_value = match_obj.group(3)
            for node_found in xml_node.findall(node_to_find):
                if node_found.attrib[xpath_attrib] == xpath_value:
                    node = node_found
                    break
        else:
            node = xml_node.find(subnode_xpath_expr)

    else:
        node = xml_node.find(subnode_xpath_expr)

    if node is not None:
        return node.get(attrib_name)

    return None


class Item:
    """
    An abstract representation of a Item

    TODO: Consider evaluating the attributes lazily
    TODO: Write what's expected to be present in the nodes
    TODO: Refactor both Host and the Port clases?

    @param item_node A item_node taken from an dnsenum xml tree
    """

    def __init__(self, item_node):
        self.node = item_node

        self.hostname = self.get_text_from_subnode('hostname')
        self.ip = self.node.text

    def do_clean(self, value):
        myreturn = ""
        if value is not None:
            myreturn = re.sub("\n", "", value)
        return myreturn

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """
        sub_node = self.node.find(subnode_xpath_expr)
        if sub_node is not None:
            return sub_node.text

        return None


class DnsenumPlugin(core.PluginBase):
    """
    Example plugin to parse dnsenum output.
    """

    def __init__(self):

        core.PluginBase.__init__(self)
        self.id = "Dnsenum"
        self.name = "Dnsenum XML Output Plugin"
        self.plugin_version = "0.0.1"
        self.version = "1.2.2"
        self.options = None
        self._current_output = None
        self._command_regex = re.compile(
            r'^(sudo dnsenum|dnsenum|sudo dnsenum\.pl|dnsenum\.pl|perl dnsenum\.pl|\.\/dnsenum\.pl).*?')

        global current_path

        self._output_file_path = os.path.join(
            self.data_path,
            "dnsenum_output-%s.xml" % self._rid)

    def parseOutputString(self, output, debug=False):
        """
        This method will discard the output the shell sends, it will read it from
        the xml where it expects it to be present.

        NOTE: if 'debug' is true then it is being run from a test case and the
        output being sent is valid.
        """

        parser = DnsenumXmlParser(output)

        for item in parser.items:
            h_id = self.createAndAddHost(item.ip)
            i_id = self.createAndAddInterface(
                h_id,
                item.ip,
                ipv4_address=item.ip,
                hostname_resolution=[item.hostname])

        del parser

    xml_arg_re = re.compile(r"^.*(-o\s*[^\s]+).*$")

    def processCommandString(self, username, current_path, command_string):
        """
        Adds the -oX parameter to get xml output to the command string that the
        user has set.
        """

        arg_match = self.xml_arg_re.match(command_string)

        if arg_match is None:
            return re.sub(
                r"(^.*?dnsenum(\.pl)?)",
                r"\1 -o %s" % self._output_file_path,
                command_string)
        else:
            return re.sub(arg_match.group(1),
                          r"-o %s" % self._output_file_path,
                          command_string)

    def setHost(self):
        pass


def createPlugin():
    return DnsenumPlugin()

if __name__ == '__main__':
    parser = DnsenumXmlParser(sys.argv[1])
    for item in parser.items:
        if item.status == 'up':
            print(item)
# I'm Py3