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


class ImageBot(object):
    
    htmltagPattern = re.compile("\<\/?[^\<\>]*\/?\>", re.DOTALL)
    pathEndingWithSlashPattern = re.compile(r"\/$")

    htmlEntitiesDict = {'&nbsp;' : ' ', '&#160;' : ' ', '&amp;' : '&', '&#38;' : '&', '&lt;' : '<', '&#60;' : '<', '&gt;' : '>', '&#62;' : '>', '&apos;' : '\'', '&#39;' : '\'', '&quot;' : '"', '&#34;' : '"'}

    def __init__(self, section, targetdir="", logfile="/tmp/getimage.log"):
        # Create the opener object(s). Might need more than one type if we need to get pages with unwanted redirects.
        self.opener = urllib.request.build_opener(urllib.request.HTTPHandler(), urllib.request.HTTPSHandler()) # This is my normal opener....
        self.no_redirect_opener = urllib.request.build_opener(urllib.request.HTTPHandler(), urllib.request.HTTPSHandler(), NoRedirectHandler()) # ... and this one won't handle redirects.
        #self.debug_opener = urllib.request.build_opener(urllib.request.HTTPHandler(debuglevel=1))
        # Initialize some object properties.
        self.sessionCookies = ""
        self.httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',  'Accept' : '*/*', 'Accept-Language' : 'en-US,en;q=0.5', 'Accept-Encoding' : 'gzip,deflate', 'Connection' : 'keep-alive', 'Cache-Control' : 'no-cache', 'Pragma' : 'no-cache'}
        self.httpHeaders['sec-fetch-dest'] = "empty"
        self.httpHeaders['sec-fetch-mode'] = "cors"
        self.httpHeaders['sec-fetch-site'] = "same-site"
        self.httpHeaders['TE'] = 'trailers'
        self.httpHeaders['X-TIMEZONE'] = 'Asia/Kolkata'
        self.homeDir = os.getcwd()
        self.requestUrl = "https://www.artsy.net/"
        self.basedir = targetdir
        if targetdir == "":
            self.basedir = self.homeDir
        #print(self.requestUrl)
        self.section = section
        data = {}
        postdata = urllib.parse.urlencode(data).encode("utf-8")
        self.pageRequest = urllib.request.Request(self.requestUrl, postdata, headers=self.httpHeaders)
        self.pageResponse = None
        self.requestMethod = "POST"
        self.jsondata = {}
        # Connect to database
        self.dbconn = MySQLdb.connect(user="artsyuser",passwd="artbankpasswd",host="localhost",db="artsydb")
        #self.dbconn = MySQLdb.connect(user="artsyuser",passwd="artbank#12Passwd",host="localhost",db="artsydb")
        self.cursor = self.dbconn.cursor()
        # DB connection done.
        self.logfp = open(logfile, "w+")
        

    def renameimagefile(self, basepath, imagefilename, mappedImagename):
        oldfilename = basepath + "/" + imagefilename
        newfilename = basepath + "/" + mappedImagename
        os.rename(oldfilename, newfilename)


    def getgalleryimages(self):
        galimgsql = "select galleryname, coverimage, id from galleries"
        #galimgsql = "select galleryname, coverimage, id from galleries where id=3638"
        try:
            self.cursor.execute(galimgsql)
        except:
            print("Error getting gallery coverimages: %s"%sys.exc_info()[1].__str__())
            return None
        galleryrecs = self.cursor.fetchall()
        targetbasedir = self.basedir + os.path.sep + "galleries"
        if not os.path.isdir(targetbasedir):
            os.makedirs(targetbasedir)
        extPattern = re.compile("\.(\w{3,4})$")
        for rec in galleryrecs:
            galleryname = rec[0]
            imgsrc = rec[1]
            galid = rec[2]
            if imgsrc == "":
                continue
            srcPattern = re.compile("src=(.*)$")
            spc = re.search(srcPattern, imgsrc)
            coverimageurl = imgsrc
            if spc:
                coverimageurl = spc.groups()[0]
            coverimageurl = coverimageurl.replace("%3A", ":").replace("%2F", "/")
            xps = re.search(extPattern, coverimageurl)
            ext = "jpg" # By default we save as jpeg
            if xps:
                ext = xps.groups()[0]
            imgnameondisk = "gal_%s.%s"%(galid, ext)
            targetcoverimage = "/media/galleries/" + imgnameondisk
            targetimage = targetbasedir + os.path.sep + imgnameondisk
            updatesql = "update galleries set coverimage='%s' where id='%s'"%(targetcoverimage, galid)
            self.pageRequest = urllib.request.Request(coverimageurl, None, headers=self.httpHeaders)
            try:
                self.pageResponse = self.opener.open(self.pageRequest)
            except:
                print("Error getting '%s': %s"%(coverimageurl, sys.exc_info()[1].__str__()))
                continue
            imagecontent = self.pageResponse.read()
            fp = open(targetimage, "wb")
            fp.write(imagecontent)
            fp.close()
            try:
                self.cursor.execute(updatesql)
            except:
                self.logfp.write("Error writing image name to DB: gallery Id - %s - %s"%(galid, targetcoverimage))
            self.dbconn.commit()
        print("Completed processing images for galleries")


    def geteventimages(self):
        evimgsql = "select eventname, gallery_id, eventimage, id from events"
        #evimgsql = "select eventname, gallery_id, eventimage, id from events where id=3638"
        try:
            self.cursor.execute(evimgsql)
        except:
            print("Error getting event images: %s"%sys.exc_info()[1].__str__())
            return None
        eventrecs = self.cursor.fetchall()
        targetbasedir = self.basedir + os.path.sep + "galleries" + os.path.sep + "events"
        if not os.path.isdir(targetbasedir):
            os.makedirs(targetbasedir)
        extPattern = re.compile("\.(\w{3,4})$")
        for rec in eventrecs:
            eventname = rec[0]
            galid = rec[1]
            imgsrc = rec[2]
            evid = rec[3]
            if imgsrc == "":
                continue
            srcPattern = re.compile("src=(.*)$")
            spc = re.search(srcPattern, imgsrc)
            eventimageurl = imgsrc
            if spc:
                eventimageurl = spc.groups()[0]
            eventimageurl = eventimageurl.replace("%3A", ":").replace("%2F", "/")
            xps = re.search(extPattern, eventimageurl)
            ext = "jpg" # By default we save as jpeg
            if xps:
                ext = xps.groups()[0]
            imgnameondisk = "ev_%s_%s.%s"%(evid, galid, ext)
            targeteventimage = "/media/galleries/events/" + imgnameondisk
            targetimage = targetbasedir + os.path.sep + imgnameondisk
            updatesql = "update events set eventimage='%s' where id='%s'"%(targeteventimage, evid)
            self.pageRequest = urllib.request.Request(eventimageurl, None, headers=self.httpHeaders)
            try:
                self.pageResponse = self.opener.open(self.pageRequest)
            except:
                print("Error getting '%s': %s"%(eventimageurl, sys.exc_info()[1].__str__()))
                continue
            imagecontent = self.pageResponse.read()
            fp = open(targetimage, "wb")
            fp.write(imagecontent)
            fp.close()
            try:
                self.cursor.execute(updatesql)
            except:
                self.logfp.write("Error writing image name to DB: event Id - %s - %s"%(evid, targeteventimage))
            self.dbconn.commit()
        print("Completed processing images for events")



    def getartworkimages(self):
        artimgsql = "select artworkname, gallery_id, event_id, image1, image2, image3, image4, id from artworks"
        #artimgsql = "select artworkname, gallery_id, event_id, image1, image2, image3, image4, id from artworks where id=3638"
        try:
            self.cursor.execute(artimgsql)
        except:
            print("Error getting artworks images: %s"%sys.exc_info()[1].__str__())
            return None
        artworkrecs = self.cursor.fetchall()
        targetbasedir = self.basedir + os.path.sep + "galleries" + os.path.sep + "events" + os.path.sep + "artworks"
        if not os.path.isdir(targetbasedir):
            os.makedirs(targetbasedir)
        extPattern = re.compile("\.(\w{3,4})$")
        for rec in artworkrecs:
            artworkname = rec[0]
            galid = rec[1]
            evid = rec[2]
            image1 = rec[3]
            image2 = rec[4]
            image3 = rec[5]
            image4 = rec[6]
            awid = rec[7]
            if image1 == "":
                continue
            srcPattern = re.compile("src=(.*)$")
            spc = re.search(srcPattern, image1)
            artworkimageurl1 = image1
            if spc:
                artworkimageurl1 = spc.groups()[0]
            artworkimageurl1 = artworkimageurl1.replace("%3A", ":").replace("%2F", "/")
            xps = re.search(extPattern, artworkimageurl1)
            ext = "jpg" # By default we save as jpeg
            if xps:
                ext = xps.groups()[0]
            img1nameondisk = "awimg1_%s_%s_%s.%s"%(awid, evid, galid, ext)
            targetartworkimage1 = "/media/galleries/events/artworks/" + img1nameondisk
            targetimage1 = targetbasedir + os.path.sep + img1nameondisk
            updatesql = "update artworks set image1='%s' where id='%s'"%(targetartworkimage1, awid)
            self.pageRequest = urllib.request.Request(artworkimageurl1, None, headers=self.httpHeaders)
            try:
                self.pageResponse = self.opener.open(self.pageRequest)
            except:
                print("Error getting '%s': %s"%(artworkimageurl1, sys.exc_info()[1].__str__()))
                continue
            imagecontent = self.pageResponse.read()
            fp = open(targetimage1, "wb")
            fp.write(imagecontent)
            fp.close()
            try:
                self.cursor.execute(updatesql)
            except:
                self.logfp.write("Error writing image1 name to DB: artwork Id - %s - %s"%(awid, targetartworkimage1))
            # Do the same for image2
            if image2 == "":
                continue
            spc = re.search(srcPattern, image2)
            artworkimageurl2 = image2
            if spc:
                artworkimageurl2 = spc.groups()[0]
            artworkimageurl2 = artworkimageurl2.replace("%3A", ":").replace("%2F", "/")
            xps = re.search(extPattern, artworkimageurl2)
            ext = "jpg" # By default we save as jpeg
            if xps:
                ext = xps.groups()[0]
            img2nameondisk = "awimg2_%s_%s_%s.%s"%(awid, evid, galid, ext)
            targetartworkimage2 = "/media/galleries/events/artworks/" + img2nameondisk
            targetimage2 = targetbasedir + os.path.sep + img2nameondisk
            updatesql = "update artworks set image2='%s' where id='%s'"%(targetartworkimage2, awid)
            self.pageRequest = urllib.request.Request(artworkimageurl2, None, headers=self.httpHeaders)
            try:
                self.pageResponse = self.opener.open(self.pageRequest)
            except:
                print("Error getting '%s': %s"%(artworkimageurl2, sys.exc_info()[1].__str__()))
                continue
            imagecontent = self.pageResponse.read()
            fp = open(targetimage2, "wb")
            fp.write(imagecontent)
            fp.close()
            try:
                self.cursor.execute(updatesql)
            except:
                self.logfp.write("Error writing image2 name to DB: artwork Id - %s - %s"%(awid, targetartworkimage2))
            # Do the same for image3
            if image3 == "":
                continue
            spc = re.search(srcPattern, image3)
            artworkimageurl3 = image3
            if spc:
                artworkimageurl3 = spc.groups()[0]
            artworkimageurl3 = artworkimageurl3.replace("%3A", ":").replace("%2F", "/")
            xps = re.search(extPattern, artworkimageurl3)
            ext = "jpg" # By default we save as jpeg
            if xps:
                ext = xps.groups()[0]
            img3nameondisk = "awimg3_%s_%s_%s.%s"%(awid, evid, galid, ext)
            targetartworkimage3 = "/media/galleries/events/artworks/" + img3nameondisk
            targetimage3 = targetbasedir + os.path.sep + img3nameondisk
            updatesql = "update artworks set image3='%s' where id='%s'"%(targetartworkimage3, awid)
            self.pageRequest = urllib.request.Request(artworkimageurl3, None, headers=self.httpHeaders)
            try:
                self.pageResponse = self.opener.open(self.pageRequest)
            except:
                print("Error getting '%s': %s"%(artworkimageurl3, sys.exc_info()[1].__str__()))
                continue
            imagecontent = self.pageResponse.read()
            fp = open(targetimage3, "wb")
            fp.write(imagecontent)
            fp.close()
            try:
                self.cursor.execute(updatesql)
            except:
                self.logfp.write("Error writing image3 name to DB: artwork Id - %s - %s"%(awid, targetartworkimage3))
            # Do the same for image4
            if image4 == "":
                continue
            spc = re.search(srcPattern, image4)
            artworkimageurl4 = image4
            if spc:
                artworkimageurl4 = spc.groups()[0]
            artworkimageurl4 = artworkimageurl4.replace("%3A", ":").replace("%2F", "/")
            xps = re.search(extPattern, artworkimageurl4)
            ext = "jpg" # By default we save as jpeg
            if xps:
                ext = xps.groups()[0]
            img4nameondisk = "awimg4_%s_%s_%s.%s"%(awid, evid, galid, ext)
            targetartworkimage4 = "/media/galleries/events/artworks/" + img4nameondisk
            targetimage4 = targetbasedir + os.path.sep + img4nameondisk
            updatesql = "update artworks set image4='%s' where id='%s'"%(targetartworkimage4, awid)
            self.pageRequest = urllib.request.Request(artworkimageurl4, None, headers=self.httpHeaders)
            try:
                self.pageResponse = self.opener.open(self.pageRequest)
            except:
                print("Error getting '%s': %s"%(artworkimageurl4, sys.exc_info()[1].__str__()))
                continue
            imagecontent = self.pageResponse.read()
            fp = open(targetimage4, "wb")
            fp.write(imagecontent)
            fp.close()
            try:
                self.cursor.execute(updatesql)
            except:
                self.logfp.write("Error writing image4 name to DB: artwork Id - %s - %s"%(awid, targetartworkimage4))
            self.dbconn.commit()
        print("Completed processing images for artworks")




if __name__ == "__main__":
    if sys.argv.__len__() < 3:
        print("Insufficient parameters. Expects a target directory and an action.")
        sys.exit()
    action = sys.argv[1]
    targetdir = sys.argv[2]
    if action.title() == "Galleries":
        bot = ImageBot(action.title(), targetdir)
        bot.getgalleryimages()
    elif action.title() == "Events":
        bot = ImageBot(action.title(), targetdir)
        bot.geteventimages()
    elif action.title() == "Artworks":
        bot = ImageBot(action.title(), targetdir)
        bot.getartworkimages()
    print("Terminating program.")





