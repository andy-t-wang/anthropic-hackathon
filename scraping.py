from selenium import webdriver
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
import requests
import os 
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Access the values using os.environ
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

print(anthropic_api_key) 

url = "https://www.anthropic.com/"

anthropic = Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=anthropic_api_key,
)

def query_claude_2(prompt): 
    completion = anthropic.completions.create(
        model="claude-2",
        max_tokens_to_sample=100000,
        prompt=f"{prompt}",
    )
    print(completion.completion)
    return completion.completion


driver = webdriver.Chrome()
driver.get(url)
page_source = driver.page_source


# parse HTML using beautiful soup
soup = bs(page_source, "html.parser")

# get the CSS files
css_files = []


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


list_and_delete_files("./llm_input")

# Save the HTML to a file
with open('llm_input/website.html', 'wb') as file:
    body_tag = soup.find("body")
    file.write(body_tag.prettify('utf-8'))

for css in soup.find_all("link"):
    if css.attrs.get("href"):
        # if the link tag has the 'href' attribute
        css_url = urljoin(url, css.attrs.get("href"))
        # check if url ends in .css
        if '.css' in css_url:
            css_files.append(css_url)
print("Total CSS files in the page:", len(css_files))

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
        print(f"Failed to download the CSS file. Status code: {response.status_code}")


with open("css_files.txt", "w") as f:
    for index, css_file in enumerate(css_files):
        print(css_file, file=f)
        if ("http" in css_file):
            download_css_from_url(css_file, filename=f"llm_input/css_file_{index}.css")

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
            with open(file_path, 'r', encoding='utf-8') as file:

                content_str += file.read() + "\n"

    return content_str

HTML_CSS_STRING = read_and_append_files("./llm_input")


PROMPT = """
You are helping to determine the style of a website based on its HTML and CSS. 

This will be used to style a new component that is being added. 

Your goal is to determine values for the following variable keys, the output values of which are in standard CSS. 

VARIABLE	DESCRIPTION
fontFamily	The font family used throughout Elements. Elements supports custom fonts by passing the fonts option to the Elements group.
fontSizeBase	The font size that’s set on the root of the Element. By default, other font size variables like fontSizeXs or fontSizeSm are scaled from this value using rem units.
spacingUnit	The base spacing unit that all other spacing is derived from. Increase or decrease this value to make your layout more or less spacious.
borderRadius	The border radius used for tabs, inputs, and other components in the Element.
colorPrimary	A primary color used throughout the Element. Set this to your primary brand color.
colorBackground	The color used for the background of inputs, tabs, and other components in the Element.
colorText	The default text color used in the Element.
colorDanger	A color used to indicate errors or destructive actions in the Element.

Please output ONLY a JSON object with the following keys and values: 

{
fontFamily: VALUE, 
fontSizeBase: VALUE, 
spacingUnit: VALUE, 
borderRadius: VALUE, 
colorPrimary: VALUE, 
colorBackground: VALUE, 
colorText: VALUE, 
colorDanger: VALUE,
componentBackgroundColor: VALUE (the background of the entire page we're adding)
componentButtonColor: VALUE  (a button on the webpage we're adding)
buttonRadius: VALUE (the radius of the button)
}

If you can't determine a value for a key, OMIT that key in the output JSON. I am appending the HTML and CSS files directly below. 

We have to choose a background color for the component and a button color. Also provide a JSON file with your suggestions based on the HTML and CSS for these two. 

The output set of these values should only be present in the CSS file. 
"""


PROMPT += HTML_CSS_STRING[:4*70000]


print("querying claude 2...")

output_json = query_claude_2(f"{HUMAN_PROMPT} {PROMPT} {AI_PROMPT}")

print("done")
print("output json is: ", output_json)