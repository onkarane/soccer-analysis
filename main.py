from utils.scrapper import Scrapper
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

def main():
    url = "https://www.premierleague.com/results?co=1&se=363&cl=4"
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(firefox_options=options)
    Scrapper.main(driver, url)

main()