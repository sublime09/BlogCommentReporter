xmlFile='/Users/arash/Downloads/gedicommentss19.wordpress.2019-05-08.xml'
import os
import csv
import sys
from xml.etree import ElementTree

"""This script converts WXR file to a number of plain text files.

WXR stands for "WordPress eXtended RSS", which basically is just a
regular XML file. This script extracts entries from the WXR file into
plain text files. Output format: article name prefixed by date for
posts, article name for pages.

Usage: wxr2txt.py filename [-o output_dir]
Original author: Ruslan Osipov
"""

NAMESPACES = {
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'wp': 'http://wordpress.org/export/1.2/',
        'dc': 'http://purl.org/dc/elements/1.1/',
}
USAGE_STRING = "Usage: wxr2txt.py filename [-o output_dir]"

def main(argv):
    # filename, output_dir = _parse_and_validate_output(argv)
    try:
        data = ElementTree.parse(xmlFile).getroot()
    except ElementTree.ParseError:
        _error("Invalid input file format. Can not parse the input.")
    page_counter, post_counter = 0, 0
    commenters ={}
    for post in data.find('channel').findall('item'):
        post_type = post.find('wp:post_type', namespaces=NAMESPACES).text
        if post_type not in ('post', 'page'):
            continue
        content = post.find('content:encoded', namespaces=NAMESPACES).text
        if content and post_type=='post':
            creator = str(post.find('dc:creator', namespaces=NAMESPACES).text).lower()
            date = post.find('wp:post_date', namespaces=NAMESPACES).text
            #title = post.find('title').text
            date = date.split(' ')[0].replace('-', '')
            # title = re.sub(r'[_]+', '_', re.sub(r'[^a-z0-9+]', '_', title.lower()))
            if int(date) > 20180801:
                if  creator in commenters:
                    commenters[creator] += 1
                else:
                    commenters[creator] = 1
    with open('mycsvfile.csv','wb') as f:
        w = csv.writer(f)
        w.writerow(commenters.keys())
        w.writerow(commenters.values())

def _parse_and_validate_output(argv):
    if len(argv) not in (2, 4):
        _error("Wrong number of arguments.")
    filename = argv[1]
    if not os.path.isfile(filename):
        _error("Input file does not exist (or not enough permissions).")
    output_dir = argv[3] if len(argv) == 4 and argv[2] == '-o' else os.getcwd()
    if not os.path.isdir(output_dir):
        _error("Output directory does not exist (or not enough permissions).")
    return filename, output_dir

def _error(text):
    print text
    print USAGE_STRING
    sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)