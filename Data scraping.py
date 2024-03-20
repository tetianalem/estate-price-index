from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import pandas as pd

#A user opens a file "input_financial data.xlsm" and writes a legal entity registration number and a year of organsations about which he wants to receive information
#At the same sheet, a user presses "Load information" button. This button launches Python script
#There is a file "output_data.xlsm"

#a function to load csv files from data.gov.lv
def get_url(url_website,name_table):
    html = urlopen(url_website)
    bs = BeautifulSoup(html, 'html.parser')
    pages = []
    #extract all url adresses from dataset
    for link in bs.find_all('a', href=re.compile('^https://data.gov.lv/dati/dataset/')):
        if 'href' in link.attrs:
            newPage = link.attrs['href']
            pages.append(newPage)
    #extract 1 table with name_table
    name_table0=str('.*'+name_table)
    r = re.compile(name_table0)
    url = list(filter(r.match, pages))[0]
    if url_website==url_financial_data:
        table = pd.read_csv(url,sep=';')
    elif url_website==url_energy_data:
        table = pd.read_csv(url,sep=',')
    return table

url_financial_data='https://data.gov.lv/dati/lv/dataset/gada-parskatu-finansu-dati'
url_energy_data='https://data.gov.lv/dati/lv/dataset/bis_swkx3qxubp9g-wp_zpvciq'

financial_statements=get_url(url_financial_data,'financial_statements')
balance_sheets=get_url(url_financial_data,'balance_sheets')
cash_flow_statements=get_url(url_financial_data,'cash_flow_statements')
income_statements=get_url(url_financial_data,'income_statements')
energy_certificates=get_url(url_energy_data,'eku-energosertifikati')

#creating of one table with information from all previously loaded tables
full_table = pd.merge(pd.merge(pd.merge(
    financial_statements,balance_sheets,on ='file_id',how ='outer'),
    income_statements,on ='file_id',how ='outer'),
    cash_flow_statements,on ='file_id',how ='outer')

#leverage ratios
#Equity ratio (Equity/Assets, benchmark: >20%)
full_table.loc[(full_table['equity']!='')&(full_table['equity']!=0)&(full_table['total_equities']!='')&(full_table['total_equities']!=0),'Equity ratio']=full_table['equity']/full_table['total_equities']
#Debt ratio (Liabilities/Assets, benchmark: <80%)
full_table.loc[(full_table['equity']!='')&(full_table['equity']!=0)&(full_table['total_equities']!='')&(full_table['total_equities']!=0),'Debt ratio']=(full_table['total_equities']-full_table['equity'])/full_table['total_equities']
#Debt-to-Equity ratio (Liabilities/Equity)
full_table.loc[(full_table['equity']!='')&(full_table['equity']!=0)&(full_table['total_equities']!='')&(full_table['total_equities']!=0),'Debt-to-Equity ratio']=(full_table['total_equities']-full_table['equity'])/full_table['equity']
#Equity multiplier (Assets/Equity, benchmark: <5)
full_table.loc[(full_table['equity']!='')&(full_table['equity']!=0)&(full_table['total_equities']!='')&(full_table['total_equities']!=0),'Equity multiplier']=full_table['total_equities']/full_table['equity']

input_data=pd.read_excel("input_financial data.xlsm")
list_input_registration_number=input_data['legal entity registration number'].values.tolist()
list_input_year=input_data['year'].values.tolist()

output_data=pd.DataFrame()

for input_registration_number,input_year in zip(list_input_registration_number, list_input_year):
    for i in range(0,len(full_table['legal_entity_registration_number'])):
        #if a user wants to obtain information about an organisation for all years in which there is information about an organisation
        if input_year=='all' and full_table.iloc[i]['legal_entity_registration_number']==input_registration_number: 
            print(input_year,input_registration_number)
            table=full_table.loc[(full_table['legal_entity_registration_number']==input_registration_number)]
            output_data=output_data.append(table)
        #if a user wants to obtain information about an organisation for a specific year
        else:
            if full_table.iloc[i]['year']==input_year and full_table.iloc[i]['legal_entity_registration_number']==input_registration_number:
                table=full_table.loc[(full_table['legal_entity_registration_number']==input_registration_number)&(full_table['year']==input_year)]
                output_data=output_data.append(table)

output_data=output_data.drop_duplicates()
output_data=output_data[['legal_entity_registration_number','year','Equity ratio','Debt ratio','Debt-to-Equity ratio','Equity multiplier']]

with pd.ExcelWriter('output_financial data.xlsx') as writer:  
    input_data.to_excel(writer, sheet_name='input')
    output_data.to_excel(writer, sheet_name='output')
