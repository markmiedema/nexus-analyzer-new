"""
Seed data for state_tax_config table.
Current as of October 2025.
"""

from sqlalchemy.orm import Session
from models.state_tax_config import StateTaxConfig
from database import SessionLocal
import logging

logger = logging.getLogger(__name__)


STATE_TAX_DATA = [
    {
        'state_code': 'AL',
        'state_name': 'Alabama',
        'has_sales_tax': True,
        'state_tax_rate': 4.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 5.22,
        'max_combined_rate': 13.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-01-01',
        'registration_url': 'https://www.revenue.alabama.gov/sales-use/',
        'notes': 'Marketplace facilitator law effective Jan 1, 2019'
    },
    {
        'state_code': 'AK',
        'state_name': 'Alaska',
        'has_sales_tax': False,
        'state_tax_rate': 0.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.76,
        'max_combined_rate': 7.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2020-04-01',
        'registration_url': 'https://www.commerce.alaska.gov/web/dcra/TaxDivision.aspx',
        'notes': 'No state sales tax, but local jurisdictions may impose'
    },
    {
        'state_code': 'AZ',
        'state_name': 'Arizona',
        'has_sales_tax': True,
        'state_tax_rate': 5.60,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.77,
        'max_combined_rate': 11.20,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://azdor.gov/transaction-privilege-tax',
        'notes': 'Transaction Privilege Tax (TPT)'
    },
    {
        'state_code': 'AR',
        'state_name': 'Arkansas',
        'has_sales_tax': True,
        'state_tax_rate': 6.50,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.93,
        'max_combined_rate': 11.63,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://www.dfa.arkansas.gov/excise-tax/sales-and-use-tax/',
        'notes': None
    },
    {
        'state_code': 'CA',
        'state_name': 'California',
        'has_sales_tax': True,
        'state_tax_rate': 7.25,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.68,
        'max_combined_rate': 10.75,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://www.cdtfa.ca.gov/taxes-and-fees/sales-and-use-tax.htm',
        'notes': 'District taxes can apply'
    },
    {
        'state_code': 'CO',
        'state_name': 'Colorado',
        'has_sales_tax': True,
        'state_tax_rate': 2.90,
        'has_local_tax': True,
        'avg_local_tax_rate': 4.87,
        'max_combined_rate': 11.20,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://tax.colorado.gov/sales-use-tax',
        'notes': 'Home-rule cities require separate registration'
    },
    {
        'state_code': 'CT',
        'state_name': 'Connecticut',
        'has_sales_tax': True,
        'state_tax_rate': 6.35,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 6.35,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://portal.ct.gov/DRS/Sales-Tax/Sales-Tax',
        'notes': 'No local sales tax'
    },
    {
        'state_code': 'DE',
        'state_name': 'Delaware',
        'has_sales_tax': False,
        'state_tax_rate': 0.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 0.00,
        'has_mpf_law': False,
        'mpf_effective_date': None,
        'registration_url': None,
        'notes': 'No sales tax'
    },
    {
        'state_code': 'FL',
        'state_name': 'Florida',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.05,
        'max_combined_rate': 8.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2021-07-01',
        'registration_url': 'https://floridarevenue.com/taxes/taxesfees/Pages/sales_tax.aspx',
        'notes': 'Discretionary surtax varies by county'
    },
    {
        'state_code': 'GA',
        'state_name': 'Georgia',
        'has_sales_tax': True,
        'state_tax_rate': 4.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 3.37,
        'max_combined_rate': 9.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2020-04-01',
        'registration_url': 'https://dor.georgia.gov/taxes/business-taxes/sales-use-tax',
        'notes': None
    },
    {
        'state_code': 'HI',
        'state_name': 'Hawaii',
        'has_sales_tax': True,
        'state_tax_rate': 4.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.44,
        'max_combined_rate': 4.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2020-07-01',
        'registration_url': 'https://tax.hawaii.gov/geninfo/general-excise-tax/',
        'notes': 'General Excise Tax (GET), not traditional sales tax'
    },
    {
        'state_code': 'ID',
        'state_name': 'Idaho',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.03,
        'max_combined_rate': 9.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-06-01',
        'registration_url': 'https://tax.idaho.gov/taxes/sales-tax/',
        'notes': None
    },
    {
        'state_code': 'IL',
        'state_name': 'Illinois',
        'has_sales_tax': True,
        'state_tax_rate': 6.25,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.54,
        'max_combined_rate': 11.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2020-01-01',
        'registration_url': 'https://tax.illinois.gov/businesses/taxinformation/sales.html',
        'notes': None
    },
    {
        'state_code': 'IN',
        'state_name': 'Indiana',
        'has_sales_tax': True,
        'state_tax_rate': 7.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 7.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://www.in.gov/dor/business-tax/sales-tax/',
        'notes': 'No local sales tax'
    },
    {
        'state_code': 'IA',
        'state_name': 'Iowa',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.94,
        'max_combined_rate': 8.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://tax.iowa.gov/taxes/sales-and-use-tax',
        'notes': None
    },
    {
        'state_code': 'KS',
        'state_name': 'Kansas',
        'has_sales_tax': True,
        'state_tax_rate': 6.50,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.26,
        'max_combined_rate': 11.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2021-07-01',
        'registration_url': 'https://www.ksrevenue.gov/taxTypes/salestax.html',
        'notes': None
    },
    {
        'state_code': 'KY',
        'state_name': 'Kentucky',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 6.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://revenue.ky.gov/Collections/Sales-Use-Tax/Pages/default.aspx',
        'notes': 'No local sales tax'
    },
    {
        'state_code': 'LA',
        'state_name': 'Louisiana',
        'has_sales_tax': True,
        'state_tax_rate': 4.45,
        'has_local_tax': True,
        'avg_local_tax_rate': 5.07,
        'max_combined_rate': 11.45,
        'has_mpf_law': True,
        'mpf_effective_date': '2020-07-01',
        'registration_url': 'https://revenue.louisiana.gov/TaxTypes/SalesUseTax',
        'notes': None
    },
    {
        'state_code': 'ME',
        'state_name': 'Maine',
        'has_sales_tax': True,
        'state_tax_rate': 5.50,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 5.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://www.maine.gov/revenue/taxes/sales-use-tax',
        'notes': 'No local sales tax'
    },
    {
        'state_code': 'MD',
        'state_name': 'Maryland',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 6.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://www.marylandtaxes.gov/business/sales-use/index.php',
        'notes': 'No local sales tax'
    },
    {
        'state_code': 'MA',
        'state_name': 'Massachusetts',
        'has_sales_tax': True,
        'state_tax_rate': 6.25,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 6.25,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://www.mass.gov/sales-and-use-tax',
        'notes': 'No local sales tax'
    },
    {
        'state_code': 'MI',
        'state_name': 'Michigan',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 6.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://www.michigan.gov/taxes/business-taxes/sales-use',
        'notes': 'No local sales tax'
    },
    {
        'state_code': 'MN',
        'state_name': 'Minnesota',
        'has_sales_tax': True,
        'state_tax_rate': 6.875,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.65,
        'max_combined_rate': 8.875,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://www.revenue.state.mn.us/sales-and-use-tax',
        'notes': None
    },
    {
        'state_code': 'MS',
        'state_name': 'Mississippi',
        'has_sales_tax': True,
        'state_tax_rate': 7.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.07,
        'max_combined_rate': 8.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2020-01-01',
        'registration_url': 'https://www.dor.ms.gov/business/sales-use-tax',
        'notes': None
    },
    {
        'state_code': 'MO',
        'state_name': 'Missouri',
        'has_sales_tax': True,
        'state_tax_rate': 4.225,
        'has_local_tax': True,
        'avg_local_tax_rate': 4.08,
        'max_combined_rate': 10.85,
        'has_mpf_law': True,
        'mpf_effective_date': '2023-01-01',
        'registration_url': 'https://dor.mo.gov/taxation/business/sales-use/',
        'notes': None
    },
    {
        'state_code': 'MT',
        'state_name': 'Montana',
        'has_sales_tax': False,
        'state_tax_rate': 0.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 0.00,
        'has_mpf_law': False,
        'mpf_effective_date': None,
        'registration_url': None,
        'notes': 'No sales tax'
    },
    {
        'state_code': 'NE',
        'state_name': 'Nebraska',
        'has_sales_tax': True,
        'state_tax_rate': 5.50,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.42,
        'max_combined_rate': 7.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-04-01',
        'registration_url': 'https://revenue.nebraska.gov/businesses/sales-and-use-tax',
        'notes': None
    },
    {
        'state_code': 'NV',
        'state_name': 'Nevada',
        'has_sales_tax': True,
        'state_tax_rate': 6.85,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.53,
        'max_combined_rate': 8.38,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://tax.nv.gov/businesses/sales___use_tax/',
        'notes': None
    },
    {
        'state_code': 'NH',
        'state_name': 'New Hampshire',
        'has_sales_tax': False,
        'state_tax_rate': 0.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 0.00,
        'has_mpf_law': False,
        'mpf_effective_date': None,
        'registration_url': None,
        'notes': 'No sales tax'
    },
    {
        'state_code': 'NJ',
        'state_name': 'New Jersey',
        'has_sales_tax': True,
        'state_tax_rate': 6.625,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 6.625,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-11-01',
        'registration_url': 'https://www.state.nj.us/treasury/taxation/businesses/salestax/',
        'notes': 'No local sales tax'
    },
    {
        'state_code': 'NM',
        'state_name': 'New Mexico',
        'has_sales_tax': True,
        'state_tax_rate': 5.125,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.69,
        'max_combined_rate': 9.06,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://www.tax.newmexico.gov/businesses/gross-receipts-tax/',
        'notes': 'Gross Receipts Tax'
    },
    {
        'state_code': 'NY',
        'state_name': 'New York',
        'has_sales_tax': True,
        'state_tax_rate': 4.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 4.52,
        'max_combined_rate': 8.875,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-06-01',
        'registration_url': 'https://www.tax.ny.gov/bus/st/stidx.htm',
        'notes': None
    },
    {
        'state_code': 'NC',
        'state_name': 'North Carolina',
        'has_sales_tax': True,
        'state_tax_rate': 4.75,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.22,
        'max_combined_rate': 7.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2020-02-01',
        'registration_url': 'https://www.ncdor.gov/taxes-forms/sales-and-use-tax',
        'notes': None
    },
    {
        'state_code': 'ND',
        'state_name': 'North Dakota',
        'has_sales_tax': True,
        'state_tax_rate': 5.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.23,
        'max_combined_rate': 8.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://www.tax.nd.gov/business/sales-and-use-tax',
        'notes': None
    },
    {
        'state_code': 'OH',
        'state_name': 'Ohio',
        'has_sales_tax': True,
        'state_tax_rate': 5.75,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.48,
        'max_combined_rate': 8.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-08-01',
        'registration_url': 'https://tax.ohio.gov/business/ohio-business-taxes/sales-and-use',
        'notes': None
    },
    {
        'state_code': 'OK',
        'state_name': 'Oklahoma',
        'has_sales_tax': True,
        'state_tax_rate': 4.50,
        'has_local_tax': True,
        'avg_local_tax_rate': 4.47,
        'max_combined_rate': 11.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://oklahoma.gov/tax/businesses/registration/sales-and-use-tax.html',
        'notes': None
    },
    {
        'state_code': 'OR',
        'state_name': 'Oregon',
        'has_sales_tax': False,
        'state_tax_rate': 0.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 0.00,
        'has_mpf_law': False,
        'mpf_effective_date': None,
        'registration_url': None,
        'notes': 'No sales tax'
    },
    {
        'state_code': 'PA',
        'state_name': 'Pennsylvania',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.34,
        'max_combined_rate': 8.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://www.revenue.pa.gov/TaxTypes/SUT/Pages/default.aspx',
        'notes': 'Allegheny County 1%, Philadelphia 2%'
    },
    {
        'state_code': 'RI',
        'state_name': 'Rhode Island',
        'has_sales_tax': True,
        'state_tax_rate': 7.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 7.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://tax.ri.gov/tax-types/sales-use-tax',
        'notes': 'No local sales tax'
    },
    {
        'state_code': 'SC',
        'state_name': 'South Carolina',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.46,
        'max_combined_rate': 9.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-04-26',
        'registration_url': 'https://dor.sc.gov/tax/sales',
        'notes': None
    },
    {
        'state_code': 'SD',
        'state_name': 'South Dakota',
        'has_sales_tax': True,
        'state_tax_rate': 4.50,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.90,
        'max_combined_rate': 7.50,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-03-01',
        'registration_url': 'https://dor.sd.gov/businesses/taxes/sales-use-tax/',
        'notes': 'Wayfair case originated here'
    },
    {
        'state_code': 'TN',
        'state_name': 'Tennessee',
        'has_sales_tax': True,
        'state_tax_rate': 7.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.55,
        'max_combined_rate': 9.75,
        'has_mpf_law': True,
        'mpf_effective_date': '2020-07-01',
        'registration_url': 'https://www.tn.gov/revenue/taxes/sales-and-use-tax.html',
        'notes': None
    },
    {
        'state_code': 'TX',
        'state_name': 'Texas',
        'has_sales_tax': True,
        'state_tax_rate': 6.25,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.94,
        'max_combined_rate': 8.25,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://comptroller.texas.gov/taxes/sales/',
        'notes': None
    },
    {
        'state_code': 'UT',
        'state_name': 'Utah',
        'has_sales_tax': True,
        'state_tax_rate': 6.10,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.11,
        'max_combined_rate': 9.05,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://tax.utah.gov/sales',
        'notes': None
    },
    {
        'state_code': 'VT',
        'state_name': 'Vermont',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.37,
        'max_combined_rate': 7.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://tax.vermont.gov/business/sales-and-use-tax',
        'notes': None
    },
    {
        'state_code': 'VA',
        'state_name': 'Virginia',
        'has_sales_tax': True,
        'state_tax_rate': 5.30,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.45,
        'max_combined_rate': 7.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://www.tax.virginia.gov/sales-and-use-tax',
        'notes': None
    },
    {
        'state_code': 'WA',
        'state_name': 'Washington',
        'has_sales_tax': True,
        'state_tax_rate': 6.50,
        'has_local_tax': True,
        'avg_local_tax_rate': 2.89,
        'max_combined_rate': 10.60,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://dor.wa.gov/taxes-rates/sales-and-use-tax-rates',
        'notes': None
    },
    {
        'state_code': 'WV',
        'state_name': 'West Virginia',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.50,
        'max_combined_rate': 7.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://tax.wv.gov/Business/SalesAndUseTax/Pages/SalesAndUseTax.aspx',
        'notes': None
    },
    {
        'state_code': 'WI',
        'state_name': 'Wisconsin',
        'has_sales_tax': True,
        'state_tax_rate': 5.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 0.44,
        'max_combined_rate': 7.90,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-10-01',
        'registration_url': 'https://www.revenue.wi.gov/Pages/FAQS/pcs-sales.aspx',
        'notes': None
    },
    {
        'state_code': 'WY',
        'state_name': 'Wyoming',
        'has_sales_tax': True,
        'state_tax_rate': 4.00,
        'has_local_tax': True,
        'avg_local_tax_rate': 1.36,
        'max_combined_rate': 6.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-07-01',
        'registration_url': 'https://revenue.wyo.gov/excise-tax-division/sales-and-use-tax',
        'notes': None
    },
    {
        'state_code': 'DC',
        'state_name': 'District of Columbia',
        'has_sales_tax': True,
        'state_tax_rate': 6.00,
        'has_local_tax': False,
        'avg_local_tax_rate': 0.00,
        'max_combined_rate': 6.00,
        'has_mpf_law': True,
        'mpf_effective_date': '2019-04-01',
        'registration_url': 'https://otr.cfo.dc.gov/page/sales-and-use-tax',
        'notes': 'No local sales tax'
    }
]


def seed_state_tax_config(db: Session = None):
    """
    Seed state_tax_config table with current state tax data.

    Args:
        db: Database session (if None, creates new session)
    """
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        # Check if data already exists
        existing_count = db.query(StateTaxConfig).count()
        if existing_count > 0:
            logger.info(f"State tax config already seeded ({existing_count} records)")
            return

        # Insert all states
        for state_data in STATE_TAX_DATA:
            state_config = StateTaxConfig(**state_data)
            db.add(state_config)

        db.commit()
        logger.info(f"Successfully seeded {len(STATE_TAX_DATA)} state tax configurations")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding state tax config: {e}")
        raise

    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    """Run seed script directly."""
    logging.basicConfig(level=logging.INFO)
    seed_state_tax_config()
    print("State tax configuration seed complete!")
