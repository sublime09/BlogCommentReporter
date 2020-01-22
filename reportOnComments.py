import os
import csv
import sys
import argparse
from datetime import datetime
from collections import Counter
from collections import defaultdict
from xml.etree import ElementTree

"""Create a report of blogging comment participation

This script reads an exported WordPress XML file (aka 'WXR').  
It then finds all comments on all posts and creates a tally
for the number of comments that each username created on posts.  

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

OLDEST_POST = datetime(2015, 10, 1)

NAMESPACES = {
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'wp': 'http://wordpress.org/export/1.2/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'excerpt': "http://wordpress.org/export/1.2/excerpt/", 
        'wfw': "http://wellformedweb.org/CommentAPI/",
}

class BloggerRow():
    def __init__(self):
        self.username = None
        self.postCount = 0
        self.postTotalLen = 0
        self.commentCount = 0
        self.commentTotalLen = 0
        self.replyCount = 0
        self.replyTotalLen = 0

def main():
    args = getArgs()
    xmlRoot = args.input
    outputFilename = args.output

    typeCounter = Counter()
    rows = defaultdict(BloggerRow)

    for post in xmlRoot.find('channel').findall('item'):
        post_type = post.find('wp:post_type', namespaces=NAMESPACES).text
        typeCounter[post_type] += 1

        if post_type != 'post':
            continue

        title = post.find('title').text
        creator = str(post.find('dc:creator', namespaces=NAMESPACES).text)
        dateStr = post.find('wp:post_date', namespaces=NAMESPACES).text
        date = datetime.fromisoformat(dateStr)
        postContent = post.find('content:encoded', namespaces=NAMESPACES).text

        if date < OLDEST_POST:
            continue
        if postContent is None:
            continue

        rows[creator].username = creator
        rows[creator].postCount += 1
        rows[creator].postTotalLen += len(postContent)

        for comment in post.findall("wp:comment", namespaces=NAMESPACES):
            commenter = comment.find('wp:comment_author_email', namespaces=NAMESPACES).text
            commenter = commenter.split('@')[0]
            commentText = comment.find('wp:comment_content', namespaces=NAMESPACES).text
            commentParentId = int(comment.find('wp:comment_parent', namespaces=NAMESPACES).text)

            rows[commenter].username = commenter
            if commentParentId == 0:
                rows[commenter].commentCount += 1
                rows[commenter].commentTotalLen += len(commentText)
            else:
                rows[commenter].replyCount += 1
                rows[commenter].replyTotalLen += len(commentText)

    print(typeCounter)

    with open(outputFilename,'w', newline='') as f:
        w = csv.writer(f)
        headRow = True

        for bloggerRow in rows.values():
            if headRow:
                colHeaders = vars(bloggerRow).keys()
                w.writerow(colHeaders)
                headRow = False
            rowVals = vars(bloggerRow).values()
            w.writerow(rowVals)
            

def validXML(filename):
    try:
        return ElementTree.parse(filename).getroot()
    except ElementTree.ParseError as e:
        print("Error: Could not parse XML of ", filename, ":", e, file=sys.stderr)
        exit(1)

def getArgs():
    parser = argparse.ArgumentParser(description="Create a report of blogging comment participation")
    parser.add_argument("input", type=validXML, help="Input XML file from wordpress for creating comment report")
    parser.add_argument("output", nargs="?", default="commentReport.csv", help="Destination csv file for comment report")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    main()