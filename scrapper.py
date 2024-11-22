import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
from links import links



# Function to extract organization and document IDs from the URL
def extract_ids(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    organization_id = path_parts[3]
    document_id = path_parts[4]
    return organization_id, document_id

# Function to get text or default value from an element
def get_element_text_or_default(soup, id_pattern):
    try:
        element = soup.find("span", id=re.compile(id_pattern))
        if element:
            element_text = element.get_text(strip=True).replace(',', '')
            return int(element_text)
        return 0
    except (AttributeError, ValueError):
        return 0

# Data storage
data_rows = []
managers_data = []
business_data = {}
# Main processing loop for each link
for link in links:
    organization_id, document_id = extract_ids(link)
    url = f"https://projects.propublica.org/nonprofits/full_text/{document_id}/IRS990"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Business Name
    business_name_element = soup.find("span", id=re.compile(r"BusinessName\[1\]"))
    BusinessName = business_name_element.text.strip() if business_name_element else "Unknown"

    # Financial data
    CYTotalRevenue                      = get_element_text_or_default(soup, "CYTotalRevenueAmt")
    PYTotalRevenue                      = get_element_text_or_default(soup, "PYTotalRevenueAmt")
    PYTotalExpenses                     = get_element_text_or_default(soup, "PYTotalExpensesAmt")
    CYTotalExpenses                     = get_element_text_or_default(soup, "CYTotalExpensesAmt")
    NetAssetsOrFundBalancesBOY          = get_element_text_or_default(soup, "NetAssetsOrFundBalancesBOYAmt")
    NetAssetsOrFundBalancesEOY          = get_element_text_or_default(soup, "NetAssetsOrFundBalancesEOYAmt")
    CashNonInterestBearingGrp           = get_element_text_or_default(soup, r"CashNonInterestBearingGrp\[1\]/EOYAmt\[1\]")
    SavingsAndTempCashInvstGrp          = get_element_text_or_default(soup, r"SavingsAndTempCashInvstGrp\[1\]/EOYAmt\[1\]")
    InvestmentsPubTradedSecGrp          = get_element_text_or_default(soup, r"InvestmentsPubTradedSecGrp\[1\]/EOYAmt\[1\]")
    InvestmentsOtherSecuritiesGrp       = get_element_text_or_default(soup, r"InvestmentsOtherSecuritiesGrp\[1\]/EOYAmt\[1\]")
    InvestmentsProgramRelatedGrp        = get_element_text_or_default(soup, r"InvestmentsProgramRelatedGrp\[1\]/EOYAmt\[1\]")
    CashNonInterestBearingGrpBOY        = get_element_text_or_default(soup, r"CashNonInterestBearingGrp\[1\]/BOYAmt\[1\]")
    SavingsAndTempCashInvstGrpBOY       = get_element_text_or_default(soup, r"SavingsAndTempCashInvstGrp\[1\]/BOYAmt\[1\]")
    InvestmentsPubTradedSecGrpBOY       = get_element_text_or_default(soup, r"InvestmentsPubTradedSecGrp\[1\]/BOYAmt\[1\]")
    InvestmentsOtherSecuritiesGrpBOY    = get_element_text_or_default(soup, r"InvestmentsOtherSecuritiesGrp\[1\]/BOYAmt\[1\]")
    InvestmentsProgramRelatedGrpBOY     = get_element_text_or_default(soup, r"InvestmentsProgramRelatedGrp\[1\]/BOYAmt\[1\]")

    # Calculations
    cash_investments = (InvestmentsProgramRelatedGrp + InvestmentsOtherSecuritiesGrp +
                        InvestmentsPubTradedSecGrp + SavingsAndTempCashInvstGrp + CashNonInterestBearingGrp)
    cash_investmentsBOY = (InvestmentsProgramRelatedGrpBOY + InvestmentsOtherSecuritiesGrpBOY +
                           InvestmentsPubTradedSecGrpBOY + SavingsAndTempCashInvstGrpBOY + CashNonInterestBearingGrpBOY)

    CYOperatingMargin = round((CYTotalRevenue - CYTotalExpenses) / CYTotalRevenue * 100, 2) if CYTotalRevenue else 0
    PYOperatingMargin = round((PYTotalRevenue - PYTotalExpenses) / PYTotalRevenue * 100, 2) if PYTotalRevenue else 0
    CurrentCashAndInvestmentsToOperations = round((cash_investments / CYTotalExpenses) * 100, 2) if CYTotalExpenses else 0
    CurrentCashAndInvestmentsToOperationsBOY = round((cash_investmentsBOY / PYTotalExpenses) * 100, 2) if PYTotalExpenses else 0

    # Check for university management team
    name_title_data = [] 
    i = 1
    while True:
        try:
            name  = soup.find("span", id=re.compile(r"Form990PartVIISectionAGrp\[" + str(i) + r"\]")).text.strip()
            title = soup.find("span", id=re.compile(r"Form990PartVIISectionAGrp\[" + str(i) + r"\]/TitleTxt\[1\]")).text.strip()
            name_title_data.append([BusinessName, name, title])
            i += 1
        except AttributeError:
            break
    
    managers_data.extend(name_title_data)
    
    # Format numbers for display
    def format_number(number):
        return "{:,}".format(number) if number else "0"

    # Append row data
    data_rows.append([
        BusinessName, link, format_number(CYTotalRevenue), format_number(PYTotalRevenue),
        format_number(CYTotalExpenses), format_number(PYTotalExpenses),
        format_number(NetAssetsOrFundBalancesEOY), format_number(NetAssetsOrFundBalancesBOY),
        format_number(CashNonInterestBearingGrp), format_number(SavingsAndTempCashInvstGrp),
        format_number(InvestmentsPubTradedSecGrp), format_number(InvestmentsOtherSecuritiesGrp),
        format_number(InvestmentsProgramRelatedGrp), format_number(cash_investments),
        format_number(CashNonInterestBearingGrpBOY), format_number(SavingsAndTempCashInvstGrpBOY),
        format_number(InvestmentsPubTradedSecGrpBOY), format_number(InvestmentsOtherSecuritiesGrpBOY),
        format_number(InvestmentsProgramRelatedGrpBOY), format_number(cash_investmentsBOY),
        format_number(CYOperatingMargin), format_number(PYOperatingMargin),
        format_number(CurrentCashAndInvestmentsToOperations),
        format_number(CurrentCashAndInvestmentsToOperationsBOY),
    ])


    
# Store the data for the current business and Save to Excel
managers = pd.DataFrame(managers_data, columns=['University','Name', 'Title'])
    
for column in managers.columns:
    if managers[column].dtype == 'object':  # Check if the column contains strings
        managers[column] = managers[column].str.title()

managers.to_excel("university_managers.xlsx", index=False)

df = pd.DataFrame(data_rows, columns=[
    'University', 'ProPublica Link', 'Current Year Total Revenue', 'Prior Year Total Revenue',
    'Current Year Operational Expense', 'Prior Year Operational Expense', 'Current Year Net Assets',
    'Prior Year Net Assets', 'Current Year Cash–non-interest-bearing',
    'Current Year Savings and temporary cash investments',
    'Current Year Investments—publicly traded securities',
    'Current Year - Investments—other securities.', 'Current Year - Investments—program-related',
    'Current Year Cash and Investments', 'Prior Year Cash–non-interest-bearing',
    'Prior Year Savings and temporary cash investments',
    'Prior Year Investments—publicly traded securities', 'Prior Year - Investments—other securities.',
    'Prior Year - Investments—program-related.', 'Prior Year Cash and Investments',
    'Current Year Operating Margin (%)', 'Prior Year Operating Margin (%)',
    'Current Cash and Investments to Operations (%)',
    'Prior Current Cash and Investments to Operations (%)'
])

df.to_excel("Engaged_College_Financial_Metrics.xlsx", index=False)

print("Data scraping and export complete!")
