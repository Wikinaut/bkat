#!/usr/bin/env python

# konvertiert die Textversion in eine kompakte Version
# ermöglicht die Erstellung einer Datenbank

# wget -O bkat.pdf "https://www.kba.de/DE/ZentraleRegister/FAER/BT_KAT_OWI/bkat_owi_01_11_2017_pdf.pdf?__blob=publicationFile&v=2"
# pdftotext -layout bkat.pdf bkat.pdf.txt

# initial version 20210221


import re
import sys
import os
import json

def filter( line ):

    line = re.sub( '\s+', ' ', line )

    if ( re.match( '.*Stand: ', line ) ):
        return ""
    if ( re.match( '.*Nicht bedruckt', line ) ):
        return ""
    if ( re.match( '.*TBNR.*Bemerkungen', line ) ):
        return ""
    if ( re.match( '.*Tatbestandskatalog.*Tatbestände', line ) ):
        return ""
    if ( re.match( '.*Tatbestandstext.*FaP-Pkt.*Euro.*FV', line ) ):
        return ""
    if ( re.match( '.*\*\).*(Änderung an|Vorschrifts|Zutreffend|nicht ordnungsgem|näher erläutern)', line, flags=re.IGNORECASE ) ):
        return ""

    return line


def clean( line ):
    line = re.sub( ' \*\*\*\)', '', line.strip() )
    line = re.sub( ' \*\*\)', '', line )
    line = re.sub( ' \*\)', '', line )
    return re.sub( ' \+\)', '', line ).strip()


def setheader( header ):
    global newheader

    newheader = header
    if (not aggregate):
        printheader()
    return


def printheader():
    global newheader

    if ( newheader != "" ):
        print( "------ {0}\n".format( newheader) )
    newheader = ""
    return


def flush_buffer():
    global punkte,bkat

    if (aggregate):

        pkte = ""
        p = ""
        if ( punkte != "0" ):
            pkte = " P:"+punkte
            p = punkte

        fv = ""
        f = ""
        if fahrverbot is not None:
            fv = " FV:" + fahrverbot[0] + " " + fahrverbot[1]
            f = fahrverbot[0] + " " + fahrverbot[1]

        print( "TBNR {0} {1} €{2}{3}\n{4}\n".format( tbnr, euro, pkte, fv, buf ) )
        # print( "TBNR {0} {1} €{2}{3}\n{4}\nLegal: {5}\n".format( tbnr, euro, pkte, fv, buf, legal ) )

        bkat[ 'tatbestaende' ].append( {
            "tbnr": tbnr,
            "txt": buf,
            "eur": euro,
            "legal": legal,
            "p": p,
            "fv": f,
            "stand": standymd,
        } )

        printheader()

    return



def main():
    global aggregate,fahrverbot,tbnr,euro,punkte,buf,stand,standymd,legal
    global bkat

    bkat = {}
    bkat['tatbestaende'] = []

    infile = open("bkat.pdf.txt")

    lines = infile.readlines()
    buf = ""
    legal = ""
    aggregate = False
    heading = ""
    stand = ""
    standymd = ""

    for line in lines:

        # print( "{:05d} {}".format( ln, line.strip() ) )

        # Vorübergehende Teilnahme am Straßenverkehr im Inland - § 20 FZV                        Seite 372/ 1
        # 103640 Sie überschritten die zulässige Höchstgeschwindigkeit innerhalb        A-2      280,00   2M

        res = re.match( 'Stand: (.*Auflage)', line )
        if ( ( res ) and ( stand == "" ) ):
            stand = res.group(1)
            print( "Bkat Stand: {0}\n".format( stand ) )
            res = re.match( '(\d\d).(\d\d).(2\d\d\d)', stand )
            if ( res ):
                standymd = res.group(3) + res.group(2) + res.group(1)

        res = re.match( '(.*) Seite\s(.*)$', line )

        if (res):
            group1 = res.group(1).strip()

            if ( group1 != heading ) \
                and ( group1 != "" ) \
                and ( group1 != "Nicht bedruckt" ) \
                and ( group1 != "Stichwortverzeichnis mit Angabe der §§" ):

                heading = res.group(1).strip()
                setheader( heading )
            continue

        res = re.match( 'Tabellen', line.strip() )
        if (res):
            flush_buffer()
            aggregate = False
            continue

        res = re.match( '(\d{6})(.*?)  ([012456789AB-]+)  .*?  (\d+,\d\d).*?(\d+M)', line )
        if (res):

            if (aggregate):
                flush_buffer()

            aggregate = True

            tbnr = res.group(1)
            buf = clean( res.group(2) )
            punkte = res.group(3)
            euro = res.group(4)
            fahrverbot = res.group(5)

        else:

            res = re.match( '(\d{6})(.*?)  ([0123456789AB-]+)  .*?  (\d+,\d\d)', line )

            if (res):

                if (aggregate):
                    flush_buffer()

                aggregate = True

                tbnr = res.group(1)
                buf = clean( res.group(2) )
                punkte = res.group(3)
                euro = res.group(4)
                fahrverbot = None

            else:

                if (aggregate):
                    ln = filter( line ).strip()
                    if ( ln != "" ):
                        if ( re.search( "^§.*(BKat|OWiG|BkatV|StVG);?$", ln, flags=re.IGNORECASE ) ):
                            if ( buf[-1] != ";" ):
                                # buf = buf + "\n"+filter( line ).strip()
                                legal = filter( line ).strip()
                            else:
                                # buf = buf + " " + filter( line ).strip()
                                legal = legal + " " + filter( line ).strip()
                        else:
                            if ( buf[-1] == "-" ):
                                buf = buf[:-1] + clean( filter( line ) )
                            elif ( buf[-1] == "/" ):
                                buf = buf + clean( filter( line ) )
                            else:
                                buf = buf + " " + clean( filter( line ) )


    flush_buffer()

    with open( 'bkat.json', 'w' ) as outfile:
        # json.dump( bkat, outfile, sort_keys=True, indent=4 )
        json.dump( bkat, outfile, indent=4 )

    return


if __name__ == "__main__":
    main()
