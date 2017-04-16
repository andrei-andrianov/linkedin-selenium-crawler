import argparse, os, time, random, json
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from datetime import datetime

#?session_redirect=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fdaria-abarkina-870b9263
#www.linkedin.com/in/davidstew/
#link to start crawling after UAS auth
startLink = "https://www.linkedin.com/uas/login?session_redirect=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fahmed-omar-b5ab3b12b%2F&fromSignIn=true&trk=uno-reg-join-sign-in"

#output files
logFileName = "linkedin_selenium_crawler.log"
logFile = open(logFileName,"w")

outputFileName = "linkedin_data.json"
outputFile = open(outputFileName, "w")

#dictionary to avoid
dict = ["Company Name",
		"Dates Employed",
		"Employment Duration",
		"Location",
		"Degree Name",
		"Field Of Study",
		"Dates attended or expected graduation",
		"Dates volunteered",
		"Volunteer duration",
		"Cause"]

class Entity:
	link = ""
	name = ""
	headline = ""
	experience = []
	education = []
	volonteering = []
	skills = []
	
def getTime():
	return str(datetime.now().strftime("%I:%M:%S%p"))

def getPeopleLinks(soup, name):
	links = []
	name = magicTrick(name)
	name1 = ""
	name2 = ""
	for str in name:
		if str:
			name1 += str
			name2 += str
			name2 += "-"
	#logFile.write("[DEBUG] name1 = "+name1+"| name2 = "+name2)
	for link in soup.find_all('a'):
		url = link.get('href')
		if url:
			if "/in/" in url:
				logFile.write("[+]["+getTime()+"] Found /in/ link:"+url+"\n")
				if name1 in url or name2 in url or "%" in url:
					logFile.write("[+] Chunk off useless links since "+name1+" or "+name2+" is in url:\n\t"+url+"\n")
					continue
				else:
					links.append(url)
					logFile.write("[+]["+getTime()+"] Added to queue:"+url+"\n")
	logFile.write("[+]["+getTime()+"] Links added to queue from current page:"+repr(len(links))+"\n\n")
	return links
	

def magicTrick(name):
	output = []
	name = name.lower()
	name = name.split(" ")
	for str in name:
		if str == " ":
			continue
		else:
			output.append(str)
	return output
	
def getID(url):
	parsedUrl = urlparse(url)
	return parsedUrl.geturl()

def parsePage(soup, entity, url):
	entity.link = url
	entity.name = soup.h1.contents[0]
	entity.headline = soup.h2.contents[0]
	entity.experience = []
	entity.education = []
	entity.volonteering = []

	#parse experience section
	exp_section = soup.find("section", class_="pv-profile-section experience-section ember-view")
	if exp_section:
		exp_list = exp_section.find_all("li")
		for li in exp_list:
			e = li.find("div", class_="pv-entity__summary-info")
			exp = {}
			k = 0
			if e:
				exp['position'] = e.h3.text
				for h4 in e.find_all("h4"):
					strl = h4.text.split("\n")
					for str in strl:
						if str and str not in dict:
							k += 1
							if k == 1:
								exp['company'] = str
							if k == 2:
								exp['period'] = str
							if k == 3:
								exp['duration'] = str
							if k == 4:
								exp['location'] = str
			entity.experience.append(exp)
	#parse education section
	edu_section = soup.find("section", id="education-section")
	if edu_section:
		edu_list = edu_section.find_all("li")
		for li in edu_list:
			e = li.find("div", class_="pv-entity__summary-info")
			edu = {}
			k = 0
			if e:
				edu['name'] = e.h3.text
				for p in e.find_all("p"):
					strl = p.text.split("\n")
					for str in strl:
						if str and str not in dict:
							k += 1
							if k == 1:
								edu['degree'] = str
							if k == 2:
								edu['field'] = str
							if k == 3:
								edu['dates'] = str
			entity.education.append(edu)
	#parse volonteering section
	vol_section = soup.find("section", id="volunteering-section")
	if vol_section:
		vol_list = vol_section.find_all("li")
		for li in vol_list:
			v = li.find("div", class_="pv-entity__summary-info")
			vol = {}
			k = 0
			if v:
				vol['duty'] = v.h3.text
				for h4 in v.find_all("h4"):
					strl = h4.text.split("\n")
					for str in strl:
						if str and str not in dict:
							k += 1
							if k == 1:
								vol['company'] = str
							if k == 2:
								vol['period'] = str
							if k == 3:
								vol['duration'] = str
							if k == 4:
								vol['cause'] = str
			entity.volonteering.append(vol)
	#parse skills section
	skill_section = soup.find("div", class_="pv-deferred-area__content")
	if skill_section:
		skill_list = skill_section.find_all("li")
		for li in skill_list:
			s = li.find("div", class_="tooltip-container")
			if s:
				strl = s.a.text.split("\n")
				for str in strl:
					if str and not "see" in str and not "See" in str:
						skill = str
						entity.skills.append(skill)
	jsonData = json.dumps(entity.__dict__)
	outputFile.write(jsonData+"\n")
	
	return entity
	
def tinyBot(browser):
	visited = {}
	pList = []
	count = 0
	while True:
		#sleep to make sure everything loads, add random to make us look human
		time.sleep(random.uniform(2.2,3.8))
		soup = BeautifulSoup(browser.page_source.encode('utf-8'), 'lxml')
		entity = Entity()
		entity = parsePage(soup, entity, browser.current_url)
		people = getPeopleLinks(soup, entity.name)
		
		if people:
			for person in people:
				ID = getID(person)
				if ID not in visited:
					pList.append(person)
					visited[ID] = 1
		if pList: #if there is people to visit
			random.shuffle(pList)
			person = pList.pop()
			newUrl = str("https://linkedin.com"+person)
			browser.get(newUrl)
			count += 1
		else:
			print ("I'm lost")
			if count < 100:
				logFile.write("[+]["+getTime()+"] Visited less than 100 people. Trying to continue..\n")
				continue
			else:
				break
	
		logFile.write("[+]["+getTime()+"] "+str(entity.name)+" Visited! | "+str(count)+"/"+str(len(pList))+" Visited/Queue\n")
					

def Main():
	argParser = argparse.ArgumentParser()
	argParser.add_argument("email", help="linkedin email")
	argParser.add_argument("password", help="linkedin password")
	args = argParser.parse_args()

	browser = webdriver.Chrome("chromedriver.exe")

	browser.get(startLink)


	emailElement = browser.find_element_by_id("session_key-login")
	emailElement.send_keys(args.email)
	passElement = browser.find_element_by_id("session_password-login")
	passElement.send_keys(args.password)
	passElement.submit()

	os.system('cls')
	logFile.write("[+]["+getTime()+"] Successfuly logged in! Bot is starting..\n")
	
	tinyBot(browser)

if __name__ == '__main__':
	Main()