from bs4 import BeautifulSoup
import pandas as pd 
import numpy as np
import requests
from selenium import webdriver
import smtplib
import time

t0 = time.time()
elapsed_time = 0

email_acct = r'' #email account to send from
email_pwd = r'' #password to email account
to_email = r'' #email account to send to
subject = 'Vaccine appointment found' #subject line of email
smtp_server = 'smtp.gmail.com' #SMTP server
smtp_port = 587 #SMTP port
max_total_runtime = np.inf 
sleeptime = 300

def update_dataframe(site):
	
	title = site.find('h5', {'class': 'card-title mb-2'}).text
	availability = site.find('h6', {'class': 'card-subtitle mb-4'}, style=True)
	
	if availability.text == 'Appointments available':
		availability = True
	else:
		availability = False
	
	county = site.findAll('h6', {'class': 'card-subtitle mb-4 text-muted'})
	
	address = county[0].text.split(': ')[-1].strip()

	zipcode = address.split('IL')[-1].strip()
	
	county = county[-1].text.split(':')[-1].strip()
	
	try:
		zipcode = int(zipcode)
	except:
		zipcode = 0
	return [title, availability, county, address, zipcode]


def explode_vector(row):
	return  [x for x in row]

while elapsed_time < max_total_runtime:

	host_website = 'https://www.ilvaccine.org/'

	page = requests.get(host_website)
	soup = BeautifulSoup(page.content, "html")

	options = webdriver.FirefoxOptions()
	options.headless = True
	options.add_argument("window-size=1400,600")
	driver = webdriver.Firefox()

	driver.get(host_website)

	time.sleep(5)
	content = driver.page_source.encode('utf-8').strip()

	soup = BeautifulSoup(content,"html.parser")

	all_cards = soup.findAll('div', {'class':"card ml-4 mr-4 mb-2"})

	vaccine_df = pd.DataFrame({'sites': all_cards})

	vaccine_df['status'] = vaccine_df['sites'].apply(update_dataframe)

	updated_df = vaccine_df.apply(lambda x: explode_vector(x['status']),  axis =1, result_type='expand')
	updated_df.columns = ['Name', 'Availability', 'Address', 'County', 'Zip'] 

	full_vaccine_df = pd.concat([vaccine_df, updated_df], axis='columns')

	# 50km from 60202
	list_of_zip_codes_near_evanston = [0, 60202,60204,60645,60626,60208,60201,60203,60076,60660,60659,60712,60077,60091,60625,60646,60043,60640,60630,60029,60053,60613,60618,60714,60657,60093,60641,60631,60647,60614,60025,60082,60068,60706,60656,60022,60639,60634,60622,60642,60026,60651,60610,60707,60065,60062,60611,60017,60654,60674,60019,60612,60661,60624,60606,60176,60016,60601,60602,60302,60171,60603,60607,60644,60018,60604,60303,60301,60689,60305,60701,60666,60605,60304,60131,60056,60161,60608,60160,60035,60664,60668,60669,60670,60673,60675,60677,60678,60680,60681,60684,60685,60686,60687,60688,60690,60691,60693,60694,60696,60697,60699,60695,60623,60153,60130,60164,60616,60070,60165,60682,60804,60090,60040,60037,60105,60399,60106,60141,60015,60104,60009,60155,60402,60163,60653,60609,60632,60546,60005,60006,60191,60007,60162,60154,60004,60126,60513,60615,60069,60534,60526,60089,60045,60638,60143,60636,60629,60621,60008,60637,60181,60101,60173,60038,60055,60078,60094,60501,60558,60523,60095,60649,60157,60499,60525,60652,60599,60074,60521,60061,60148,60620,60067,60179,60459,60044,60619,60159,60168,60522,60196,60456,60458,60193,60117,60088,60455,60195,60139,60514,60805,60172,60194,60454,60108,60086,60559,60048,60047,60138,60064,60169,60137,60457,60199,60453,60415,60655,60515,60617,60527,60643,60480,60628,60133,60465,60188,60085,60482,60189,60197,60116,60128,60132,60079,60011,60060,60192]

	full_vaccine_df = full_vaccine_df[pd.DataFrame(full_vaccine_df.Zip.tolist()).isin(list_of_zip_codes_near_evanston).any(1).values]
	available = full_vaccine_df.loc[full_vaccine_df.Availability]

	
	if (full_vaccine_df.shape[0] != 0) and (available.shape[0] != 0):
		for index, row in full_vaccine_df.iterrows():
			if ((row['Zip'] == 0) and row['County'] == 'Cook') or (row['Zip'] != 0):
				ready_text = f'''
				Location Name: {row['Name']}
				County Name: {row['County']}
				Zipcode: {row['Zip']}
				Address: {row['Address']}
				'''
				server = smtplib.SMTP(smtp_server, smtp_port)
				server.starttls()
				server.login(email_acct, email_pwd)
				server.sendmail(email_acct, to_email, ready_text)
				
				print(f'Sending {index} of {full_vaccine_df.shape[0]} email')

	elapsed_time = time.time()-t0
	time.sleep(sleeptime)

driver.quit()

