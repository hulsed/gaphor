import io
import xml.etree.ElementTree as etree

from gaphor.i18n import gettext

NS = {"g": "http://gaphor.sourceforge.net/model"}


def extract_gaphor(fileobj, keywords, comment_tags, options):
    """Extract text from Gaphor models.

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    See also:

    * babel.messages.extract.extract()
    * http://babel.pocoo.org/en/latest/messages.html#writing-extraction-methods
    * https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html
    """
    lineno = None
    funcname = "gettext"
    comments: list[str] = []

    tree = etree.parse(fileobj)

    for node in tree.findall(".//g:name/g:val", NS):
        yield (lineno, funcname, node.text, comments)
    for node in tree.findall(".//g:body/g:val", NS):
        yield (lineno, funcname, node.text, comments)


def translate_model(fileobj):

    tree = etree.parse(fileobj)

    for node in tree.findall(".//g:name/g:val", NS):
        node.text = gettext(node.text or "")
    for node in tree.findall(".//g:body/g:val", NS):
        node.text = gettext(node.text or "")

    return io.StringIO(etree.tostring(tree.getroot(), encoding="unicode", method="xml"))
