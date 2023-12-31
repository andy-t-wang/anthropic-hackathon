from flask_cors import CORS
from PIL import Image
import numpy as np
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
import requests
import os
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from dotenv import load_dotenv
import re
import tinycss2
import cssbeautifier
from flask import Flask, request, jsonify
import json
from flask_cors import CORS, cross_origin  # comment this on deployment
import time

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)
imageFile = 'tmp.png'
options = Options()
options.add_argument("window-size=1600,900")


@app.route('/post_endpoint', methods=['POST'])
def post_example():
    # Assuming the POST data is JSON, let's parse it
    data = request.json

    url = data['url']

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(2)
    driver.get_screenshot_as_file(imageFile)
    page_source = driver.page_source
    colors = get_colors(url)

    # parse HTML using beautiful soup
    soup = bs(page_source, "html.parser")

    # get the CSS files
    css_files = []

    for css in soup.find_all("link"):
        if css.attrs.get("href"):
            # if the link tag has the 'href' attribute
            css_url = urljoin(url, css.attrs.get("href"))
            # check if url ends in .css
            if '.css' in css_url:
                css_files.append(css_url)
                print(css_url)

    list_and_delete_files("./llm_input")

    print("LENGTH before CULL is: ", len(soup.prettify('utf-8')))
    # Tags to be removed
    tags_to_remove = ['script', 'path', 'noscript', 'g', 'meta',
                      'clippath', 'svg', 'link', 'br', 'source', 'video', 'img', "li", "ul", "h1", "h2", "h3", "h4"]

    # Find and remove the specified tags and their contents
    for tag_name in tags_to_remove:
        for tag in soup.find_all(tag_name):
            tag.decompose()  # Removes the tag from the soup

    # Save the HTML to a file
    with open('llm_input/website.html', 'wb') as file:
        # body_tag = soup.find("body")
        file.write(soup.prettify('utf-8'))

    print("LENGTH AFTER CULL is: ", len(soup.prettify('utf-8')))

    print("Total CSS files in the page:", len(css_files))

    with open("css_files.txt", "w") as f:
        for index, css_file in enumerate(css_files):
            if ("http" in css_file):
                download_css_from_url(
                    css_file, filename=f"llm_input/css_file_{index}.css")

    HTML_CSS_STRING = read_and_append_files("./llm_input")

    PROMPT = f"""
    I am going to give you source code for a webpage and I want you to extract the style elements of some values for me.

    These are the main colors in the page for reference (Ordered by most frequent to least frequent).  The colors you return should be in the colors list below.
    {colors}

    Webpage HTML/CSS Code:
    {HTML_CSS_STRING}

    

    Now extract following style values from the code above. I've included the name of the key and the description of the value I want you to extract.
    
    KEY	                   DESCRIPTION
    hero-background-color  The background color of ONLY the first hero section
    hero-text-color	       The color of the text in the first hero section
    card-color	           Background color of the card elements 
    card-border-radius     The border radius of the card elements
    card-text-color        The color of the text on the card elements 
    button-color	       The color of the buttons
    button-border-radius   The border radius of the buttons
    button-text-color      The color of the text on the buttons

    Note: In most cases the first item in the list of colors provided is the hero background color
    Please output ONLY a JSON object with the following keys and values and NOTHING more. 
    Here is an example of the JSON output specification. If there is a gradient for the background value use the gradient

    {{
        hero-background-color: #hex (example), 
        text-color: #hex (example), 
        card-color: #hex (example), 
        card-border-radius: px (example),
        card-text-color: #hex (example),
        button-color: #hex (example), 
        button-border-radius: px (example),
        button-text-color: #hex (example)
    }}

    Only return values found in the code provided.
    Only output the JSON as a string. Such that we could use json.loads on your output and get a dictionary.
    {{
"""

    print("querying claude 2...")

    with open("input_prompt.txt", "w") as f:
        f.write(PROMPT)

    output_json = query_claude_2(f"{HUMAN_PROMPT} {PROMPT} {AI_PROMPT}")

    # Extract content between { and }
    json_match = re.search(r'\{(.*?)\}', output_json, re.DOTALL)

    if json_match:
        json_content = '{' + json_match.group(1) + '}'
        # Parse the JSON content to get a Python dictionary
        parsed_json = json.loads(json_content)

        css = f"""
            body {{
            background: {parsed_json['hero-background-color']};
            color: {parsed_json['hero-text-color']};
            }}

            form {{
            background: {parsed_json['card-color']};
            border-radius: {parsed_json['card-border-radius']};
            color: {parsed_json['card-text-color']};
            }}

            button {{
            background: {parsed_json['button-color']};
            border-radius: {parsed_json['button-border-radius']};
            color: {parsed_json['button-text-color']};
            }}
        """
        with open("stripe/public/temp.css", "w") as css_file:
            css_file.write(css)

        return jsonify({"output_json": parsed_json}), 404
    else:
        print("JSON content not found in the provided string.")
        return jsonify({"output_json": output_json}), 404


def format_css(css_content):
    opts = cssbeautifier.default_options()
    opts.indent_size = 1  # Number of spaces for each indentation
    formatted_css = cssbeautifier.beautify(css_content, opts)
    return formatted_css


def should_keep_rule(rule, desired_properties):
    # Check if the rule is an @media rule, and if so, discard it
    if isinstance(rule, tinycss2.ast.AtRule) and rule.lower_at_keyword in ['media', 'font-face']:
        return False

    # If the rule is not a QualifiedRule (doesn't have selectors and content),
    # keep it by default, as it might be another type of at-rule or a comment.
    if not isinstance(rule, tinycss2.ast.QualifiedRule):
        return True

    # Parse the declarations inside the rule
    declarations = tinycss2.parse_declaration_list(rule.content)

    for declaration in declarations:
        # If any of the desired properties are found in the declarations, keep the rule
        if isinstance(declaration, tinycss2.ast.Declaration) and declaration.lower_name in desired_properties:
            return True

    return False


def filter_css_by_properties(css_content, desired_properties):
    parsed_rules = tinycss2.parse_stylesheet(css_content)

    # Convert property names to lowercase for consistent comparisons
    desired_properties = [prop.lower() for prop in desired_properties]

    # Filter the rules
    cleaned_rules = [rule for rule in parsed_rules if should_keep_rule(
        rule, desired_properties)]

    return tinycss2.serialize(cleaned_rules)


# Load the .env file
load_dotenv()

# Access the values using os.environ
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

print(anthropic_api_key)


anthropic = Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=anthropic_api_key,
)


def query_claude_2(prompt):
    completion = anthropic.completions.create(
        model="claude-2",
        max_tokens_to_sample=256,
        prompt=f"{prompt}",
        temperature=0
    )
    print(completion.completion)
    return completion.completion


def list_and_delete_files(directory_path):
    # List the contents of the directory
    files = os.listdir(directory_path)

    # Check if the directory is empty
    if not files:
        print("Directory is empty.")
        return

    # If not empty, display the files
    print("Contents of the directory:")
    for file in files:
        print(file)

    # Filter out .html and .css files and delete them
    for file in files:
        if file.endswith('.html') or file.endswith('.css'):
            file_path = os.path.join(directory_path, file)
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}. Reason: {e}")


def download_css_from_url(url, filename):
    # Sending a GET request to the URL
    response = requests.get(url)

    # Ensure the request was successful
    if response.status_code == 200:
        # Write the content of the response to a local file
        with open(filename, "wb") as file:
            file.write(response.content)
        print("CSS file downloaded successfully!")
    else:
        print(
            f"Failed to download the CSS file. Status code: {response.status_code}")


def remove_media_selectors(css_content):
    # This regex pattern finds all @media blocks in the CSS
    pattern = r'@media[^{]+\{([\s\S]+?\})\}'
    # Use re.sub to replace all @media blocks with an empty string
    return re.sub(pattern, '', css_content)


def read_and_append_files(folder_path):
    # The files we want to look for
    files_to_check = ["website.html"]

    # Extend the list with possible css files. We assume there could be a large number,
    # but you can reduce the range if you have an upper limit
    for i in range(100):  # assuming a max of 100 css files, adjust as needed
        files_to_check.append(f"css_file_{i}.css")

    # Initialize the result string
    content_str = ""

    for file_name in files_to_check:
        file_path = os.path.join(folder_path, file_name)

        # Check if the file exists
        if os.path.exists(file_path):
            css_content = ""

            with open(file_path, 'r', encoding='utf-8') as file:

                css_content = file.read()

                # Remove all @media selectors
                cleaned_css = remove_media_selectors(css_content)

                if ".css" in file_path:
                    desired_properties = [
                        'color', 'fontsize', 'backgroundcolor', 'borderradius', 'background']
                    print("LENGTH OF CSS BEFORE CLEANING is: ", len(cleaned_css))
                    cleaned_css = filter_css_by_properties(
                        css_content, desired_properties)
                    print("LENGTH OF CSS AFTER CLEANING is: ", len(cleaned_css))

                    cleaned_css = format_css(cleaned_css)

                    content_str += f"CSS File: \n{cleaned_css}" + "\n"
                else:
                    content_str += f"HTML File: \n{cleaned_css}" + "\n"

            # Write the cleaned CSS back to the file (or to a new file if preferred)
            with open(file_path, 'w') as f:
                f.write(cleaned_css)

    return content_str


#####


def palette(img):
    """
    Return palette in descending order of frequency
    """
    arr = np.asarray(img)
    palette, index = np.unique(asvoid(arr).ravel(), return_inverse=True)
    palette = palette.view(arr.dtype).reshape(-1, arr.shape[-1])
    count = np.bincount(index)
    order = np.argsort(count)
    return palette[order[::-1]]


def asvoid(arr):

    arr = np.ascontiguousarray(arr)
    return arr.view(np.dtype((np.void, arr.dtype.itemsize * arr.shape[-1])))


def convertToHex(rgb):
    return '#%02x%02x%02x' % rgb


def get_colors(url):
    # savePrint(imageFile, url)
    img = Image.open(imageFile, 'r').convert('RGB')
    top_ten_colors = palette(img)[:10]
    # print(top_ten_colors)
    colors = [convertToHex(tuple(top_ten_colors[i]))
              for i in range(min(10, len(top_ten_colors)))]
    print(colors)
    return colors


####
if __name__ == "__main__":

    app.run(debug=True)
