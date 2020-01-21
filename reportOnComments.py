import os
import csv
import sys
import argparse
from xml.etree import ElementTree

"""
Create a report of blogging comment participation

This script converts WXR file to a number of plain text files.
WXR stands for "WordPress eXtended RSS", which basically is just a
regular XML file. This script extracts entries from the WXR file into
plain text files. Output format: article name prefixed by date for
posts, article name for pages.
Original author: Ruslan Osipov
Updated by: Arash, Patrick Sullivan

usage: reportOnComments.py [-h] input output

positional arguments:
  input       Input XML file from wordpress for creating comment report
  output      Destination csv file for comment report

optional arguments:
  -h, --help  show this help message and exit
"""

# TODO: Improve report.  Average comment length. 

NAMESPACES = {
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'wp': 'http://wordpress.org/export/1.2/',
        'dc': 'http://purl.org/dc/elements/1.1/',
}

def main():
    args = getArgs()
    xmlRoot = args.input
    outputFilename = args.output

    page_counter, post_counter = 0, 0
    commenters ={}
    for post in xmlRoot.find('channel').findall('item'):
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
    with open(outputFilename,'w', newline='') as f:
        w = csv.writer(f)
        for kv in commenters.items():
            print(kv)
            w.writerow(kv)


def validXML(filename):
    try:
        return ElementTree.parse(filename).getroot()
    except ElementTree.ParseError as e:
        print("Error: Could not XML parse", filename, ":", e, file=sys.stderr)
        exit(1)

def getArgs():
    parser = argparse.ArgumentParser(description="Create a report of blogging comment participation")
    parser.add_argument("input", type=validXML, help="Input XML file from wordpress for creating comment report")
    parser.add_argument("output", nargs="?", default="commentReport.csv", help="Destination csv file for comment report")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    main()