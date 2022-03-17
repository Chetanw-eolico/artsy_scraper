# -*- coding: utf-8 -*-
import os, sys, re
import urllib, urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import unicodedata
import io
import gzip
import time
import simplejson as json
import datetime
import string
import requests
#from requests_toolbelt.adapters.source import SourceAddressAdapter
from urllib.parse import urlencode, quote_plus
import html
import csv
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
import subprocess


partialUrlPattern = re.compile("^/\w+")

def decodeHtmlEntities(content):
    entitiesDict = {'&nbsp;' : ' ', '&quot;' : '"', '&lt;' : '<', '&gt;' : '>', '&amp;' : '&', '&apos;' : "'", '&#160;' : ' ', '&#60;' : '<', '&#62;' : '>', '&#38;' : '&', '&#34;' : '"', '&#39;' : "'"}
    for entity in entitiesDict.keys():
        content = content.replace(entity, entitiesDict[entity])
    return(content)


# Implement signal handler for ctrl+c here.
def setSignal():
    pass

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.response.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302


def unicodefraction_to_decimal(v):
    fracPattern = re.compile("(\d*)\s*([^\s\.\,;a-zA-Z]+)")
    fps = re.search(fracPattern, v)
    if fps:
        fpsg = fps.groups()
        wholenumber = fpsg[0]
        fraction = fpsg[1]
        decimal = round(unicodedata.numeric(fraction), 3)
        if wholenumber:
            decimalstr = str(decimal).replace("0.", ".")
        else:
            decimalstr = str(decimal)
        value = wholenumber + decimalstr
        return value
    return v


class ArtsyBot(object):
    
    htmltagPattern = re.compile("\<\/?[^\<\>]*\/?\>", re.DOTALL)
    pathEndingWithSlashPattern = re.compile(r"\/$")

    htmlEntitiesDict = {'&nbsp;' : ' ', '&#160;' : ' ', '&amp;' : '&', '&#38;' : '&', '&lt;' : '<', '&#60;' : '<', '&gt;' : '>', '&#62;' : '>', '&apos;' : '\'', '&#39;' : '\'', '&quot;' : '"', '&#34;' : '"'}

    def __init__(self, targeturl, section, logfile="/tmp/artsybot.log"):
        # Create the opener object(s). Might need more than one type if we need to get pages with unwanted redirects.
        self.opener = urllib.request.build_opener(urllib.request.HTTPHandler(), urllib.request.HTTPSHandler()) # This is my normal opener....
        self.no_redirect_opener = urllib.request.build_opener(urllib.request.HTTPHandler(), urllib.request.HTTPSHandler(), NoRedirectHandler()) # ... and this one won't handle redirects.
        #self.debug_opener = urllib.request.build_opener(urllib.request.HTTPHandler(debuglevel=1))
        # Initialize some object properties.
        self.sessionCookies = ""
        self.httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',  'Accept' : '*/*', 'Accept-Language' : 'en-US,en;q=0.5', 'Accept-Encoding' : 'gzip,deflate', 'Connection' : 'keep-alive', 'Cache-Control' : 'no-cache', 'Content-Type' : 'application/json', 'Host' : 'metaphysics-production.artsy.net', 'Origin' : 'https://www.artsy.net', 'Pragma' : 'no-cache', 'Referer' : 'https://www.artsy.net/'}
        self.httpHeaders['authority'] = "metaphysics-production.artsy.net"
        self.httpHeaders['sec-fetch-dest'] = "empty"
        self.httpHeaders['sec-fetch-mode'] = "cors"
        self.httpHeaders['sec-fetch-site'] = "same-site"
        self.httpHeaders['TE'] = 'trailers'
        self.httpHeaders['X-TIMEZONE'] = 'Asia/Kolkata'
        self.homeDir = os.getcwd()
        self.requestUrl = targeturl
        print(self.requestUrl)
        self.section = section
        parsedUrl = urlparse(self.requestUrl)
        self.baseUrl = parsedUrl.scheme + "://" + parsedUrl.netloc
        data = {}
        postdata = urllib.parse.urlencode(data).encode("utf-8")
        self.pageRequest = urllib.request.Request(self.requestUrl, postdata, headers=self.httpHeaders)
        self.pageResponse = None
        self.requestMethod = "POST"
        self.jsondata = {}
        # Connect to database
        #self.dbconn = MySQLdb.connect(user="artsyuser",passwd="artsypasswd",host="localhost",db="artsydb")
        self.dbconn = MySQLdb.connect(user="root",passwd="Passw0rd@12",host="localhost",db="artsydb")
        self.cursor = self.dbconn.cursor()
        # DB connection done.
        self.logfp = open(logfile, "w+")
        self.artistsdict = {}


    def executebot(self, catslug):
        botscript = """
        curl -N 'https://metaphysics-production.artsy.net/v2' \\
  -H 'authority: metaphysics-production.artsy.net' \\
  -H 'pragma: no-cache' \\
  -H 'cache-control: no-cache' \\
  -H 'accept: */*' \\
  -H 'x-timezone: Asia/Calcutta' \\
  -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36' \\
  -H 'content-type: application/json' \\
  -H 'origin: https://www.artsy.net' \\
  -H 'sec-fetch-site: same-site' \\
  -H 'sec-fetch-mode: cors' \\
  -H 'sec-fetch-dest: empty' \\
  -H 'referer: https://www.artsy.net/' \\
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \\
  --data-binary '{"id":"PartnersRailQuery","query":"query PartnersRailQuery(\\n  $id: String!\\n  $category: [String]\\n  $type: [PartnerClassification!]!\\n) {\\n  partnerCategory(id: $id) {\\n    ...PartnersRail_partnerCategory_43V8rY\\n    id\\n  }\\n}\\n\\nfragment FollowProfileButton_profile on Profile {\\n  id\\n  slug\\n  name\\n  internalID\\n  is_followed: isFollowed\\n}\\n\\nfragment PartnerCell_partner on Partner {\\n  internalID\\n  slug\\n  name\\n  href\\n  initials\\n  locationsConnection(first: 15) {\\n    edges {\\n      node {\\n        city\\n        id\\n      }\\n    }\\n  }\\n  profile {\\n    ...FollowProfileButton_profile\\n    isFollowed\\n    image {\\n      cropped(width: 445, height: 334, version: [\\"wide\\", \\"large\\", \\"featured\\", \\"larger\\"]) {\\n        src\\n        srcSet\\n      }\\n    }\\n    id\\n  }\\n}\\n\\nfragment PartnersRail_partnerCategory_43V8rY on PartnerCategory {\\n  name\\n  primary: partners(defaultProfilePublic: true, eligibleForListing: true, eligibleForPrimaryBucket: true, partnerCategories: $category, sort: RANDOM_SCORE_DESC, type: $type) {\\n    internalID\\n    ...PartnerCell_partner\\n    id\\n  }\\n  secondary: partners(eligibleForListing: true, eligibleForSecondaryBucket: true, type: $type, partnerCategories: $category, sort: RANDOM_SCORE_DESC, defaultProfilePublic: true) {\\n    internalID\\n    ...PartnerCell_partner\\n    id\\n  }\\n}\\n","variables":{"id":"####CATSLUG####","category":"GALLERY","type":"GALLERY"}}' \\
  --compressed
        """
        tstr = str(int(time.time()))
        botpath = os.getcwd() + os.path.sep + "galleriesbot_%s.exe"%tstr
        botscript = botscript.replace("####CATSLUG####", catslug)
        fb = open(botpath, "w")
        fb.write(botscript)
        fb.close()
        os.chmod(botpath, 0o755)
        p = os.popen("%s"%botpath)
        output = p.read()
        p.close()
        sys.stdout.flush()
        os.remove(botpath)
        return output


    def executecatbot(self, botpath):
        tstr = str(int(time.time()))
        output = os.popen("%s"%botpath).read()
        sys.stdout.flush()
        return output


    def _decodeGzippedContent(cls, encoded_content):
        response_stream = io.BytesIO(encoded_content)
        decoded_content = ""
        try:
            gzipper = gzip.GzipFile(fileobj=response_stream)
            decoded_content = gzipper.read()
        except: # Maybe this isn't gzipped content after all....
            decoded_content = encoded_content
        decoded_content = decoded_content.decode('utf-8')
        return(decoded_content)

    _decodeGzippedContent = classmethod(_decodeGzippedContent)


    def _getCookieFromResponse(cls, lastHttpResponse):
        cookies = ""
        responseCookies = lastHttpResponse.getheader("Set-Cookie")
        pathPattern = re.compile(r"Path=/;", re.IGNORECASE)
        domainPattern = re.compile(r"Domain=[^;,]+(;|,)", re.IGNORECASE)
        expiresPattern = re.compile(r"Expires=[^;]+;", re.IGNORECASE)
        maxagePattern = re.compile(r"Max-Age=[^;]+;", re.IGNORECASE)
        samesitePattern = re.compile(r"SameSite=[^;]+;", re.IGNORECASE)
        securePattern = re.compile(r"secure;?", re.IGNORECASE)
        httponlyPattern = re.compile(r"HttpOnly;?", re.IGNORECASE)
        if responseCookies and responseCookies.__len__() > 1:
            cookieParts = responseCookies.split("Path=/")
            for i in range(cookieParts.__len__()):
                cookieParts[i] = re.sub(domainPattern, "", cookieParts[i])
                cookieParts[i] = re.sub(expiresPattern, "", cookieParts[i])
                cookieParts[i] = re.sub(maxagePattern, "", cookieParts[i])
                cookieParts[i] = re.sub(samesitePattern, "", cookieParts[i])
                cookieParts[i] = re.sub(securePattern, "", cookieParts[i])
                cookieParts[i] = re.sub(pathPattern, "", cookieParts[i])
                cookieParts[i] = re.sub(httponlyPattern, "", cookieParts[i])
                cookieParts[i] = cookieParts[i].replace(",", "")
                cookieParts[i] = re.sub(re.compile("\s+", re.DOTALL), "", cookieParts[i])
                cookies += cookieParts[i]
        cookies = cookies.replace(";;", ";")
        return(cookies)

    _getCookieFromResponse = classmethod(_getCookieFromResponse)


    def getPageContent(self):
        try:
            return(self.pageResponse.read())
        except:
            return(b"")


    def formatDate(cls, datestr):
        mondict = {'January' : '01', 'February' : '02', 'March' : '03', 'April' : '04', 'May' : '05', 'June' : '06', 'July' : '07', 'August' : '08', 'September' : '09', 'October' : '10', 'November' : '11', 'December' : '12' }
        mondict2 = {'Jan' : '01', 'Feb' : '02', 'Mar' : '03', 'Apr' : '04', 'May' : '05', 'Jun' : '06', 'Jul' : '07', 'Aug' : '08', 'Sep' : '09', 'Oct' : '10', 'Nov' : '11', 'Dec' : '12' }
        mondict3 = {'jan.' : '01', 'fév.' : '02', 'mar.' : '03', 'avr.' : '04', 'mai.' : '05', 'jui.' : '06', 'jul.' : '07', 'aoû.' : '08', 'sep.' : '09', 'oct.' : '10', 'nov.' : '11', 'déc.' : '12' }
        mondict4 = {'Janvier' : '01', 'Février' : '02', 'Mars' : '03', 'Avril' : '04', 'Mai' : '05', 'Juin' : '06', 'Juillet' : '07', 'Août' : '08', 'Septembre' : '09', 'Octobre' : '10', 'Novembre' : '11', 'Décembre' : '12'}
        datestrcomponents = datestr.split(" ")
        if not datestr:
            return ""
        dd = datestrcomponents[0]
        mm = '01'
        datestrcomponents[1] = datestrcomponents[1].capitalize()
        if datestrcomponents[1] in mondict.keys():
            mm = mondict[datestrcomponents[1]]
        else:
            try:
                mm = mondict2[datestrcomponents[1]]
            except:
                pass
        yyyy = datestrcomponents[2]
        yearPattern = re.compile("\d{4}")
        if not re.search(yearPattern, yyyy):
            yyyy = "2021"
        retdate = mm + "/" + dd + "/" + yyyy
        return retdate

    formatDate = classmethod(formatDate)


    def fractionToDecimalSize(self, sizestring):
        sizestringparts = sizestring.split("x")
        if sizestringparts.__len__() < 1:
            sizestringparts = sizestring.split("by")
        unitPattern = re.compile("(\s*(in)|(cm)\s*$)", re.IGNORECASE)
        ups = re.search(unitPattern, sizestringparts[-1])
        unit = ""
        if ups:
            upsg = ups.groups()
            unit = upsg[0]
        sizestringparts[-1] = unitPattern.sub("", sizestringparts[-1])
        decimalsizeparts = []
        beginspacePattern = re.compile("^\s+")
        endspacePattern = re.compile("\s+$")
        for szpart in sizestringparts:
            szpart = beginspacePattern.sub("", szpart)
            szpart = endspacePattern.sub("", szpart)
            d_szpart = unicodefraction_to_decimal(szpart)
            decimalsizeparts.append(d_szpart)
        decimalsize = " x ".join(decimalsizeparts)
        decimalsize += " " + unit
        return decimalsize


    def getDetailsPage(self, detailUrl):
        self.requestUrl = detailUrl
        self.pageRequest = urllib.request.Request(self.requestUrl, headers=self.httpHeaders)
        self.pageResponse = None
        self.postData = {}
        try:
            self.pageResponse = self.opener.open(self.pageRequest)
        except:
            print ("Error: %s"%sys.exc_info()[1].__str__())
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        return self.currentPageContent


    def getImagenameFromUrl(self, imageUrl):
        urlparts = imageUrl.split("/")
        imagefilepart = urlparts[-1]
        imagefilenameparts = imagefilepart.split("?")
        imagefilename = imagefilenameparts[0]
        return imagefilename


    def getImage(self, imageUrl, imagepath, downloadimages):
        imageUrlParts = imageUrl.split("/")
        imagefilename = imageUrlParts[-2] + "_" + imageUrlParts[-1]
        imagedir = imageUrlParts[-2]
        headers = {}
        for k in self.httpHeaders.keys():
            headers[k] = self.httpHeaders[k]
        imgUrl = imageUrl
        imgUrl = imgUrl.replace("%3A", ":").replace("%2F", "/")
        if downloadimages == "1":
            pageRequest = urllib.request.Request(imgUrl, headers=headers)
            #pageRequest.set_proxy(self.httpproxylist[3], 'http')
            pageResponse = None
            try:
                pageResponse = self.opener.open(pageRequest)
            except:
                print ("Error %s: %s"%(imgUrl, sys.exc_info()[1].__str__()))
            try:
                if pageResponse is not None:
                    imageContent = pageResponse.read()
                    ifp = open(imagepath + os.path.sep + imagefilename, "wb")
                    ifp.write(imageContent)
                    ifp.close()
            except:
                print("Error: %s"%sys.exc_info()[1].__str__())
        return imagefilename


    def getjsondata(self, output):
        try:
            self.jsondata = json.loads(output)
        except:
            self.jsondata = {}


    def getgallerydetails(self, galleryslug):
        curlq = """
        curl -N 'https://metaphysics-production.artsy.net/v2' \\
  -H 'authority: metaphysics-production.artsy.net' \\
  -H 'pragma: no-cache' \\
  -H 'cache-control: no-cache' \\
  -H 'accept: */*' \\
  -H 'x-timezone: Asia/Calcutta' \\
  -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36' \\
  -H 'content-type: application/json' \\
  -H 'origin: https://www.artsy.net' \\
  -H 'sec-fetch-site: same-site' \\
  -H 'sec-fetch-mode: cors' \\
  -H 'sec-fetch-dest: empty' \\
  -H 'referer: https://www.artsy.net/' \\
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \\
  --data-binary $'{"id":"partnerRoutes_OverviewQuery","query":"query partnerRoutes_OverviewQuery(\\\\n  $partnerId: String\\u0021\\\\n) {\\\\n  partner(id: $partnerId) @principalField {\\\\n    ...Overview_partner\\\\n    id\\\\n  }\\\\n}\\\\n\\\\nfragment AboutPartner_partner on Partner {\\\\n  profile {\\\\n    fullBio\\\\n    bio\\\\n    id\\\\n  }\\\\n  website\\\\n  vatNumber\\\\n  displayFullPartnerPage\\\\n}\\\\n\\\\nfragment ArticleCard_article on Article {\\\\n  channelID\\\\n  thumbnailTitle\\\\n  href\\\\n  author {\\\\n    name\\\\n    id\\\\n  }\\\\n  contributingAuthors {\\\\n    name\\\\n    id\\\\n  }\\\\n  thumbnailImage {\\\\n    medium: cropped(width: 400, height: 300) {\\\\n      width\\\\n      height\\\\n      src\\\\n      srcSet\\\\n    }\\\\n  }\\\\n}\\\\n\\\\nfragment ArticlesRail_partner on Partner {\\\\n  slug\\\\n  articlesConnection(first: 8) {\\\\n    totalCount\\\\n    edges {\\\\n      node {\\\\n        internalID\\\\n        ...ArticleCard_article\\\\n        id\\\\n      }\\\\n    }\\\\n  }\\\\n}\\\\n\\\\nfragment ArtistsRail_partner on Partner {\\\\n  slug\\\\n  profileArtistsLayout\\\\n  displayFullPartnerPage\\\\n  artistsWithPublishedArtworks: artistsConnection(hasPublishedArtworks: true, displayOnPartnerProfile: true) {\\\\n    totalCount\\\\n  }\\\\n  representedArtistsWithoutPublishedArtworks: artistsConnection(representedBy: true, hasPublishedArtworks: false, displayOnPartnerProfile: true) {\\\\n    totalCount\\\\n  }\\\\n}\\\\n\\\\nfragment Overview_partner on Partner {\\\\n  slug\\\\n  partnerType\\\\n  displayFullPartnerPage\\\\n  profileBannerDisplay\\\\n  displayArtistsSection\\\\n  ...AboutPartner_partner\\\\n  ...ShowsRail_partner\\\\n  ...ArtistsRail_partner\\\\n  ...SubscriberBanner_partner\\\\n  ...ArticlesRail_partner\\\\n  locationsConnection(first: 1) {\\\\n    edges {\\\\n      node {\\\\n        city\\\\n        coordinates {\\\\n          lat\\\\n          lng\\\\n        }\\\\n        id\\\\n      }\\\\n    }\\\\n  }\\\\n}\\\\n\\\\nfragment ShowCard_show on Show {\\\\n  href\\\\n  name\\\\n  isFairBooth\\\\n  exhibitionPeriod\\\\n  coverImage {\\\\n    medium: cropped(width: 320, height: 240) {\\\\n      width\\\\n      height\\\\n      src\\\\n      srcSet\\\\n    }\\\\n  }\\\\n}\\\\n\\\\nfragment ShowsRail_partner on Partner {\\\\n  slug\\\\n  displayFullPartnerPage\\\\n  showsConnection(status: ALL, first: 20, isDisplayable: true) {\\\\n    totalCount\\\\n    edges {\\\\n      node {\\\\n        id\\\\n        ...ShowCard_show\\\\n      }\\\\n    }\\\\n  }\\\\n}\\\\n\\\\nfragment SubscriberBanner_partner on Partner {\\\\n  hasFairPartnership\\\\n  name\\\\n}\\\\n","variables":{"partnerId":"####GALSLUG####"}}' \\
  --compressed
        """
        curlq = curlq.replace("####GALSLUG####", galleryslug)
        tstr = str(int(time.time()))
        botpath = os.getcwd() + os.path.sep + "gallerydetailsbot_%s.exe"%tstr
        fb = open(botpath, "w")
        fb.write(curlq)
        fb.close()
        os.chmod(botpath, 0o755)
        p = os.popen("bash %s"%botpath)
        output = p.read()
        p.close()
        sys.stdout.flush()
        os.remove(botpath)
        gallerydata = {}
        #print(output)
        eventdata = []
        try:
            jsondata = json.loads(output)
            gallerydata['description'] = jsondata['data']['partner']['profile']['fullBio']
            gallerydata['description'] = gallerydata['description'].replace('"', "&quot;").replace("'", "&quot;")
            #print(gallerydata['description'])
            gallerydata['website'] = jsondata['data']['partner']['website']
            srcset = jsondata['data']['partner']['showsConnection']['edges'][0]['node']['coverImage']['medium']['srcSet']
            srcsetimages = srcset.split(",")
            largePattern = re.compile("large", re.IGNORECASE)
            magnificationPattern = re.compile("\s+\d+x")
            for imgsrc in srcsetimages:
                if re.search(largePattern, imgsrc):
                    imgsrc = magnificationPattern.sub("", imgsrc)
                    gallerydata['coverimage'] = imgsrc
                    # TO DO: Download image and store it in some location
            events = jsondata['data']['partner']['showsConnection']['edges']
            for evt in events:
                eventdict = {}
                eventdict['eventname'] = evt['node']['name']
                eventdict['eventperiod'] = evt['node']['exhibitionPeriod']
                if evt['node']['isFairBooth'] == True:
                    eventdict['eventtype'] = "Exhibition"
                else:
                    eventdict['eventtype'] = "Booth"
                eventdict['eventurl'] = "https://www.artsy.net" + evt['node']['href']
                eventdict['eventinfo'] = ""
                eventdata.append(eventdict)
            gallerydata['events'] = eventdata
        except:
            print("Error: %s"%sys.exc_info()[1].__str__())
            gallerydata = {'description' : '', 'website' : '', 'coverimage' : '', 'events' : []}
        return gallerydata


    def loadartistsdict(self):
        artistsql = "select artistname, nationality, birthdate, deathdate from artists"
        try:
            self.cursor.execute(evtinssql)
        except:
            return {}
        self.artistsdict = {}
        artistrecords = self.cursor.fetchall()
        for arec in artistrecords:
            artistname = arec['artistname'].lower()
            nationality = str(arec['nationality'])
            birthdate = str(arec['birthdate'])
            deathdate = str(arec['deathdate'])
            self.artistsdict[artistname] = [nationality, birthdate, deathdate]


    def getpricinginfo(self, awslug):
        botcontentpath = "/root/artwork/artsy/artworkpricebot.exe"
        fe = open(botcontentpath)
        botcodetemplate = fe.read()
        fe.close()
        botcode = botcodetemplate.replace("####AWSLUG####", awslug)
        tstr = str(int(time.time()))
        botpath = os.getcwd() + os.path.sep + "artworkpricebot_%s.exe"%tstr
        fb = open(botpath, "w")
        fb.write(botcode)
        fb.close()
        os.chmod(botpath, 0o755)
        p = os.popen("bash %s"%botpath)
        output = p.read()
        p.close()
        sys.stdout.flush()
        os.remove(botpath)
        try:
            jsondata = json.loads(output)
        except:
            print("JSON Artwork Price details Error: %s"%sys.exc_info()[1].__str__())
            return ""
        pricingdata = {'estimate' : '', 'soldprice' : ''}
        try:
            pricingdata = {'estimate' : jsondata['data']['artwork']['listPrice']['minor'], 'soldprice' : ''}
        except:
            print("JSON Artwork Price keys Error: %s"%sys.exc_info()[1].__str__())
        return pricingdata


    def getartworkdetails(self, awslug, title, artists):
        artworkdata = {'artistbirthyear' : '', 'artistdeathyear' : '', 'artistnationality' : '', 'size' : '', 'estimate' : '', 'soldprice' : '', 'medium' : '', 'signature' : '', 'letterofauthenticity' : '', 'description' : '', 'provenance' : '', 'literature' : '', 'exhibitions' : '', 'image1' : '', 'image2' : '', 'image3' : '', 'image4' : ''}
        # run eventartworkdetailsbot.exe code, map artist info from artists table and fill up the dict above
        botcontentpath = "/root/artwork/artsy/eventartworkdetailsbot.exe"
        fe = open(botcontentpath)
        botcodetemplate = fe.read()
        fe.close()
        botcode = botcodetemplate.replace("####AWSLUG####", awslug)
        tstr = str(int(time.time()))
        botpath = os.getcwd() + os.path.sep + "eventartworkdetailsbot_%s.exe"%tstr
        fb = open(botpath, "w")
        fb.write(botcode)
        fb.close()
        os.chmod(botpath, 0o755)
        p = os.popen("bash %s"%botpath)
        output = p.read()
        p.close()
        sys.stdout.flush()
        os.remove(botpath)
        try:
            jsondata = json.loads(output)
        except:
            print("JSON Artwork details Error: %s"%sys.exc_info()[1].__str__())
            return artworkdata
        artdata = jsondata['data']['artwork']
        try:
            artworkdata['description'] = str(artdata['description'])
            artworkdata['size'] = str(jsondata['data']['framed'])
        except:
            pass
        try:
            artworkdata['signature'] = str(jsondata['data']['signatureInfo'])
        except:
            pass
        try:
            artworkdata['letterofauthenticity'] = str(jsondata['data']['certificateOfAuthenticity'])
        except:
            pass
        try:
            artworkdata['medium'] = str(jsondata['data']['mediumType']['longDescription'])
        except:
            pass
        try:
            artworkdata['provenance'] = str(jsondata['data']['provenance'])
        except:
            pass
        try:
            artworkdata['literature'] = str(jsondata['data']['literature'])
        except:
            pass
        try:
            artworkdata['exhibitions'] = str(jsondata['data']['exhibition_history'])
        except:
            pass
        pricinginfo = self.getpricinginfo(awslug)
        artworkdata['estimate'] = pricinginfo['estimate']
        artworkdata['soldprice'] = pricinginfo['soldprice']
        aname = artists
        if "," in artists:
            artistslist = artists.split(",")
            aname = artistslist[0].strip()
        try:
            artworkdata['artistbirthyear'] = self.artistsdict[aname.lower()][1]
            artworkdata['artistdeathyear'] = self.artistsdict[aname.lower()][2]
            artworkdata['artistnationality'] = self.artistsdict[aname.lower()][0]
        except:
            pass
        return artworkdata


    def geteventartworks(self, eslug):
        baseurl = "https://www.artsy.net"
        workslist = []
        botcontentpath = "/root/artwork/artsy/eventartworksbot.exe"
        fe = open(botcontentpath)
        botcodetemplate = fe.read()
        fe.close()
        botcode = botcodetemplate.replace("####EVENTSLUG####", eslug)
        tstr = str(int(time.time()))
        botpath = os.getcwd() + os.path.sep + "eventartworksbot_%s.exe"%tstr
        fb = open(botpath, "w")
        fb.write(botcode)
        fb.close()
        os.chmod(botpath, 0o755)
        p = os.popen("bash %s"%botpath)
        output = p.read()
        p.close()
        sys.stdout.flush()
        os.remove(botpath)
        try:
            jsondata = json.loads(output)
            edges = jsondata['data']['show']['filtered_artworks']['edges']
        except:
            print("JSON Error: %s"%sys.exc_info()[1].__str__())
            edges = []
        for edge in edges:
            node, slug, artworkurl, imageurl, title, artists, creationdate = "", "", "", "", "", "", ""
            try:
                node = edge['node']
                slug = node['slug']
                artworkurl = baseurl + node['href']
                imageurl = node['image']['url']
                title = node['title']
                artists = node['artistNames'].replace("'", "")
                creationdate = node['date']
            except:
                print("Artwork SQL Insertion Error: %s"%(sys.exc_info()[1].__str__()))
            artworkdatadict = self.getartworkdetails(slug, title, artists)
            # Remember to leave a pattern for gallery_id and event_id in the insert sql.
            insertartworksql = "insert into artworks (artworkname, creationdate, gallery_id, artistname, artistbirthyear, artistdeathyear, artistnationality, size, estimate, soldprice, medium, event_id, signature, letterofauthenticity, description, provenance, literature, image1, image2, image3, image4, workurl, inserted, edited, exhibitions) values ('%s', '%s', '####GALLERYID####', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '####EVENTID####', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', now(), now(), '%s')"%(title, creationdate, artists, artworkdatadict['artistbirthyear'], artworkdatadict['artistdeathyear'], artworkdatadict['artistnationality'], artworkdatadict['size'], artworkdatadict['estimate'], artworkdatadict['soldprice'], artworkdatadict['medium'], artworkdatadict['signature'], artworkdatadict['letterofauthenticity'], artworkdatadict['description'], artworkdatadict['provenance'], artworkdatadict['literature'], artworkdatadict['image1'], artworkdatadict['image2'], artworkdatadict['image3'], artworkdatadict['image4'], artworkurl, artworkdatadict['exhibitions'])
            workslist.append(insertartworksql)
        return workslist


    def populategalleriesdata(self):
        jsondict = self.jsondata
        baseurl = "https://www.artsy.net"
        #print(jsondict)
        sqllist = []
        galleriesdict = {}
        self.loadartistsdict()
        try:
            categoryname = jsondict['data']['partnerCategory']['name']
            gallerieslist = jsondict['data']['partnerCategory']['primary']
            for gallery in gallerieslist:
                galleryname = gallery['name']
                galleryslug = gallery['slug']
                galleryname = galleryname.replace("'", "\\'")
                galleryurl = baseurl + gallery['href']
                locationconnections = gallery['locationsConnection']['edges']
                locationslist = []
                for loccon in locationconnections:
                    loccity = loccon['node']['city']
                    loccity = loccity.replace("'", "\\'")
                    locationslist.append(loccity)
                locations = ", ".join(locationslist)
                inssql = "insert into galleries (galleryname, slug, location, description, galleryurl, website, coverimage, inserted, edited) values ('%s', '%s', '%s', '##DESC##', '%s', '##WEBS##', '##COVR##', now(), now())"%(galleryname, galleryslug, locations, galleryurl)
                sqllist.append(inssql)
                galleriesdict[inssql] = galleryslug
        except:
            print("Couldn't find galleries from response %s\n%s"%(jsondict, sys.exc_info()[1].__str__()))
        # The following part should be subprocessed once all the data capture logic is in place.
        for sqlquery in sqllist:
            gdata = self.getgallerydetails(galleriesdict[sqlquery])
            try:
                sqlquery = sqlquery.replace("##DESC##", gdata['description']) 
                sqlquery = sqlquery.replace("##WEBS##", gdata['website']) 
                sqlquery = sqlquery.replace("##COVR##", gdata['coverimage']) 
                self.cursor.execute(sqlquery)
                self.cursor.execute("select max(id) from galleries")
                records = self.cursor.fetchall()
                lastid = -1
                if records.__len__() == 0:
                    print("Error occurred in fetching last inserted gallery Id - %s"%gdata['website'])
                else:
                    lastid = records[0][0]
            except:
                print("Error: %s"%sys.exc_info()[1].__str__())
            events = gdata['events']
            for eventdict in events:
                if eventdict['eventname'] is None:
                    eventdict['eventname'] = ""
                eventname = eventdict['eventname'].replace("'", "").replace('"', '')
                if eventdict['eventperiod'] is None:
                    eventdict['eventperiod'] = ""
                eventperiod = eventdict['eventperiod'].replace("'", "").replace('"', '')
                eventurl = eventdict['eventurl']
                eventslug = eventurl.replace("https://www.artsy.net/show/", "")
                artworkslist = self.geteventartworks(eventslug)
                eventtype = eventdict['eventtype']
                if eventtype is None:
                    eventtype = "Unknown"
                if eventurl is None:
                    eventurl = ""
                eventinfo = ""
                try:
                    resp = requests.get(eventurl)
                    esoup = BeautifulSoup(resp.text, features="html.parser")
                    metatags = esoup.find_all("meta", {'name' : 'description'})
                    if metatags.__len__() > 0:
                        try:
                            eventinfo = metatags[0]['content']
                        except:
                            eventinfo = ""
                        eventinfo = eventinfo.replace("'", "&quot;").replace('"', '&quot;')
                        eventinfo = eventinfo.replace("\n", "").replace("\r", "")
                except:
                    print("Error: %s"%sys.exc_info()[1].__str__())
                evtinssql = "insert into events (eventtype, eventstatus, gallery_id, eventinfo, artworkscount, eventurl, eventname, eventperiod, inserted, edited) values ('%s', '', %s, '%s', 0, '%s', '%s', '%s', now(), now())"%(eventtype, lastid, eventinfo, eventurl, eventname, eventperiod)
                try:
                    self.cursor.execute(evtinssql)
                except:
                    pass
                self.cursor.execute("select max(id) from events")
                evrecords = self.cursor.fetchall()
                lastevid = -1
                if evrecords.__len__() == 0:
                    print("Error occurred in fetching last inserted event Id - %s"%gdata['website'])
                else:
                    lastevid = evrecords[0][0]
                # Get last event_id and execute statements in artworkslist here
                for insworksql in artworkslist:
                    insworksql = insworksql.replace("####GALLERYID####", str(lastid)).replace("####EVENTID####", str(lastevid))
                    try:
                        self.cursor.execute(insworksql)
                    except:
                        print("Error in '%s' - %s"%(insworksql, sys.exc_info()[1].__str__()))
                self.dbconn.commit()


    def getcategories(self):
        catbotpath = "/root/artwork/artsy/gallery_cats.exe"
        catoutput = self.executecatbot(catbotpath)
        self.getjsondata(catoutput)
        categories = []
        try:
            jsoncats = self.jsondata['data']['viewer']['partnerCategories']
        except:
            jsoncats = []
        for cat in jsoncats:
            categories.append(cat['slug'])
        return categories


    def getartistsbyalphabet(self, character, pageno):
        baseurl = "https://www.artsy.net"
        curlq = """
        curl 'https://metaphysics-production.artsy.net/v2' \\
  -H 'authority: metaphysics-production.artsy.net' \\
  -H 'pragma: no-cache' \\
  -H 'cache-control: no-cache' \\
  -H 'accept: */*' \\
  -H 'x-timezone: Asia/Calcutta' \\
  -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36' \\
  -H 'content-type: application/json' \\
  -H 'origin: https://www.artsy.net' \\
  -H 'sec-fetch-site: same-site' \\
  -H 'sec-fetch-mode: cors' \\
  -H 'sec-fetch-dest: empty' \\
  -H 'referer: https://www.artsy.net/' \\
  -H 'accept-language: en-GB,en-US;q=0.9,en;q=0.8' \\
  --data-binary $'{"id":"artistsRoutes_ArtistsByLetterQuery","query":"query artistsRoutes_ArtistsByLetterQuery(\\\\n  $letter: String\\u0021\\\\n  $page: Int\\\\n  $size: Int\\\\n) {\\\\n  viewer {\\\\n    ...ArtistsByLetter_viewer_qU0ud\\\\n  }\\\\n}\\\\n\\\\nfragment ArtistsByLetter_viewer_qU0ud on Viewer {\\\\n  artistsConnection(letter: $letter, page: $page, size: $size) {\\\\n    pageInfo {\\\\n      endCursor\\\\n      hasNextPage\\\\n    }\\\\n    pageCursors {\\\\n      ...Pagination_pageCursors\\\\n    }\\\\n    artists: edges {\\\\n      artist: node {\\\\n        internalID\\\\n        name\\\\n        href\\\\n        id\\\\n      }\\\\n    }\\\\n  }\\\\n}\\\\n\\\\nfragment Pagination_pageCursors on PageCursors {\\\\n  around {\\\\n    cursor\\\\n    page\\\\n    isCurrent\\\\n  }\\\\n  first {\\\\n    cursor\\\\n    page\\\\n    isCurrent\\\\n  }\\\\n  last {\\\\n    cursor\\\\n    page\\\\n    isCurrent\\\\n  }\\\\n  previous {\\\\n    cursor\\\\n    page\\\\n  }\\\\n}\\\\n","variables":{"letter":"####ALPHABET####","page":####PAGENO####,"size":100}}' \\
  --compressed
        """
        curlq = curlq.replace("####ALPHABET####", character)
        curlq = curlq.replace("####PAGENO####", pageno)
        tstr = str(int(time.time()))
        botpath = os.getcwd() + os.path.sep + "artistlistbot_%s.exe"%tstr
        fb = open(botpath, "w")
        fb.write(curlq)
        fb.close()
        os.chmod(botpath, 0o755)
        p = os.popen("bash %s"%botpath)
        output = p.read()
        p.close()
        sys.stdout.flush()
        os.remove(botpath)
        artistlist = []
        try:
            jsondata = json.loads(output)
            artists = jsondata['data']['viewer']['artistsConnection']['artists']
            for artist in artists:
                name = artist['artist']['name']
                href = artist['artist']['href']
                slug = href
                slug = slug.replace("/artist/", "")
                href = baseurl + href
                artistlist.append({name : [href, slug]})
        except:
            print("Error: %s"%sys.exc_info()[1].__str__())
        return artistlist


    def getartists(self):
        baseurl = "https://www.artsy.net"
        alphabets = ['d', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        pagenumbers = [x for x in range(1, 50)]
        artistdetailsbotpath = "/root/artwork/artsy/artistdetails.exe"
        fp = open(artistdetailsbotpath)
        artistdetailsbotcontent = fp.read()
        fp.close()
        for ch in alphabets:
            for pageno in pagenumbers:
                artists = artsybot.getartistsbyalphabet(ch, str(pageno))
                for adict in artists:
                    name = list(adict.keys())[0]
                    print("Working on " + name + " ## " + adict[name][1])
                    artistdetailsbotcode = artistdetailsbotcontent.replace("####ARTSLUG####", adict[name][1])
                    tstr = str(int(time.time()))
                    artbotpath = os.getcwd() + os.path.sep + "artistdetailsbot_%s.exe"%tstr
                    fb = open(artbotpath, "w")
                    fb.write(artistdetailsbotcode)
                    fb.close()
                    os.chmod(artbotpath, 0o755)
                    p = os.popen("bash %s"%artbotpath)
                    output = p.read()
                    p.close()
                    sys.stdout.flush()
                    os.remove(artbotpath)
                    try:
                        jsondata = json.loads(output)
                    except:
                        print("Error: %s - continuing to next artist on page."%sys.exc_info()[1].__str__())
                        continue
                    try:
                        slug = str(jsondata['data']['artist']['slug'])
                    except:
                        slug = ""
                    try:
                        nationality = str(jsondata['data']['artist']['nationality'])
                    except:
                        nationality = ""
                    try:
                        birthday = str(jsondata['data']['artist']['birthday'])
                        deathday = str(jsondata['data']['artist']['deathday'])
                    except:
                        birthday = ""
                        deathday = ""
                    try:
                        gender = str(jsondata['data']['artist']['gender'])
                    except:
                        gender = ""
                    try:
                        href = baseurl + str(jsondata['data']['artist']['href'])
                    except:
                        href = ""
                    try:
                        largeimage = str(jsondata['data']['artist']['image']['large'])
                        squareimage = str(jsondata['data']['artist']['image']['square'])
                    except:
                        largeimage = ""
                        squareimage = ""
                    try:
                        about = str(jsondata['data']['artist']['biographyBlurb']['text'])
                    except:
                        about = ""
                    try:
                        edges = json.dumps(jsondata['data']['artist']['artworks_connection']['edges'])
                    except:
                        edges = "[]"
                    #print(nationality + " ## " + birthday + " ## " + gender)
                    insartistsql = "insert into artists (artistname, nationality, birthdate, deathdate, about, profileurl, gender, slug, squareimage, largeimage, edges, inserted, edited) values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', now(), now())"%(name, nationality, birthday, deathday, about, href, gender, slug, squareimage, largeimage, edges)
                    #print(insartistsql)
                    try:
                        self.cursor.execute(insartistsql)    
                    except:
                        print("Error: %s"%sys.exc_info()[1].__str__())
                self.dbconn.commit()


    def logmessage(self, msg):
        pass


    def closebot(self):
        self.dbconn.close()
        self.cursor.close()
        self.logfp.close()



if __name__ == "__main__":
    if sys.argv.__len__() < 2:
        print("Insufficient arguments. Please specify the target section as the first argument.")
        sys.exit()
    inputtarget = sys.argv[1].title()
    targetsdict = {'Galleries' : 'https://metaphysics-production.artsy.net/v2', 'Artists' : 'https://www.artsy.net/artists', 'Museums' : 'https://www.artsy.net/institutions'}
    if inputtarget == "Galleries":
        artsybot = ArtsyBot(targetsdict['Galleries'], 'Galleries')
        categories = artsybot.getcategories()
        #print(categories)
        for cat in categories:
            output = artsybot.executebot(cat)
            artsybot.getjsondata(output)
            artsybot.populategalleriesdata()
    elif inputtarget == "Artists":
        artsybot = ArtsyBot(targetsdict['Artists'], 'Artists')
        artsybot.getartists()
    else:
        print("Invalid argument value: %s"%inputtarget)
    artsybot.closebot()







