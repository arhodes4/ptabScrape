import requests
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time
from datetime import datetime



'''
Scraper for ptab.uspto.gov:
This function uses object-oriented programming techniques in concjunction with the requests library to scrape
https://ptab.uspto.gov. The steps that the scraping bot executes upon are as follows:

1. Login to ptab via a POST request
2. Click on "Search" tab via GET request
3. Enter AIA review number into search form via POST request
4. Scrape "Status" field via GET request
    a.) Find initial status and set as status_0
    b.) Continue to scrape "Status" field and store as status_1, if not equal to status_0, send email of new status,
        if not, continue to scrape "status" field and replace status_1
5. Click on "View Documents" button via GET request
6. Count number of documents populated in child window
    a.) Find initial document count and set as doc_count_0
    b.) Continue to scrape child window for document count and set as doc_count_1, if not equal to doc_count_0,
        download document via doc_download() function and POST request, then send email of downloaded document. 
        If not, continue to count doc length and replace doc_count_1

Time from initial login to end of scrape is: 3.279 seconds
        

'''


class ptab:

    def __init__(self, patent, receiving_email):
        self.port = 587
        self.patent = patent
        self.email_username = 'ptab.alert'
        self.sending_email = 'ptab.alert@gmail.com'
        self.receiving_email = receiving_email
        self.pword = 'denovocap'
        self.context = ssl.create_default_context ()
        self.url_origin = 'https://ptab.uspto.gov/ptabe2e/rest/login'
        self.url_search = 'https://ptab.uspto.gov/#/external/search'
        self.url_enter = 'https://ptab.uspto.gov/ptabe2e/rest/search'
        self.url_doc_view = 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1539888/documents'

        self.data = '{"userName":"arhodes3@villanova.edu","password":"Trust888Trust888"}'
        self.params = (
            ('cacheFix', '1615866146331'),
        )
        self.cookies = {
            '_gid': 'GA1.2.505039707.1615866090',
            '_gat_SiteSpecificT': '1',
            '_gat_RollupT': '1',
            '_gat_GSA_ENOR0': '1',
            '_ga': 'GA1.2.767718179.1615866090',
            '_gat_UA-21265023-12': '1',
            '_4c_': 'lZJNj5swEIb%2FysrnOMHYGJNb%2BqEqUluttNuVekLGOMEKwZbxQrOr%2FPeOE0j22HJh5hnP6xl439HY6A6tCSeZ4JwkCSV0gQ761KP1O%2FKmjq8BrRGFQkbzAhPNCGYqY1iKiuGMc7qrqBQqFWiB%2FkStlHKWJkXCk%2BS8QIOZNThNeUYkxTTTArOKU1wQpXAqE7qTRUVVwWaNOE8uioIzskAhtMBEEh9QVG5SfEfK1hqUSbEkZEmgObxBilOWQKy7eGsf9hB%2F25S%2Ftl8gzXmeE0Fy6LguDYNC%2FdXDFagJwfXr1Wocx%2BVr74Jd7u2wcjLoLvQrF2S1Ct7Itp8YvmRYdjWWzmkIKyt9jXVXL5twbEHYeVu%2FqlCGk4uTjrp66OsDFGo9GKXL0dShiSukIrnTRpt9EwDD0pE6D3EK0Wi62o4fui71id66OM2BPl7nhvw3ZM9e1voo%2FSGCnwC2j%2BV3OZaPtjXqVG67nZ0KLzC%2B9R%2FJZpCmLb%2B2WgVvO6PKT%2BatfDrdlLrQlhsVzGCC0TN91n0wR9udyientWpuhcrbsddxo8%2BNt0f9IAqgNpZ%2FSAWh1zvt%2FeUEZL0J8cvd%2FseEwKQzxVfqLkaFoLVKtrEHvH2%2BGarIUgaGymZDCc5mR7l2chS5208kDCyc0dl%2B7H56mE7Tf9G%2BbguW%2BJ%2B28%2Fkv',
            '_ga_CD30TTEK1F': 'GS1.1.1615866089.1.1.1615866100.0',
            '_gat': '1',
        }
        self.headers = {
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'ADRUM': 'isAjax:true',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://ptab.uspto.gov',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://ptab.uspto.gov/',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        self.auth_cookies = {
            '_ga_CD30TTEK1F': 'GS1.1.1615956693.4.1.1615957453.0',
            '_ga': 'GA1.1.290601150.1614925497',
            '_4c_': 'bVHBrpswEPyVyuc4scEYwy1VqypSVUV6ba%2FI2CZY4RlkHGgS5d%2B7Vgnta8uF3ZnZ2V3vHc2tcaiknGZFlrMsEQXfoLO5jqi8I291%2FE2oREyQXBhNMdFSYdbUFAuWcMxr0qQ5K%2FI6r9EG%2FYheSZITClCasccGaff00KaRly6ssjSjGRVccAIyO4RFF4fJ04KKPKHkrTYiUft0lOi%2FvJ9Xq4UQRUHfSiMC0mn1okJKzeoUM8YZht0krhPYsK4bmdI6yTQpnu3ia4mM5hkvNiiEDjBB4geOalgc70j12kTnYkvplkJxuEGKE0YgNi52HcMJ4k%2F76tvhA6RJQTihNCNbaMKKJINnBP7ioQVqQxjGcreb53l7GYfQb0%2F9tOuM9M66E5ZOY2%2FG%2FuKVGXd901hlZYdP8mZCMP8AeJDBuDCC%2FeB7fVGhCtchzjub%2Bt2oz0BoM1llqtnq0MZFEkF%2Bo62xpxaOhmD1iA4%2BLgDRbJ3u57%2BrFnSt4ixqj8sQJfoC2VcvtXmV%2FvwEDsfqs5yrY99Zda0OrukX4rsBN%2F8nsp%2Bk7aqPnVHB986q6r29VS%2FX1cmFrtqrYCcbrFkbmjHY195dq5fBGNUuxON5Z05YSuHOgix3Fpz9OvTj8RM%3D',
            'ADRUM': 's=1616095160444&r=https%3A%2F%2Fptab.uspto.gov%2F%3F-1483723136',
            '_gid': 'GA1.3.1332106114.1615871533',
            '_gat': '1',
        }

        self.auth_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:84.0) Gecko/20100101 Firefox/84.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhcHBsaWNhdGlvblVzZXJJZCI6MTUwMzc1LCJlbXBsb3llZUlkIjpudWxsLCJ1c2VySWQiOm51bGwsInVzZXJOYW1lIjoiYXJob2RlczNAdmlsbGFub3ZhLmVkdSIsImZpcnN0TmFtZSI6IkFuZHJldyIsIm1pZGRsZU5hbWUiOm51bGwsImxhc3ROYW1lIjoiUmhvZGVzIiwiZW1haWxJZCI6ImFyaG9kZXMzQHZpbGxhbm92YS5lZHUiLCJwaG9uZSI6bnVsbCwiaWF0IjoxNjE2MDk1MDgwOTYwLCJleHAiOjE2MTYwOTY5ODA0NzgsImlzcyI6IlBUQUJFMkUiLCJlbmRFZmZlY3RpdmVEYXRlIjpudWxsLCJyb2xlcyI6WyJQVEFCRTJFX0V4dGVybmFsX1VzZXIiXX0.3JaZsc-l5M8XG8QQoOBnqDznJ_FuPHLSsGGcmEJrCd4',
            'ADRUM': 'isAjax:true',
            'Connection': 'keep-alive',
            'Referer': 'https://ptab.uspto.gov/',
        }

        self.auth_params = (
            ('cacheFix', '1616095195994'),
        )

        self.cookies1 = {
            '_ga_CD30TTEK1F': 'GS1.1.1615738669.3.1.1615739194.0',
            '_ga': 'GA1.1.290601150.1614925497',
            '_4c_': 'jVRNb9swDP0rhc9VItmSLefWYR8osA4F2g3YyZAlJRbiWoKsxE2L%2FPdRie1s7TAsl5CP5JNIPvk1GRrdJSuSE1ZkJSkpweQ62epDn6xeE29U%2FNsnq4RyXHCtCMJKSETXNUGcpjnKa7zOCloWdVEn18lz5ErTAhOAMkaP14l0I8drsvMtUDUhuH61XA7DsNj1LtjFxu6XTgTdhX7pgqiXwRvR9iOGTh4SnULCOQ1mbYVXSHdq0YSnFo6VVmlgJuWCkAUBILyAi1KKwdZdbKAPG7C%2F3FTfbz%2BCm5Y4x4QwvIDeaZkyuC%2FEnbdqJ0MVDi4SDrq%2B6tUWAkrvjdTVYFRo4kkpxxe00WbTBIA5PqHOxxPAGkyn7PC2akTnqpzG3PvzAMD%2FCd6jF0o%2FCb%2BNwDcAbu%2Brr2Ko7m1r5KG67dZ2DPyAOVj%2FO3KzF6atPrVaBm87I6sP5qV6OMxMXWirGxnM3gSjJ%2FRR98E82e5QPTitZTMHam%2BHXseOPhuv1%2Fb5ilOAbYzfCQkmoNr7Uwp4vQlxdPNmRwg0NaHojLq4lgyM1krRxhqQYuzcbDba3%2BnQWJDfaRJwUduJuGkFaoWxr8WuDdGN85Ot6Hsjle63wbrkOMqQMJ4yxvOyLEAQAaTHc4rjDzL2ZlJ2xomkOMsQT7FAVEuQWa1LVBOcMsX0WtUkmSkLikvOy5KMlIRPjK4dGcklmWW4IFmeT8l0Pt%2Ftx%2BzszW05y97f9rwDUPw%2Fytj7MpjT%2FH5B5FpKhgqSEkTTrEYc3juiSgtMoaGc4eS%2FOLuJ8rKF86vPGGEEqvKYZlyYxjF%2BW3iREvxnbkRi7sQokr%2FG%2FTBTjYHzAp7fIMfj8Rc%3D',
            'ADRUM': 's=1615912841570&r=https%3A%2F%2Fptab.uspto.gov%2F%3F-618507588',
            '_gid': 'GA1.3.1332106114.1615871533',
            '_gat': '1',
        }

        self.headers1 = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:84.0) Gecko/20100101 Firefox/84.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/json;charset=utf-8',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhcHBsaWNhdGlvblVzZXJJZCI6MTUwMzc1LCJlbXBsb3llZUlkIjpudWxsLCJ1c2VySWQiOm51bGwsInVzZXJOYW1lIjoiYXJob2RlczNAdmlsbGFub3ZhLmVkdSIsImZpcnN0TmFtZSI6IkFuZHJldyIsIm1pZGRsZU5hbWUiOm51bGwsImxhc3ROYW1lIjoiUmhvZGVzIiwiZW1haWxJZCI6ImFyaG9kZXMzQHZpbGxhbm92YS5lZHUiLCJwaG9uZSI6bnVsbCwiaWF0IjoxNjE1OTUzMzYyMTcxLCJleHAiOjE2MTU5NTY5NDI4NDEsImlzcyI6IlBUQUJFMkUiLCJlbmRFZmZlY3RpdmVEYXRlIjpudWxsLCJyb2xlcyI6WyJQVEFCRTJFX0V4dGVybmFsX1VzZXIiXX0.KiOc6_4i21ssiZj3ZA9ocAwdCmLclKo6LStfJn-eGBg',
            'ADRUM': 'isAjax:true',
            'Origin': 'https://ptab.uspto.gov',
            'Connection': 'keep-alive',
            'Referer': 'https://ptab.uspto.gov/',
        }

        self.params1 = (
            ('cacheFix', '1615955158823'),
        )

        self.data1 = '{{"proceedingNumber":{},"patentNumber":"","applicationNumber":"","partyName":"","searchAlgType":1,"trailTypes":["IPR","PGR","CBM","DER"],"contentSearchString":"","filingParties":["PETITIONER","PATENT OWNER","BOARD"],"visibilityOptions":[],"techCenter":"","uploadedStartDate":"","uploadedEndDate":"","secondaryPartyName":"","additionalRPSelected":false,"counselSelected":false,"patentDescription":"","designPatentType":false,"reissuePatentType":false,"instRangeStartDate":"","instRangeEndDate":"","filingStartDate":"","filingEndDate":"","judgeEmpId":"","override":false,"isSearchPerformed":"N"}}'.format(self.patent)

        self.cookies2 = {
            '_ga_CD30TTEK1F': 'GS1.1.1615956693.4.1.1615957453.0',
            '_ga': 'GA1.1.290601150.1614925497',
            '_4c_': 'bVHBrpswEPyVyuc4scEYwy1VqypSVUV6ba%2FI2CZY4RlkHGgS5d%2B7Vgnta8uF3ZnZ2V3vHc2tcaiknGZFlrMsEQXfoLO5jqi8I291%2FE2oREyQXBhNMdFSYdbUFAuWcMxr0qQ5K%2FI6r9EG%2FYheSZITClCasccGaff00KaRly6ssjSjGRVccAIyO4RFF4fJ04KKPKHkrTYiUft0lOi%2FvJ9Xq4UQRUHfSiMC0mn1okJKzeoUM8YZht0krhPYsK4bmdI6yTQpnu3ia4mM5hkvNiiEDjBB4geOalgc70j12kTnYkvplkJxuEGKE0YgNi52HcMJ4k%2F76tvhA6RJQTihNCNbaMKKJINnBP7ioQVqQxjGcreb53l7GYfQb0%2F9tOuM9M66E5ZOY2%2FG%2FuKVGXd901hlZYdP8mZCMP8AeJDBuDCC%2FeB7fVGhCtchzjub%2Bt2oz0BoM1llqtnq0MZFEkF%2Bo62xpxaOhmD1iA4%2BLgDRbJ3u57%2BrFnSt4ixqj8sQJfoC2VcvtXmV%2FvwEDsfqs5yrY99Zda0OrukX4rsBN%2F8nsp%2Bk7aqPnVHB986q6r29VS%2FX1cmFrtqrYCcbrFkbmjHY195dq5fBGNUuxON5Z05YSuHOgix3Fpz9OvTj8RM%3D',
            'ADRUM': 's=1616013800421&r=https%3A%2F%2Fptab.uspto.gov%2F%3F-1483723136',
            '_gid': 'GA1.3.1332106114.1615871533',
            '_gat': '1',
        }

        self.headers2 = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:84.0) Gecko/20100101 Firefox/84.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhcHBsaWNhdGlvblVzZXJJZCI6MTUwMzc1LCJlbXBsb3llZUlkIjpudWxsLCJ1c2VySWQiOm51bGwsInVzZXJOYW1lIjoiYXJob2RlczNAdmlsbGFub3ZhLmVkdSIsImZpcnN0TmFtZSI6IkFuZHJldyIsIm1pZGRsZU5hbWUiOm51bGwsImxhc3ROYW1lIjoiUmhvZGVzIiwiZW1haWxJZCI6ImFyaG9kZXMzQHZpbGxhbm92YS5lZHUiLCJwaG9uZSI6bnVsbCwiaWF0IjoxNjE2MDgzMTIxMzk3LCJleHAiOjE2MTYwODcyMjMxNjEsImlzcyI6IlBUQUJFMkUiLCJlbmRFZmZlY3RpdmVEYXRlIjpudWxsLCJyb2xlcyI6WyJQVEFCRTJFX0V4dGVybmFsX1VzZXIiXX0.rf78zSQTF90FdTbCPW6wIcBSQtgDF1ZnYR8dtVSp00c',
            'Connection': 'keep-alive',
            'Referer': 'https://ptab.uspto.gov/',
        }

        self.params2 = (
            ('cacheFix', '1616027845608'),
            ('extUserSearchView', 'Y'),
        )

        self.cookies3 = {
            '_ga_CD30TTEK1F': 'GS1.1.1615956693.4.1.1615957453.0',
            '_ga': 'GA1.1.290601150.1614925497',
            '_4c_': 'bVHBrpswEPyVyuc4scEYwy1VqypSVUV6ba%2FI2CZY4RlkHGgS5d%2B7Vgnta8uF3ZnZ2V3vHc2tcaiknGZFlrMsEQXfoLO5jqi8I291%2FE2oREyQXBhNMdFSYdbUFAuWcMxr0qQ5K%2FI6r9EG%2FYheSZITClCasccGaff00KaRly6ssjSjGRVccAIyO4RFF4fJ04KKPKHkrTYiUft0lOi%2FvJ9Xq4UQRUHfSiMC0mn1okJKzeoUM8YZht0krhPYsK4bmdI6yTQpnu3ia4mM5hkvNiiEDjBB4geOalgc70j12kTnYkvplkJxuEGKE0YgNi52HcMJ4k%2F76tvhA6RJQTihNCNbaMKKJINnBP7ioQVqQxjGcreb53l7GYfQb0%2F9tOuM9M66E5ZOY2%2FG%2FuKVGXd901hlZYdP8mZCMP8AeJDBuDCC%2FeB7fVGhCtchzjub%2Bt2oz0BoM1llqtnq0MZFEkF%2Bo62xpxaOhmD1iA4%2BLgDRbJ3u57%2BrFnSt4ixqj8sQJfoC2VcvtXmV%2FvwEDsfqs5yrY99Zda0OrukX4rsBN%2F8nsp%2Bk7aqPnVHB986q6r29VS%2FX1cmFrtqrYCcbrFkbmjHY195dq5fBGNUuxON5Z05YSuHOgix3Fpz9OvTj8RM%3D',
            'ADRUM': 's=1616008668552&r=https%3A%2F%2Fptab.uspto.gov%2F%3F-1483723136',
            '_gid': 'GA1.3.1332106114.1615871533',
            '_gat': '1',
        }

        self.headers3 = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:84.0) Gecko/20100101 Firefox/84.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhcHBsaWNhdGlvblVzZXJJZCI6MTUwMzc1LCJlbXBsb3llZUlkIjpudWxsLCJ1c2VySWQiOm51bGwsInVzZXJOYW1lIjoiYXJob2RlczNAdmlsbGFub3ZhLmVkdSIsImZpcnN0TmFtZSI6IkFuZHJldyIsIm1pZGRsZU5hbWUiOm51bGwsImxhc3ROYW1lIjoiUmhvZGVzIiwiZW1haWxJZCI6ImFyaG9kZXMzQHZpbGxhbm92YS5lZHUiLCJwaG9uZSI6bnVsbCwiaWF0IjoxNjE2MDQzMTIyODk4LCJleHAiOjE2MTYwNDQ5NTAwMjgsImlzcyI6IlBUQUJFMkUiLCJlbmRFZmZlY3RpdmVEYXRlIjpudWxsLCJyb2xlcyI6WyJQVEFCRTJFX0V4dGVybmFsX1VzZXIiXX0.q7X9osBcDaZ9VQ-64dTyNcINmsQJg-qfEaZ5L4_2SS0',
            'ADRUM': 'isAjax:true',
            'Connection': 'keep-alive',
            'Referer': 'https://ptab.uspto.gov/',
        }

        self.c = True
        self.d = True

    def scrape(self):

        with requests.Session() as r:
            # Request authorization token from website upon login
            r.trust_env = True
            response = r.post ( self.url_origin, headers=self.headers, params=self.params, cookies=self.cookies, data=self.data )
            token = response.headers['Authorization']
            self.headers2['Authorization'] = token

            # Get initial status
            r.post ( self.url_origin, headers=self.headers, params=self.params, cookies=self.cookies,
                     data=self.data )
            r.get ( self.url_search )
            session = r.post ( self.url_enter, headers=self.headers1, params=self.params1,
                               cookies=self.cookies1, data=self.data1 )
            status_0 = session.json ()['searchResults'][0]['roleBasedState']

            # Get initial document count
            r.post ( self.url_origin, headers=self.headers, params=self.params, cookies=self.cookies, data=self.data )
            r.get ( self.url_search )
            r.post ( self.url_enter, headers=self.headers1, params=self.params1,
                     cookies=self.cookies1, data=self.data1 )

            response = r.get (self.url_doc_view,
                               headers=self.headers2,
                               params=self.params2, cookies=self.cookies2)

            doc_count_0 = len ( response.json () )

            while self.c or self.d:
                # Check for status change

                r.post ( self.url_origin, headers=self.headers, params=self.params, cookies=self.cookies,
                         data=self.data )
                r.get ( self.url_search )
                session = r.post ( self.url_enter, headers=self.headers1, params=self.params1,
                         cookies=self.cookies1, data=self.data1 )
                status_1 = session.json()['searchResults'][0]['roleBasedState']
                print(status_1)
                if status_1 != status_0:
                    ptab.send_status(status_0, status_1)
                    self.c = False

                # Check for document upload
                r.post(self.url_origin, headers=self.headers, params=self.params, cookies=self.cookies, data=self.data)
                r.get(self.url_search)
                r.post(self.url_enter, headers=self.headers1, params=self.params1,
                                cookies=self.cookies1, data=self.data1, allow_redirects=False)
                response = r.get (self.url_doc_view,
                                          headers=self.headers2,
                                          params=self.params2, cookies=self.cookies2, allow_redirects=False )
                token = response.headers['Authorization']
                # Replace authorization token with updated one (expires every 30 mins.)
                self.headers2['Authorization'] = token
                r.post ( self.url_origin, headers=self.headers, params=self.params, cookies=self.cookies,
                         data=self.data )
                r.get ( self.url_search )
                r.post ( self.url_enter, headers=self.headers1, params=self.params1,
                         cookies=self.cookies1, data=self.data1, allow_redirects=False )
                response = r.get ( self.url_doc_view,
                                   headers=self.headers2,
                                   params=self.params2, cookies=self.cookies2, allow_redirects=False )
                doc_count_1 = len(response.json())

                # Check HTTPS status
                if response.status_code == 200:
                    print('Status code {}: Request successful'.format(response.status_code))
                else:
                    print('Error. HTTPS status code {}'.format(response.status_code))

                # Pull objectId of most recent document
                objectid = response.json ()[-1]['objectId']


                # If doc_count is different from initial doc count, download document
                if doc_count_0 != doc_count_1:
                    self.headers3['Authorization'] = token
                    ptab.doc_download(objectid)
                    self.d = False
                print(doc_count_0)

                # Pause for 5 seconds before running through loop again
                time.sleep(5)

    def doc_download(self, objectId):

        with requests.Session () as r:
            # Login and navigate to document child window
            r.post ( self.url_origin, headers=self.headers, params=self.params, cookies=self.cookies, data=self.data )
            r.get ( self.url_search )
            r.post ( self.url_enter, headers=self.headers1, params=self.params1,
                     cookies=self.cookies1, data=self.data1 )
            request = r.get ( self.url_doc_view,
                    headers=self.headers2,
                    params=self.params2, cookies=self.cookies2 )

            # Pull document title from return headers
            title = request.json()[-1]['documentName']

            # Login once more, navigate to child window and download document
            r.post ( self.url_origin, headers=self.headers, params=self.params, cookies=self.cookies, data=self.data )
            r.get ( self.url_search )
            r.post ( self.url_enter, headers=self.headers1, params=self.params1,
                     cookies=self.cookies1, data=self.data1 )
            r.get ( self.url_doc_view,
                              headers=self.headers2,
                              params=self.params2, cookies=self.cookies2 )
            request = r.get (
                'https://ptab.uspto.gov/ptabe2e/rest/petitions/1539888/documents/{}/download'.format ( objectId ),
                headers=self.headers3, cookies=self.cookies3 )
            name = self.patent.strip('""')

            # Write downloaded document to pdf file of working directory
            with open('{}_doc.pdf'.format(name), 'wb') as f:
                f.write(request.content)
                # Send document via send_doc function
                ptab.send_doc(title)

    def send_status(self, status_0, status_1):
        # Send status change info. via email through smtp server
        with smtplib.SMTP_SSL ( "smtp.gmail.com", self.port, context=self.context ) as server:
            server.login ( self.email_username, self.pword )
            server.sendmail(self.sending_email,self.receiving_email, 'The status in {} changed from {} to {}.'.format(self.patent,status_0, status_1))

    def send_doc(self, title):
        # Send document
        message = MIMEMultipart ()
        message['From'] = self.sending_email
        message['To'] = self.receiving_email
        message['Subject'] = 'A new document was uploaded for {} with the title {}. See attached.'.format(self.patent, title)

        name = self.patent.strip ( '""' )
        pdfname = '{}_doc.pdf'.format(name)
        # open the file
        binary_pdf = open (pdfname, 'rb')

        payload = MIMEBase ('application', 'octate-stream', Name=pdfname)
        payload.set_payload ((binary_pdf).read())

        # enconding the binary into base64
        encoders.encode_base64 (payload)

        # add header with pdf name
        payload.add_header ('Content-Decomposition', 'attachment', filename=pdfname)
        message.attach ( payload )

        session = smtplib.SMTP ('smtp.gmail.com', self.port)

        # enable security
        session.starttls()

        # login with sending email and password
        session.login(self.sending_email, self.pword)

        text = message.as_string ()
        session.sendmail(self.sending_email, self.receiving_email, text)
        session.quit()
        print ('Mail Sent')



ptab = ptab('"IPR2020-01402"', 'arhodes4@ycp.edu')
ptab.scrape()
