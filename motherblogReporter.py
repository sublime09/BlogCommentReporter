import sys
import argparse
import csv
import re

from os import path
from os import makedirs
from os import getcwd
from os import walk

from xml.etree import ElementTree
from bs4 import BeautifulSoup

from contextlib import closing
from urllib.request import urlopen
from urllib.error import HTTPError
from time import sleep

"""Create a report of blogging comment participation

This script reads an exported WordPress XML file (aka 'WXR').  
It then finds all comments on all posts and creates a tally
for the number of comments that each username created on posts.  

Original author: Ruslan Osipov
Updated by: Arash, Patrick Sullivan

For usage, see: python motherblogReporter.py --help
"""

def main():
	args = getArgs()
	print("Scanning XML for posts...")
	postReport(args)
	print("Downloading posts ...")
	downloadPosts(args)
	print("Scanning comments of posts...")
	commentReport(args)
	print("DONE! See results in output CSV files")


def postReport(args):
	NS = {  #  NAMESPACES needed for wordpress xml parsing
		'content': 'http://purl.org/rss/1.0/modules/content/',
		'wp': 'http://wordpress.org/export/1.2/',
		'dc': 'http://purl.org/dc/elements/1.1/',
		'excerpt': "http://wordpress.org/export/1.2/excerpt/", 
		'wfw': "http://wellformedweb.org/CommentAPI/",
	}

	xmlRoot = args.blogXML
	items = xmlRoot.findall(".//channel/item", NS)
	assert len(items) > 0, "NO ITEMS in the xml???"
	posts = [p for p in items if p.find('wp:post_type', NS).text == 'post']
	published = [p for p in posts if p.find('wp:status', NS).text == 'publish']
	posts = published
	print("Posts:", len(posts))
	assert None not in posts
	authors = [str(post.find('dc:creator', NS).text) for post in posts]
	print("Unique Authors:", ' '.join(set(authors)))
	titles = [post.find('title').text for post in posts]
	assert None not in titles
	dates = [post.find('wp:post_date', NS).text for post in posts]
	postLinks = [post.find(".//link", NS).text for post in posts]
	contents = [post.find('content:encoded', NS).text for post in posts]
	# cLens = [len(str(c)) for c in contents] # old version that was not accurate
	cLens = [len(BeautifulSoup(str(c), "lxml").get_text()) for c in contents]
	assert 0 not in cLens

	with open(args.postReport,'w', newline='') as f:
		w = csv.writer(f)
		header = "author date length title link"
		w.writerow(header.split())
		for row in zip(authors, dates, cLens, titles, postLinks):
			if row[2] <= len(str(None)): continue
			w.writerow(row)


def readPostsReport(args):
	report = None
	with open(args.postReport,'r', newline='') as f:
		reader = csv.reader(f)
		report = [row for row in reader]
	header = report.pop(0)
	return header, report


def downloadPosts(args):
	header, report = readPostsReport(args)
	postsDir = path.join(getcwd(), args.postData)

	for rowNum, row in enumerate(report):
		author = row[header.index("author")]
		url = row[header.index("link")]
		title = row[header.index("title")]

		cleanTitle = title.replace("/", "-").replace('\\', "-")
		shortTitle = str(rowNum) + "-" +cleanTitle[:15].strip()

		authorDir = path.join(postsDir, author)
		postFilePath = path.join(authorDir, shortTitle + ".html")
		shortPath = postFilePath.lstrip(getcwd())
		
		if path.isfile(postFilePath):
			if (args.verbose): print("Already cached:", shortPath)
			continue
		try:
			if (args.verbose): print("Souping:", url)
			soup = getSoup(url)
			makedirs(authorDir, exist_ok=True)
			with open(postFilePath, 'w') as f:
				f.write(str(soup))
			print("NEW written:", shortPath)
		except AssertionError as e:
			print(e)
			print("ERROR: SKIPPED:", url)


def getSoup(url):
	content = None
	sleep(1)
	try:
		with closing(urlopen(url)) as resp:
			assert resp.status == 200, "Bad response status!"
			contentType = str(resp.headers['Content-Type']).lower()
			assert 'html' in contentType, "Not HTML content!"
			content = resp.read()
	except HTTPError as e:
		assert False, "Assert:" + str(e)
	assert len(content) > 0, "No content in response!"
	return BeautifulSoup(content, "html.parser")


def walkDirFiles(top):
	for root, dirs, files in walk(top):
	    for name in files:
	        yield path.join(root, name)


def commentReport(args):
	postsDir = path.join(getcwd(), args.postData)
	fpaths = [fp for fp in walkDirFiles(postsDir)]
	soup = None
	commenters, commLens = [], []

	for filepath in fpaths:
		shortPath = filepath.lstrip(getcwd())
		if (args.verbose): print("Souping and Comment Searching:", shortPath)
		with open(filepath, 'r') as f:
			soup = BeautifulSoup(f, "html.parser")
		assert soup is not None, "TERRIBLE SOUP!!!"
		commArea = soup.select("div#comments,div#commentsbox")
		assert len(commArea) == 1, "Multiple comment areas???"
		commArea = commArea[0]
		assert commArea is not None, "ERROR: No commArea!!!"

		# commAuts = re.match(str(commArea), r"comment-author-[\S\"\']*")
		commContent = commArea.select("div.comment-content,div.comment-body")
		contentLens = [len(c.get_text()) for c in commContent]

		commVcards = commArea.find_all("div", class_='vcard')
		commAuts = [vc.text.strip().replace(" says:", "") for vc in commVcards]
		commAuts = [re.sub( r" on .*? at .*? said:", "", a) for a in commAuts]

		try:
			assert len(commContent) == len(commAuts), "COMMENT MISMATCH"
		except Exception as e:
			print(e)
			breakpoint()

		commenters.extend(commAuts)
		commLens.extend(contentLens)

	with open(args.commentReport, 'w', newline='') as f:
		w = csv.writer(f)
		w.writerow("Commenter Length".split())
		for row in zip(commenters, commLens):
			w.writerow(row)


def validXML(filename):
	try:
		return ElementTree.parse(filename).getroot()
	except ElementTree.ParseError as e:
		print("Error: Could not parse XML of ", filename, ":", e, file=sys.stderr)
		raise e


def getArgs():
	desc = "Creates reports of blogging comment participation"
	parser = argparse.ArgumentParser(description=desc)
	h = "The XML file exported from a wordpress motherblog"
	parser.add_argument("blogXML", type=validXML, help=h)
	h = "Destination csv file for post report"
	parser.add_argument("--postReport", default="postReport.csv", help=h)
	h = "Folder where posts are downloaded / analyzed"
	parser.add_argument("--postData", default="postData", help=h)
	h = "Destination csv file for comment report"
	parser.add_argument("--commentReport", default="commentReport.csv", help=h)
	h = "Verbose output"
	parser.add_argument("-v", "--verbose", action="store_false", help=h)
	return parser.parse_args()


if __name__ == "__main__":
	main()
