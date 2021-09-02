#!/usr/bin/env python3

from time import sleep
import sys
from lxml import html
import requests
import requests_cache
import isbnlib
import yaml


if len(sys.argv) < 4:
    print("Usage: {} withlist_html_file output_file list_name".format(sys.argv[0]))
    sys.exit(1)

source_file = sys.argv[1]
output_file = sys.argv[2]
list_name = sys.argv[3]

session = requests_cache.CachedSession('amazon_cache')

# Amazon blocks requests user agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
}

with open(source_file) as data:
    tree = html.fromstring(data.read())
    books = tree.xpath("//a[starts-with(@id,'itemName_')]")
    result = {list_name: []}

    counter = 0
    for book in books:
        sleep(1)

        sys.stdout.write("\r{}/{}".format(counter, len(books)))
        sys.stdout.flush()

        counter += 1

        book_info = {}
        link = book.attrib['href'].strip()
        book_page = session.get(link, headers=headers)
        title = book.text.strip()
        authors = []

        # Grabbing book details
        book_tree = html.fromstring(book_page.content)
        details = book_tree.xpath("//div[@id = 'detailBullets_feature_div']")
        isbn = None
        for child in details[1][0].iterchildren():
            key = child[0][0].text.strip()
            if "isbn-13" in key.lower():
                isbn = child[0][1].text.strip()
                break
            elif "isbn-10" in key.lower():
                isbn = child[0][1].text.strip()
                break
            # Fallback, some don't have ISBN type
            elif "isbn" in key.lower():
                isbn = child[0][1].text.strip()
                break

        if isbn:
            # Try to get title and authors via ISBN
            book_data = isbnlib.meta(isbn)
            if book_data:
                title = book_data["Title"]
                authors = book_data["Authors"]

            if authors:
                book_info["authors"] = authors

            book_info["isbn"] = isbn

        if title:
            book_info["title"] = title

        if link:
            book_info["link"] = link

        result[list_name].append(book_info)

    with open(output_file, "w") as output:
        output.write(yaml.dump(result, indent=4))
