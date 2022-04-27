import os, sys, re, time
import unicodedata
import io
import datetime
import string
from urllib.parse import urlencode, quote_plus, urlparse
import csv
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb



if __name__ == "__main__":
    if sys.argv.__len__() < 2:
        print("Insufficient parameters. Expecting target directory as a parameter.")
        sys.exit()
    targetdirpath = sys.argv[1] # Get the target directory as commandline argument
    if not os.path.exists(targetdirpath) or not os.path.isdir(targetdirpath): # Create directory if it doesn't exist
        os.makedirs(targetdirpath)
    dbconn = MySQLdb.connect(user="artsyuser",passwd="artbank#12Passwd",host="localhost",db="artsydb")
    cursor = dbconn.cursor()
    #datasql = "select g.galleryname as galleryname, g.location as gallerylocation, g.description as gallerydescription, g.coverimage as galleryimage, g.gallerytype as gallerytype, g.id as galleryid, e.eventname as eventname, e.eventperiod, e.eventstartdate as eventstartdate, e.eventenddate as eventenddate, e.eventinfo as eventinfo, e.eventtype as eventtype, e.eventlocation as eventlocation, e.id as eventid from events e left join galleries g on e.gallery_id=g.id"
    datasql = "select aw.id as artworkid, aw.artworkname as artworkname, aw.artistname as artistname, aw.artistbirthyear as artistbirthyear, aw.artistdeathyear as artistdeathyear, aw.artistnationality as artistnationality, aw.size as size, aw.medium as medium, aw.estimate as estimate, aw.soldprice as soldprice, aw.description as description, aw.image1 as artworkimage1, aw.image2 as artworkimage2, aw.image3 as artworkimage3, aw.image4 as artworkimage4, g.galleryname as galleryname, g.location as gallerylocation, g.description as gallerydescription, g.coverimage as galleryimage, g.gallerytype as gallerytype, g.id as galleryid, e.eventname as eventname, e.eventperiod, e.eventstartdate as eventstartdate, e.eventenddate as eventenddate, e.eventinfo as eventinfo, e.eventtype as eventtype, e.eventlocation as eventlocation, e.id as eventid from artworks aw left join events e on aw.event_id=e.id left join galleries g on e.gallery_id=g.id"
    cursor.execute(datasql)
    header = '"ArtworkID", "ArtworkName", "ArtistName", "ArtistBirth", "ArtistDeath", "ArtistNationality", "ArtworkSize", "ArtworkMedium", "Estimate", "SoldPrice", "ArtworkDescription", "ArtworkImage1", "ArtworkImage2", "ArtworkImage3", "ArtworkImage4", "GalleryName", "GalleryLocation", "GalleryDescription","GalleryImage", "GalleryType", "GalleryId", "EventName", "EventPeriod",  "EventStartDate", "EventEndDate", "EventInfo", "EventType", "EventLocation", "EventId"\n'
    csvfile = targetdirpath + os.path.sep + "galleryeventartworks.csv"
    fcsv = open(csvfile, "w")
    fcsv.write(header)
    records = cursor.fetchall()
    for rec in records:
        awid = rec[0]
        artworkname = rec[1]
        artistname = rec[2]
        artistbirthyear = rec[3]
        artistdeathyear = rec[4]
        artistnationality = rec[5]
        size = rec[6]
        medium = rec[7]
        estimate = rec[8]
        soldprice = rec[9]
        description = rec[10]
        artworkimage1 = rec[11]
        artworkimage2 = rec[12]
        artworkimage3 = rec[13]
        artworkimage4 = rec[14]
        galleryname = rec[15]
        galleryloc = rec[16]
        gallerydesc = rec[17]
        galleryimage = rec[18]
        gallerytype = rec[19]
        galleryid = rec[20]
        eventname = rec[21]
        eventperiod = rec[22]
        eventstartdate = rec[23]
        eventenddate = rec[24]
        eventinfo = rec[25]
        eventtype = rec[26]
        eventloc = rec[27]
        eventid = rec[28]
        galleryfilename = targetdirpath + os.path.sep + "gal_%s.txt"%galleryid
        eventfilename = targetdirpath + os.path.sep + "ev_%s_%s.txt"%(eventid, galleryid)
        artworkfilename = targetdirpath + os.path.sep + "aw_%s_%s_%s.txt"%(awid, eventid, galleryid)
        fgal = open(galleryfilename, "w")
        fgal.write(gallerydesc)
        fgal.close()
        fev = open(eventfilename, "w")
        fev.write(eventinfo)
        fev.close()
        faw = open(artworkfilename, "w")
        faw.write(description)
        faw.close()
        data = '"%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s"\n'%(awid, artworkname, artistname, artistbirthyear, artistdeathyear, artistnationality, size, medium, estimate, soldprice, artworkfilename, artworkimage1, artworkimage2, artworkimage3, artworkimage4, galleryname, galleryloc, galleryfilename, galleryimage, gallerytype, galleryid, eventname, eventperiod, eventstartdate, eventenddate, eventfilename, eventtype, eventloc, eventid) # Formulate the data record here.
        fcsv.write(data)
    fcsv.close()







