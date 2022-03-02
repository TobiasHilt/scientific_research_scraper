import arxiv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import pandas as pd
import requests
from requests.structures import CaseInsensitiveDict
import random
import re
import numpy as np
import locale
from webdriver_manager.chrome import ChromeDriverManager
import json

################################################## Arxiv ###################################################### 


def scrape_arxiv(arxiv_query,count): 
    records_arxiv = []
    if count == "max":
        search = arxiv.Search(
                arxiv_query,
                sort_by = arxiv.SortCriterion.SubmittedDate,
                sort_order = arxiv.SortOrder.Descending
                )

        
    else:
        search = arxiv.Search(
                arxiv_query,
                max_results = count,
                sort_by = arxiv.SortCriterion.SubmittedDate,
                sort_order = arxiv.SortOrder.Descending
                )

    
    
 
    for result in search.results():
        
          records_arxiv.append({  #Liste mit Ergebnissen erweitern
                "Title" : result.title,
                "Author" : result.authors,
                "Date" : result.published,
                "Publisher": '-',
                "Abstract" : result.summary,
                "Link" : result.pdf_url,

                })

    

    df_ARXIV = pd.DataFrame(records_arxiv)
    df_ARXIV.insert(0, 'DOI', '')
    df_ARXIV['Database'] = "Arxiv"
    df_ARXIV['Date'] = df_ARXIV['Date'].dt.tz_localize(None)
    #except:
     #   df_ARXIV['Date'] =  df_ARXIV['Date']
        
    df_ARXIV['DOI'] = np.nan
    df_ARXIV['Date']= df_ARXIV['Date'].dt.date
    df_ARXIV.index+=1
    
        
    return df_ARXIV



################################################## Scopus ###################################################### 

# Api aufrufen und parsen --> für jede Seite der Suchergebnisse wird das gemacht
def _search_scopus(key, query, view, index=0):
    par = {'apiKey': key, 'query': query, 'start': index,
           'httpAccept': 'application/json', 'view': view}
    
    Url = "https://api.elsevier.com/content/search/scopus"
    r = requests.get(Url, params=par)


    js = r.json()
   # print(r.url)
    try:
        total_count = int(js['search-results']['opensearch:totalResults'])
        entries = js['search-results']['entry']
    except:
        print(js['service-error'])
        
    result_df = pd.DataFrame([json_to_pd_scopus(entry) for entry in entries])

    if index == 0:
        return(result_df, total_count)
    else:
        return(result_df)


# Json into Pandas parsen
def json_to_pd_scopus (entry):
    try:
        DOI = entry['prism:doi']
    except:
        DOI = None
    
    
    try:
        Titel = entry['dc:title']
    except:
        Titel = None
        
    
    try:
        Author = entry['dc:creator']
        
    except:
        Author = None
        
    
    try:
        Publisher = entry['prism:publicationName']
    except:
        Publisher = None
        
    
    try:
        Date = entry['prism:coverDate']
    except:
        Date = None
      
    try:
        link_list = entry['link']
        for link in link_list:
            if link['@ref'] == 'scopus':
                    Link = link['@href']
    except:
        Link = None
        
    
    try:
        Citedby = entry['citedby-count']
    except:
        Citedby = None
        
    try:
        Abstract = entry['dc:description']
    except:
        Abstract = None
                       
    
    return pd.Series({'DOI': DOI, 'Title': Titel, 'Author': Author, 'Date': Date, 'Publisher': Publisher,'Cited_by': Citedby, 'Abstract': Abstract, 'Link': Link, 'Database': "Scopus"})

# Aufrufbare Funktion
def scrape_scopus(  key, query, count, view='COMPLETE'):
        if type(count) is not int:
            raise ValueError("%s is not a valid input for the number of entries to return." %number)

        result_df, total_count = _search_scopus(key, query, view=view)

        if total_count <= count:
            count = total_count

        if count <= 25:
            # if less than 25, just one page of response is enough
            return result_df[:count]

        # if larger than, go to next few pages until enough
        i = 1
        while True:
            index = 25*i
            result_df = result_df.append(_search_scopus(key, query, view=view, index=index),
                                         ignore_index=True)
            if result_df.shape[0] >= count:
                result_df.index += 1
                return result_df[:count+1]
            i += 1
        



################################################## Science Direct ###################################################### 


# Api aufrufen und parsen --> für jede Seite der Suchergebnisse wird das gemacht
def _search_sd(key, insttoken, query,  index=0):
    
    
    headers = {}
    headers = CaseInsensitiveDict()
    headers["X-ELS-APIKey"] = key #"8b45b88887de27f0f63d9ad72d06fba9"
    headers["X-ELS-Insttoken"] = insttoken #"fc8667ab791d1fa42063ac02d0408609"
    headers["Content-Type"] = "application/json"
    headers['Accept'] ="application/json"

    data = {
     "qs" : query,
      "display": {
        "offset": index,
        "show": 100
    
      }
    }



    url = "https://api.elsevier.com/content/search/sciencedirect"
    r = requests.put(url, headers=headers, data=json.dumps(data))


    js = r.json()
    #print(r.url)
    try:
        total_count = int(js['resultsFound'])
        entries = js['results']
    except:
        print(js['service-error'])
        
    result_df = pd.DataFrame([json_to_pd(entry) for entry in entries])

    if index == 0:
        return(result_df, total_count)
    else:
        return(result_df)


# Json into Pandas parsen
def json_to_pd (entry):
    try:
        DOI = entry['doi']
    except:
        DOI = None
    
    try:
        Titel = entry['title']
    except:
        Titel = None
        
    
    try:
        Author = str(entry['authors'])
        Author = Author.split(": '") [1]
        Author = Author.split("'") [0]
       # Author = Author_list['@name']
        
    except:
        Author = None
        
    
    try:
        Publisher = entry['sourceTitle']
    except:
        Publisher = None
        
    
    try:
        Date = entry['publicationDate']
    except:
        Date = None
      
    try:
        Link = entry['uri']
    except:
        Link = None                   
                       
    Abstract = None
    
    return pd.Series({'DOI': DOI, 'Title': Titel, 'Author': Author, 'Date': Date, 'Publisher': Publisher, 'Abstract': '-',  'Link': Link, 'Database': "Science Direct"})

# Aufrufbare Funktion
def scrape_sd( key, insttoken, query, count):
        if type(count) is not int:
            raise ValueError("%s is not a valid input for the number of entries to return." %number)

        result_df, total_count = _search_sd(key, insttoken, query)

        if total_count <= count:
            count = total_count

        if count <= 100:
            # if less than 25, just one page of response is enough
            return result_df[:count]

        # if larger than, go to next few pages until enough
        i = 1
        while True:
            index = 100*i
            result_df = result_df.append(_search_sd(key, insttoken, query,  index=index),
                                         ignore_index=True)
            if result_df.shape[0] >= count:
                result_df.index += 1
                return result_df[:count+1]
            i += 1






################################################## Web of Science ###################################################### 




def scrape_wos (query_wos, count):
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        
       

        driver = webdriver.Chrome(ChromeDriverManager().install())
        
        # URL aufrufen
        driver.get('https://www.webofscience.com/wos/woscc/basic-search')
        time.sleep(5)
        #cookies reject
        try:
            driver.find_element_by_id('onetrust-reject-all-handler').click()
        except:
            print("-")
        # Falls Werbung aufpoppt, closen
        try:
            driver.find_element_by_id('pendo-close-guide-8fdced48').click()
        except:
            print("-")

        #Searchbar finden und ausfüllen

        finally:
            search = driver.find_element_by_name('search-main-box')

        search.send_keys(query_wos)   
        
        time.sleep(5)
        search.send_keys(Keys.RETURN)




        #Warten bis Werbung kommt
        time.sleep(5)

        #Werbung wegklicken
        try:
            driver.find_element_by_id('pendo-close-guide-dc656865').click()
            print("Web of Science - Werbung entfernt!")
        except:
            time.sleep(2)
            print("Web of Science - Keine Werbung!")

        time.sleep(2)    

        #Anzahl Suchergebnisse   
        Anzahl = driver.find_element_by_class_name('brand-blue').text    
        print("Web of Science - Anzahl Suchergebnisse:", Anzahl)
        x = locale.atof(Anzahl)
        x = int(x)
       
          
        records = []  # Liste für Ergebnisse initialisieren
        if count < x:
            y = int(count/50)
            print('Web of Science - - Ausgabe an Sucherergebnissen: ', count)
        else:
            y = int(int(x)/50)
            print('Web of Science - - Ausgabe an Sucherergebnissen: ', x)
        
        print('Web of Science - Seiten zu durchsuchen: ', y+1) 

        if x<50:
            z = x*2
            
        else:
            if count < 40:
                z = 2*count
            else:
                z = 40
            
        
        time.sleep(2)
        
        for i in range(y+1):
            time.sleep(5)
            #Nach unten srollen, da sonst nur der ersten Data-Container automatisch geladen wird

            y = 300
            for timer in range(0,z):
                 driver.execute_script("window.scrollTo(0, "+str(y)+")")
                 y += 400  
                 time.sleep(1)
            #driver.find_element_by_css_selector("body").send_keys(Keys.CONTROL, Keys.END)

            
            time.sleep(2)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            

            for item in soup.select('app-record'): 
                    try:
                        #Titel
                        #print(item.select('app-summary-title')[0].get_text()) 
                        Titel = item.select('app-summary-title')[0].get_text()
                    except:
                        Titel = None

                    try:
                        #Date
                        #date_help = item.select('summary-record-pubdate')#.get_text()
                        date_help = item.find("span", {"name": "pubdate"}).get_text()
                        date = date_help.split('|', 1)[0]
                    except:
                        date = None

                    try:
                        Link = item.select('a')[0]['href']
                        Link = "https://www.webofscience.com"+Link
                    except:
                        Link = None

                    try:
                        Author = item.select('app-summary-authors')[0].get_text()
                    except:
                        Author = None

                    try:
                        #Abstract
                       # print(item.select('p')[0].get_text())
                        Abstract = item.select('p')[0].get_text()
                    except:
                        Abstract = None
                        #Journal/Publisher

                    try:
                     #   print(item.select('app-jcr-overlay')[0].get_text())
                        Publisher = item.select('app-jcr-overlay')[0].get_text()
                    except:
                        Publisher = None

                    try:
                        #Zitieranzahl
                        cit = item.select('div')[10].get_text()
                        substring = "Citations"
                        if substring in cit:
                            cit = cit.split(" Citations")[0]
                        else:
                            cit = None

                    except:
                        cit = None

                    records.append({  #Liste mit Ergebnissen erweitern
                                   #"DOI" : '',
                                    "Title" : Titel,
                                    "Author" : Author,
                                    "Date" : date,
                                    "Cited_by": cit,
                                    "Publisher" : Publisher,
                                    "Abstract" : Abstract,
                                    "Link" : Link
                                    #"Zitiert von": zit,
                                    
                                    })
                      
                
            time.sleep(10)
            #Entweder nächste Seite aufrufen oder Browser beenden
            try:
                driver.find_element_by_css_selector('button[data-ta="next-page-button"]').click()
            except:    
                driver.quit()
                
        driver.quit()
        print('--------------------')
        df_WOS = pd.DataFrame(records)   
        df_WOS.insert(0, 'DOI', '')
        df_WOS['DOI'] = np.nan
        df_WOS['Database'] = "Web of Science"
        df_WOS = df_WOS.head(count)
        df_WOS.index += 1
        
        return df_WOS



    
    
################################################## ACM digital ###################################################### 

    
    
    
    
def scrape_acm (query_acm,  count):
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        
       

        driver = webdriver.Chrome(ChromeDriverManager().install())

        # URL aufrufen
        driver.get('https://dl.acm.org/')
        time.sleep(5)

        search = driver.find_element_by_name('AllField')

       
        search.send_keys(query_acm)   
        
        time.sleep(5)
        search.send_keys(Keys.RETURN)
        time.sleep(5)
        

        Anzahl = driver.find_element_by_class_name("result__count").text
        Anzahl = Anzahl.split(" ")[0]
        try:
            Anzahl = Anzahl.replace(',', '')
        except:
            Anzahl = Anzahl
        #print(Anzahl)
        
        
        
        x =int(Anzahl)
        print('ACM digital - Anzahl Suchergebnisse: ', x)
          
        records = []  # Liste für Ergebnisse initialisieren
        if count < int(x):
            y = int(count/20)
            print('ACM digital - Ausgabe an Sucherergebnissen: ', count)
        else:
            #Schleife über Seiten einbauen 
            y = int(int(x)/20)
            print('ACM digital - Ausgabe an Sucherergebnissen: ', x)
        
        if x<20:
            z = x*2
        else:
            if count < 20:
                z = 2*count
            else:
                z = 15
        
        
        print('ACM digital - Seiten zu durchsuchen: ', y+1) 
        
        for i in range(y+1):
            time.sleep(5)
            #Nach unten srollen, da sonst nur der erste Data-Container automatisch geladen wird

            y = 300
            for timer in range(0,z):
                 driver.execute_script("window.scrollTo(0, "+str(y)+")")
                 y += 400  
                 time.sleep(1)
            
            
            time.sleep(2)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            

            for item in soup.select('div[class="issue-item__content-right"]'):
                try: 
                    #DOI
                    DOI_help = item.select('a')[0]['href']
                    DOI = DOI_help.split("/doi/")[1]
                    #print(DOI)
                except:
                    DOI = None
                    
                try:
                    #Title
                    Title = item.select('h5')[0].get_text()                  
                except:
                    Title = None
                    
                try:
                    Author = item.select('ul')[0].get_text()
                    Author = Author.replace("\n", " ")
                except:
                    Author = Nonee
                    #print(Author)
                    
                try:
                    #Date
                    Date = item.select('span[class="dot-separator"]')[0].get_text()
                    Date = Date.split(",")[0]
                except:
                    Date = None
                    #print(Date)
                
                try:
                    #Publisher
                    Publisher = item.select('span[class="epub-section__title"]')[0].get_text()
                    try: 
                        Publisher = Publisher.split(":")[1]
                    except:
                        Publisher = Publisher
                    #print(Publisher)
                except:
                    Publisher = None

                try:
                    Abstract = item.select('p')[0].get_text()
                    #print(Abstract)
                except:
                    Abstract = None
                
                try:
                    #Link
                    Link = "https://dl.acm.org" + DOI_help
                    #print(Link)
                except:
                    Link = None

                try:
                    cit= item.find("span", {"class": "citation"}).get_text()
                except:
                    cit = None

                records.append({  #Liste mit Ergebnissen erweitern
                                "DOI" : DOI,
                                "Title" : Title,
                                "Author" : Author,
                                "Cited_by" : cit,
                                "Date" : Date,
                                "Publisher" : Publisher,
                                "Abstract" : Abstract,
                                "Link" : Link
                                

                                })

                
            time.sleep(2)
            #Entweder nächste Seite aufrufen oder Browser beenden
        try:
            driver.find_element_by_class_name('pagination__btn--next').click()
        except:    
            driver.quit()
                
        driver.quit()
        print('--------------------')
        df_ACM = pd.DataFrame(records)    
        df_ACM = df_ACM.head(count)
        df_ACM['Database'] = "ACM Digital"
        df_ACM.index += 1
        
        return df_ACM



    
    
################################################## IEEE ###################################################### 

    
    
    
    
def scrape_ieee (query_ieee, count):
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        
       

        driver = webdriver.Chrome(ChromeDriverManager().install())

        # URL aufrufen
        driver.get('https://ieeexplore.ieee.org/')
        time.sleep(5)

        search = driver.find_element_by_class_name("Typeahead-input")

       
        search.send_keys(query_ieee)   
        
        time.sleep(3)
        search.send_keys(Keys.RETURN)
        time.sleep(8)
        

        Anzahl = driver.find_element_by_class_name("Dashboard-header").text
        Anzahl = Anzahl.split("of ")[1]
        
        Anzahl = Anzahl.split(" for")[0]
        
        Anzahl = Anzahl.split(" result")[0]
        
        try:
            Anzahl = int(Anzahl.replace(",",""))
        except:
            Anzahl = int(Anzahl)
        
        print("IEEE digital - Anzahl Suchergebnisse: ", Anzahl)
        
        
        
          
        records = []  # Liste für Ergebnisse initialisieren
        if count < Anzahl:
            y = int(count/25)
            print("IEEE digital - Ausgabe an Suchergebnissen: ", count)
        else:
            #Schleife über Seiten einbauen 
            y = int(Anzahl/25)
            print("IEEE digital - Ausgabe an Suchergebnissen: ", Anzahl)
        
        print('IEEE digital - Seiten zu durchsuchen: ', y+1) 
        
        if Anzahl<25:
            z = Anzahl*2
        else:
            if count < 25:
                z = 2*count
            else:
                z = 15
            
        
        
        
        for i in range(y+1):
            time.sleep(5)
            #Nach unten srollen, da sonst nur der erste Data-Container automatisch geladen wird

            t = 400
            for timer in range(0,z):
                 driver.execute_script("window.scrollTo(0, "+str(t)+")")
                 t += 400  
                 time.sleep(1)
            
            
            time.sleep(2)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            

            for item in soup.select('div[class="List-results-items"]'):
                try: 
                        
                    #Title
                    Title = item.select('h2')[0].get_text()
                        #print(Title) 
                except:
                    Title = None
                
                try:
                    Author = item.select('p')[0].get_text()
                except:
                    Author = None
                
                try:
                    Date = item.select('div[class="publisher-info-container"]')[0].get_text()
                    Date = Date.split("|")[0]
                    Date = Date.split(": ")[1]
                    #print(Date)
                except:
                    Date =None
                
                try:
                    Publisher = item.select('div[class="description"]')[0].get_text()
                    Publisher = Publisher.split("|")[0]
                    Publisher = Publisher.split("Year :")[0]
                    
                except:
                    Publisher = None
                    #print(Publisher)
                try:
                    #Abstract
                    Abstract = item.select('div[class="row doc-access-tools-container"]')[0].get_text()
                    Abstract = Abstract.split("Abstract")[1]
                    Abstract = Abstract.split("Show More")[0]
                    
                except:
                    Abstract = None
                
                    #print(Abstract)
                try:
                    #Link
                    Link_help = item.select('a')[0]['href']#.get_text()
                    Link = "https://ieeexplore.ieee.org" + Link_help
                except:
                    Link = None
                    
                try:
                    cit = item.select('a:contains("Papers")')[0].get_text()
                    substring = "Papers"
                    if substring in cit:
                        cit = cit.replace("Papers (","")
                        cit = cit.replace(")","")
                    else:
                        cit = cit
                except:
                    cit = None


                    #print(Link)

                    #print("---------------------")
                    #print(item)

                records.append({  #Liste mit Ergebnissen erweitern
                                #"DOI" : '',
                                "Title" : Title,
                                "Author" : Author,
                                "Cited_by": cit,
                                "Date" : Date,
                                "Publisher" : Publisher,
                                "Abstract" : Abstract,
                                "Link" : Link
                                

                                })

                
            
            #Entweder nächste Seite aufrufen oder Browser beenden
            try:
                driver.find_element_by_class_name('next-btn').click()
            except:    
                driver.quit()
                
        driver.quit()
        print('--------------------') 
        df_ieee = pd.DataFrame(records)    
        df_ieee.insert(0, 'DOI', '')
        df_ieee['DOI'] = np.nan
        df_ieee['Database'] = "IEEE"
        df_ieee = df_ieee.head(count)
        df_ieee.index += 1
        
        return df_ieee


    
################################################## Emerald ###################################################### 

    
    
    
    
def scrape_emerald (query_emerald, count):
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        
       

        driver = webdriver.Chrome(ChromeDriverManager().install())

        # URL aufrufen
        driver.get('https://www.emerald.com/insight/')
        time.sleep(5)

        search = driver.find_element_by_id("terms")

       
        search.send_keys(query_emerald)   
        
        time.sleep(3)
        search.send_keys(Keys.RETURN)
        time.sleep(8)
        

        Anzahl = driver.find_element_by_class_name("intent_searchresultscount").text
        Anzahl = Anzahl.split("of ")[1]
        Anzahl = int(Anzahl)
        print("Emerald Insight - Anzahl Suchergebnisse: ", Anzahl)
        
        driver.find_element_by_link_text("50").click()
        time.sleep(6)
        
          
        records = []  # Liste für Ergebnisse initialisieren
        if count < Anzahl:
            y = int(count/50)
            print("Emerald Insight - Ausgabe an Suchergebnissen: ", count)
        else:
            #Schleife über Seiten einbauen 
            y = int(Anzahl/50)
            print("Emerald Insight - Ausgabe an Suchergebnissen: ", Anzahl)
        
        print('Emerald Insight - Seiten zu durchsuchen: ', y+1) 
        
            
        
        
        
        for i in range(y+1):
            time.sleep(5)
            #Nach unten srollen, da sonst nur der erste Data-Container automatisch geladen wird

            t = 500
            for timer in range(0,15):
                 driver.execute_script("window.scrollTo(0, "+str(t)+")")
                 t += 1500  
                 time.sleep(1)
            
            
            time.sleep(2)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            

            for item_2 in soup.select('div[class="intent_search_result container card-shadow is-animated Search-item__wrapper"]'):
    
                for item in item_2.select('div[class="d-lg-flex flex-row pb-3"]'):
                    #print(item)
                    try:
                        Title =  item.select('h2')[0].get_text()
                        #print(Title)
                    except:
                        Title= None

                    try:
                        Author = item.select('p')[0].get_text()
                        Author = Author.split(",")[0]
                        Author = Author.split("and")[0]
                        #print(Author)
                    except:
                        Author = None

                    try:
                        Date = item.select('div[class="pr-2 small"]')[0].get_text()
                        Date = Date.split("Publication date: ")[1]
                        #Date = Date.split(" ")[2]
                        #print(Date)
                    except:
                        Date = None

                try:
                    Abstract = item_2.select('div[class="intent_abstract pb-1 col-md-7 pt-2 pl-2 pr-4"]')[0].get_text()
                    #print(Abstract)
                except:
                    Abstract = None

                try:
                    Link = item_2.select('div[class="mb-1"]')[2].get_text()
                    Link = Link.split("DOI: ")[1]
                    #print(Link)

                except:
                    Link = None

                try:
                    Publisher = item_2.select('div[class="mb-1"]')[0].get_text()
                    #Publisher = Publisher.split(",")[0]
                    #print(Publisher)

                except:
                    Publisher = None

                try:
                    DOI = Link.split("https://doi.org/")[1]
                    #print(DOI)
                except:
                    DOI = None

                cit = None

                #print("---")

                records.append({  #Liste mit Ergebnissen erweitern
                                "DOI" : DOI,
                                "Title" : Title,
                                "Author" : Author,
                                "Cited_by": cit,
                                "Date" : Date,
                                "Publisher" : Publisher,
                                "Abstract" : Abstract,
                                "Link" : Link
                                

                                })

                
            
            #Entweder nächste Seite aufrufen oder Browser beenden
            try:
                driver.find_element_by_class_name("intent_next_page_link").click()
            except:    
                driver.quit()
                
        driver.quit()
        print('--------------------') 
        df_emerald = pd.DataFrame(records)    
        
        df_emerald['Database'] = "Emerald Insight"
        df_emerald = df_emerald.head(count)
        df_emerald.index += 1
        
        return df_emerald
    
    
    
    
    
        

    
    

################################################## Google Scholar ###################################################### 



def scrape_scholar(query_scholar, Start, count):
        #Start Datum der Suche

        start_date = Start
        

        driver = webdriver.Chrome(ChromeDriverManager().install())

        # URL aufrufen
        driver.get('https://scholar.google.de/')
        time.sleep(5)

        #Searchbar finden und ausfüllen
        search = driver.find_element_by_id('gs_hdr_tsi')




        search.send_keys(query_scholar)

        time.sleep(5)
        search.send_keys(Keys.RETURN)
        #############################################################################

        #### 60 Sekunden Warteschranke einbauen, falls Captcha-Abfrage kommt. Falls Captach gelöst geht es automatisch weiter
        #### Falls es nicht gelöst wird, wird der driver beendet

        try:
            load = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "gs_ab_md")))
            
            
            # Zeitraum einstellen --> Man muss nur Start einstellen, da dann automatisch bis heute gesucht wird
            time.sleep(3)
            driver.find_element_by_link_text("Zeitraum wählen...").click()
            time.sleep(2)
            start = driver.find_element_by_id('gs_as_ylo')
            start.send_keys(start_date)
            time.sleep(2)
            start.send_keys(Keys.RETURN)
            time.sleep(2)

            ## Anzahl Ergebnisse --> /10 ist die Anzahl der Klicks auf "weiter"
            Anzahl = driver.find_element_by_id('gs_ab_md').text
            Anzahl = Anzahl.split("Ungefähr ")[1]
            Anzahl = Anzahl.split(" Ergebnisse")[0]
            Anzahl = int(Anzahl.replace('.',''))
            
            
            if count < Anzahl:
                y = int(count/10)+1
            else:
                y = int(Anzahl/10)+1
                      
            print("Seitenanzahl der Scholar-Suche:", y)
            print("Insgesamte Anzahl an Ergebnissen bei Google Scholar:", Anzahl)
            
            if Anzahl<10:
                z = Anzahl*2
            else:
                if count < 10:
                    z = 2*count
                else:
                    z = 10
            records = []  # Liste für Ergebnisse initialisieren

        # in range(y); 2 nur zum Testen
            for i in range(y): #y
                
                time.sleep(2)
                # Scrollen simulieren, damit Google denkt wir sind ein echter Mensch
                y = 300
                for timer in range(0,5):
                     driver.execute_script("window.scrollTo(0, "+str(y)+")")
                     y += 400  
                     time.sleep(1)
                
                
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'lxml')

                ### Die ganzen Prints können auskommentiert werden


                for item in soup.select('[data-lid]'): 
                        #print('----------------------------------------') 
                        try: 
                            
                            # print(item) 
                            #print(item.select('h3')[0].get_text()) 
                            title = item.select('h3')[0].get_text()

                            #print(item.select('a')[0]['href'])
                            link = item.select('a')[0]['href']

                            #print(item.select('.gs_a')[0].get_text()) 
                            author = item.select('.gs_a')[0].get_text()

                            txt = item.select('.gs_a')[0].get_text()
                            #print("Veröffentlichungsjahr:", re.findall(r'\d+', txt)[0])

                            year = re.findall(r'\d+', txt)[-1]
                            #print(item.select('.gs_rs')[0].get_text()) 

                            abstract = item.select('.gs_rs')[0].get_text()

                            zit=item.select('.gs_fl')[1].get_text()
                            #print("Zitiert von:", re.findall(r'\d+', zit)[0])

                             
                        except Exception as e: 
                            #raise e
                            print('---')
                            
                        #print('----------------------------------------')    
                        
                        records.append({  #Liste mit Ergebnissen erweitern
                            #"DOI" : '',
                            "Title" : title,
                            "Author" : author,
                            "Date" : year,
                            "Abstract" : abstract,
                            "Link" : link,
                            "Zitiert von": zit    
                            })
                # Random Wartezeit (2-10 Sekunden), bis nächste Seite aufgerufen wird, um IP-Blocks zu verhindern

            w = random.randint(1,9)
            time.sleep(w)

            #Entweder nächste Google-Seite aufrufen oder Browser beenden
            try:
                driver.find_element_by_link_text('Weiter').click()
            except:    
                driver.quit()

        finally:
            driver.quit()
                
                
        # alles in Dataframe packen        
        df_scholar = pd.DataFrame(records)
        df_scholar.insert(0, 'DOI', '')
        df_scholar['DOI'] = np.nan
        df_scholar['Title'] = df_scholar["Title"].str.replace(r"\[.*\]", "", regex=True)
        df_scholar = df_scholar.head(count)
        df_scholar.index += 1
        return df_scholar
        



################################################## API-Scrape ###################################################### 

def api_scrape(query, scopus_key, sd_key, count):
    #count = 5000
    try:
        df_Scopus = scrape_scopus(scopus_key, query, count)
    except:
        print('Keine Suchergebnisse bei Scopus!')
        df_Scopus = pd.DataFrame()
    
    try:
        df_ScienceDirect = scrape_sd(sd_key, query, count)
    except:
        print('Keine Suchergebnisse bei Science Direct!')
        df_ScienceDirect = pd.DataFrame()
    
    try:
        df_Arxiv = scrape_arxiv(query, count)
    except:
        print('Keine Suchergebnisse bei Arxiv!')
        df_Arxiv = pd.DataFrame()
      
    frames = [df_Scopus, df_ScienceDirect, df_Arxiv]

    result = pd.concat(frames, ignore_index=True)
    pre = len(result)
    result[result['DOI'].isnull() | ~result[result['DOI'].notnull()].duplicated(subset='DOI',keep='first')]
    result['Title'] = result['Title'].str.lower()
    result.drop_duplicates(subset ='Title', keep = 'first', inplace = True)
    after = len(result)
    print('Anzahl Suchergebnisse: ', after)
    print('Es wurden', pre-after, 'Duplikate entfernt! (Basierend auf DOI oder Titel)')
    result.reset_index(inplace = True, drop = True)
    result.index += 1
    result['Cited_by'] = pd.to_numeric(result['Cited_by'])
    
    return result




################################################## complete-Scrape ###################################################### 

def complete_scrape(query, scopus_key, sd_key, count):
    #count = 5000
    try:
        df_Scopus = scrape_scopus(scopus_key, query, count)
    except:
        print('Keine Suchergebnisse bei Scopus!')
        df_Scopus = pd.DataFrame()
    
    try:
        df_ScienceDirect = scrape_sd(sd_key, query, count)
    except:
        print('Keine Suchergebnisse bei Science Direct!')
        df_ScienceDirect = pd.DataFrame()
    
    try:
        df_Arxiv = scrape_arxiv(query, count)
    except:
        print('Keine Suchergebnisse bei Arxiv!')
        df_Arxiv = pd.DataFrame()
    
    try:
        df_wos = scrape_wos(query, count)
    except:
        print('Keine Suchergebnisse bei Web of Science!')
        df_wos = pd.DataFrame()
    
    try:
        df_acm = scrape_acm(query, count)
    except:
        print('Keine Suchergebnisse bei ACM digital!')
        df_acm = pd.DataFrame()
    
    try:
        df_ieee = scrape_ieee(query, count)
    except:
        print('Keine Suchergebnisse bei IEEE!')
        df_ieee = pd.DataFrame()
        
    try:
        df_emerald = scrape_emerald(query, count)
    except:
        print('Keine Suchergebnisse bei Emerald Insight')
        df_emerald = pd.DataFrame()
    
    
    
    frames = [df_Scopus, df_ScienceDirect, df_Arxiv, df_wos, df_acm, df_ieee, df_emerald]

    result = pd.concat(frames, ignore_index=True)
    pre = len(result)
    result[result['DOI'].isnull() | ~result[result['DOI'].notnull()].duplicated(subset='DOI',keep='first')]
    result['Title'] = result['Title'].str.lower()
    result.drop_duplicates(subset ='Title', keep = 'first', inplace = True)
    after = len(result)
    print('Anzahl Suchergebnisse: ', after)
    print('Es wurden', pre-after, 'Duplikate entfernt! (Basierend auf DOI oder Titel)')
    result.reset_index(inplace = True, drop = True)
    result['Cited_by'] = pd.to_numeric(result['Cited_by'])
    result.index += 1
    
    return result



        
                

