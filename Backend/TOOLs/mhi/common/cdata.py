"""
Add CDATA section support to xml.etree.ElementTree

Adapted from http://stackoverflow.com/a/8915039/3690024
"""

import xml.etree.ElementTree as ET

if not hasattr(ET, 'CDATA'):
    _original_serialize_xml = ET._serialize_xml # type:ignore # pylint: disable=protected-access

    def _cdata(node, text):
        element = ET.Element('![CDATA[')
        element.text = text
        node.append(element)

    def _serialize_xml(write, elem, qnames, namespaces,
                       *args, **kwargs):
        if elem.tag == '![CDATA[':
            write("<%s%s]]>" % (elem.tag, elem.text))
        else:
            _original_serialize_xml(write, elem, qnames, namespaces,
                                    *args, **kwargs)

    ET._serialize_xml = ET._serialize['xml'] = _serialize_xml # type:ignore # pylint: disable=protected-access
    ET.CDATA = _cdata # type:ignore
