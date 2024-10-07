import requests
import re
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse
from tqdm import tqdm 
import json


class VideoScraper:
    def __init__(self, url):
        self.url = url
        self.video = {}
        self.getVideoTitle = ''
        self.originalVideoTitle = ''
        self.invalid_chars = r'[\\/:*?"<>|]'
        self.checkRenameVideo = False



    def checkSoupAvailable(self, getPreviousLink):
        if getPreviousLink != None:
            return True
        else:
            return False
        
    def is_valid_name(self, name):
        return not re.search(self.invalid_chars, name)
    
    # Prompt the user to input a valid folder name
    def get_valid_name(self):
        while True:
            title = input("Enter a valid name: ")
            if self.is_valid_name(title):
                return title
            else:
                print("The name contains invalid characters. Please try again.")

                    
  

    def getVideoID(self):

        #get html content
        r = requests.get(self.url)
        soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib
        #print(soup.prettify())


        #find and get Video title
        if self.getVideoTitle == '':
            videoTitle = soup.find('h1', class_='page-title')
            checkVideoTitle = self.checkSoupAvailable(videoTitle)

            if checkVideoTitle:
                self.getVideoTitle = videoTitle.text
                # Check if the video title contains invalid characters
                if not self.is_valid_name(self.getVideoTitle):
                    print(f"The name contains invalid characters.")
                    self.originalVideoTitle = self.getVideoTitle
                    self.getVideoTitle = self.get_valid_name()
                    self.checkRenameVideo = True
            else:
                self.getVideoTitle = "output"

            print(self.getVideoTitle)


        # Find all articles
        articles = soup.find_all('article')
        for article in articles:
            videoName = article.find('h2', class_='entry-title').text
            videoID = article.find('video')['data-apireq']
            
            if self.checkRenameVideo:
                new_videoName = re.sub(re.escape(self.originalVideoTitle), self.getVideoTitle, videoName)
                self.video[new_videoName] = videoID
            else:
                self.video[videoName] = videoID

        #if there are more than 1 page will get the link and repeat
        getPreviousLink = soup.find(class_="nav-previous")
        checkPreviousLink = self.checkSoupAvailable(getPreviousLink)
      

        if checkPreviousLink:
            self.url = getPreviousLink.find('a')["href"]
            self.getVideoID()
            return
        
        # Pass the video details to DownloadVideo class to download
        postData = ResponsePostGetURL(self.video, self.getVideoTitle)
        postData.requestsPost()

    


class ResponsePostGetURL:
    def __init__(self, video, videoTitle):
        self.videoNameAndURL = {}
        self.videoData = video
        self.videoTitle = videoTitle
        self.post_url = "https://v.anime1.me/api"  # Change this to your actual POST URL
        # The headers captured from the browser (for example, you might need cookies, tokens, etc.)
        self.headers = {
            "Host": "v.anime1.me",
            "Content-Length": "138",
            "Referer": "https://anime1.me/",
            "Origin": "https://anime1.me/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Connection": "keep-alive",
         #   "Cookie": "_ga=GA1.1.538806435.1651934006; _ga_1QW4P0C598=GS1.1.1681516178.10.1.1681516358.0.0.0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded",
            "Alt-Used": "v.anime1.me",
            "Priority": "u=0"
        }


        
    def selectAndExtractURL(self, response):
        # Parse the JSON string into a Python dictionary
        data = json.loads(response.text)
        # Extract the 'src' fields from the parsed JSON
        for item in data['s']:
            if "mp4" in item['src']:
                return f"https:{item['src']}"
    

    def requestsPost(self):
        for key, values in self.videoData.items():
            data = f"d={values}"

            # Create a session to handle cookies automatically
            session = requests.Session()

            # Send the POST request to simulate clicking the play button
            response = session.post(self.post_url, headers=self.headers, data=data) 

            sessionCookies = session.cookies.get_dict()

            # Check the response
            if response.status_code == 200:
                videoURL = self.selectAndExtractURL(response)
                print(videoURL)
                self.videoNameAndURL[key] = videoURL
                downloadVideo = DownloadVideo(key, videoURL, sessionCookies, self.videoTitle)
                downloadVideo.requestsGetVideo()
            else:
                print(f"Failed to play video. Status code: {response.status_code}")




class DownloadVideo:
    def __init__(self, name, url, sessionCookies, videoTitle):
        self.videoName = name
        self.videoURL = url
        self.sessionCookies = sessionCookies
        self.videoTitle = videoTitle
    
    def setHeaders(self):
        # Combine cookies into a single string for the header
        cookie_string = '; '.join([f'{key}={value}' for key, value in self.sessionCookies.items()])

        headers = {
            "Host": urlparse(self.videoURL).netloc,
            "Referer": self.videoURL,
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Cookie": f"{cookie_string}; ",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "TE": "trailers",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Priority": "u=0, i",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"

        }

        return headers


    def createFolder(self, folder):
        # Create a download directory if it doesn't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        newpath = os.path.join(script_dir, folder)
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        videoFolder = os.path.join(newpath, self.videoTitle)
        if not os.path.exists(videoFolder):
            os.makedirs(videoFolder)
        
        return videoFolder
    
    def downloadVideoMP4(self, response, outputFolder):
        # Get the total file size from the headers
        total_size = int(response.headers.get('content-length', 0))
                # Open the file in write-binary mode
        with open(f"{outputFolder}/{self.videoName}.mp4", "wb") as f:
            # Use tqdm to show progress with the file size
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=self.videoName, ascii=True) as progress_bar:
                # Download the file in chunks
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        progress_bar.update(len(chunk))

    
        

    def requestsGetVideo(self):
        outputFolder = self.createFolder("output")
   
        response = requests.get(self.videoURL, headers=self.setHeaders(), stream=True)
        if response.status_code == 200:
            self.downloadVideoMP4(response, outputFolder)
           # print(f'{self.videoName} : {urlparse(self.videoURL).netloc}')
    
        else:
            print(f"Failed to download {self.videoName}: {self.videoURL} (Status Code: {response.status_code})")
              
                


url = input("Enter url: ")


# Create an instance of the class
scraper = VideoScraper(url)
scraper.getVideoID()








