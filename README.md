# Read first

This is a useful tool, if you would like to quickly and fully automated download relevant meta-data for a given search string from various scientific databases. These databases include: Arxiv, Scopus, Sciencedirect, ACM digital, IEEE explore, Emerald Insights & Web of Science. 
You will need to create a personal api key for scopus, sciencedirect and arxiv.


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5574867.svg)](https://doi.org/10.5281/zenodo.5574867)

If you use this software please cite as followed:

@software{Hilt_Scientific_research_scraper_2021,
author = {Hilt, Tobias},
doi = {10.5281/zenodo.5574867},
month = {10},
title = {{Scientific research scraper}},
url = {https://github.com/TobiasHilt/scientific_research_scraper},
version = {1.0.1},
year = {2021}
}


## Notebooks:
There are 4 notebook available: 'Quick.ipynb', 'Complete.ipynb', 'Detailed.ipynb' and 'scholar.ipynb'.
### Quick:
As the names allready indicate the first notebook is much quicker because it only searches those databases which are call-able via an api-call (Arxiv, Scopus, Science Direct).The search-query is the same for all databases, if there are no search-results for one (or more) of the databases an error message is printed and the database will be ignored. The results for the databases are joined and can be downloaded as an excel file (date_quick.xlsx)

### Complete:
The second notebook searches all available databases (Science Direct, Scopus, Arxiv, Web of Science, IEEE, ACM digital) and operates remarkably slower. This is due to the fact, that not all databases support api-calls. Therefore these databases need to be scraped via a Webdriver (which operates humanlike and therefore takes a while to run). It is advised to just grab a coffee and return to the computer a few minutes after starting the notebook. Again, the search query is the same for all databases, if there are no search-results for one (or more) of the databases an error is raised and the database will be ignored. When it's finished the results are again joined and can be downloaded as an excel file (date_complete.xlsx)

### Detailed:
The third and last notebook allows you to search each database seperatly and download the results seperatly as well (e.q. date_scopus.xlsx). For a first overview of the researched topic a scrape of Googlescholar is also possible in this notebook.
In this case you need to run a cell for each database seperatly and therefore can edit the search-query and parameters such as count for each database individually. If wanted the results for some (or all) databases can be combined into one big table and be downloaded at the end of the document. By default all of the above databases are concatenated here. If you only wish to join some of them you simply need to delete the rest from the variable 'frames'.

### Scholar:
This notebook can be used for a first scrape of google scholar to get an overview of the topic. 

## How-To:

    - Install and import all necessary packages (git command lines below)
    - Start your desired notebook
    - Edit the Search-String matching your needs ('query'-variable)
    - Edit the desired location to save the documents ('Location'-variable)
    - Edit the api-Keys with your personal key from: https://dev.elsevier.com
    - Start institutional VPN
    - Run the desired cells 
    - Download the results
    
    

## Packages:

##### pip3 install jupyterlab (or just upload the desired .ipynb-file to: https://colab.research.google.com/notebooks/ )
##### pip3 install pandas
##### pip3 install bs4
##### pip3 install selenium
##### pip3 install arxiv
##### pip3 install chromedriver
##### pip3 install openpyxl





    
 
