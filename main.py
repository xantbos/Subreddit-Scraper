import requests
import html
import json
import os
from bs4 import BeautifulSoup
import re
import threading

#Simple script to scrape a subreddit's new rss and find regex-matched content.
#Originally designed to scrape game keys for closed betas and whatnot.
#If the config's regex is matched in a new post's content, the bot will scrape the keys and put them
#into a file designated by the config and then open the file for the user.

#Just wish I was better with tkinter so this would look better.

#Global access config file
with open('config.json', encoding="utf8") as file:
    config_file = json.load(file)

#Reddit reading class
class RedditReader:

	#Init functionality for the class
	def __init__(self):
		self.sub = config_file["subreddit"]
		self.subFormat = "https://www.reddit.com/r/{}/new/.rss"
		self.headers = { "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36" }
		self.postList = [] # list of RedditPost objects
		self.firstRun = True # First scrape flag
		print("\nBeginning rss read of {}".format(self.subFormat.format(self.sub)))
		print("") # formatting
		
	#Function to read the rss feed of a subreddit
	def readRssXML(self):
		try: 
			r = requests.get(self.subFormat.format(self.sub), headers=self.headers)
		except: 
			print("Error reading the subreddit data.")
			threading.Timer(15.0, self.readRssXML).start() # 15 second grace for network issues
			return
		soup = BeautifulSoup(r.text, 'lxml-xml') # format the xml rss feed
		for entry in soup.find_all("entry"): # find all marked entry fields
			thisPost = RedditPost(entry) # send to the RedditPost class which parses automatically
			if not thisPost in self.postList: # make sure this post doesn't already exist in our list 
				self.postList.append(thisPost) # add it to our list
				print(thisPost) # print the post for the user to see
				if not self.firstRun:
					if thisPost.has_keys(): # check if this post has keys in it
						self.dump_keys(thisPost) # if so we dump the keys
		print("----")
		self.firstRun = False
		threading.Timer(8.0, self.readRssXML).start() # 8 seconds since reddit's API likes 1 request ~5s or so
		
	#Function to append list of keys to an output file
	def dump_keys(self, post):
		oldData = None # prevent possible nonetype errors
		with codecs.open(config_file["keyfile"], mode="r", encoding="utf-8") as f:
			oldData = f.read() # take current data into our var
		outContent = None
		if oldData is None: oldData = "" # prevent crashes
		if isinstance(post.get_keys(), (list, tuple)): # check if we get back a list
			outContent = "\n".join(post.get_keys()) + "\n" + oldData # merge the list with our old data
		else:
			outContent = post.get_keys() + "\n" + oldData # merge the text with our old data
		if not outContent is None: # if we generated something and there wasn't some glitch
			with codecs.open(config_file["keyfile"], mode="w", encoding="utf-8") as f:
				f.write(outContent)
			if config_file["openkeyfile"] == 1:
				os.startfile(config_file["keyfile"]) # open our file for the user

#Class to store the basic info of a reddit post				
class RedditPost:

	#Init functionality for the class
	def __init__(self, post):
		self.author = None # post author
		self.id = None # post id
		self.link = None # post url
		self.title = None # post title
		self.content = None # post body content
		self.keys = None # potential list of keys
		self.parsePost(post) # instead of packing the init with more content we made a func
	
	#Comparator override
	def __eq__(self, item2):
		return True if self.id == item2.id else False # reddit post ids are unique
		
	#str() Override
	def __str__(self):
		return "{} - {}".format(self.id, self.link) # return id and html link
		
	#Bool method to see if we regex'd keys
	def has_keys(self):
		return True if self.keys else False
		
	#Function to return the keys
	def get_keys(self):
		return self.keys
		
	#Function to 'parse' a post
	#'Parse' because we're just using bs4's amazing ability
	def parsePost(self, post):
		self.author = post.author.name
		self.id = post.id.get_text()
		self.title = post.title.get_text()
		self.link = post.link["href"]
		self.content = html.unescape(post.content.get_text()) #Unescape to prevent symbols
		self.scrape_keys() # Attempt to scrape keys
		
	#Function to regex for keys and store them
	#Will terminate on first successful match
	def scrape_keys(self):
		for expression in config_file["regex"]: # cycle through all regex demands
			regex = r"{}".format(expression) # create the regex
			list = re.findall(regex, self.content) # attempt to match
			if len(list) > 0: # if we got a match
				self.keys = list # store the matched data
				break # we've matched so end the loop
			else: # no match
				self.keys = None # set to none to ensure no glitches

if __name__=="__main__":
	subScrub = RedditReader()
	subScrub.readRssXML()