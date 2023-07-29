from selenium import webdriver
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin

url = "https://www.anthropic.com/"

driver = webdriver.Chrome()
driver.get(url)
page_source = driver.page_source


# parse HTML using beautiful soup
soup = bs(page_source, "html.parser")

# get the CSS files
css_files = []

# Save the HTML to a file
with open('notion.html', 'wb') as file:
    file.write(soup.prettify('utf-8'))

for css in soup.find_all("link"):
    if css.attrs.get("href"):
        # if the link tag has the 'href' attribute
        css_url = urljoin(url, css.attrs.get("href"))
        # check if url ends in .css
        if '.css' in css_url:
            css_files.append(css_url)
print("Total CSS files in the page:", len(css_files))

# # write file links into files
# with open("javascript_files.txt", "w") as f:
#     for js_file in script_files:
#         print(js_file, file=f)

with open("css_files.txt", "w") as f:
    for css_file in css_files:
        print(css_file, file=f)
