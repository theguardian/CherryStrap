import time, datetime
from time import strptime

def now():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def today():
    today = datetime.date.today()
    yyyymmdd = datetime.date.isoformat(today)
    return yyyymmdd

def age(histdate):
    nowdate = datetime.date.today()
    m1, d1, y1 = (int(x) for x in nowdate.split('-'))
    m2, d2, y2 = (int(x) for x in histdate.split('-'))
    date1 = datetime.date(y1, m1, d1)
    date2 = datetime.date(y2, m2, d2)
    age = date1 - date2
    return age.days

def datecompare(nzbdate, control_date):
    y1 = int(nzbdate.split('-')[0])
    m1 = int(nzbdate.split('-')[1])
    d1 = int(nzbdate.split('-')[2])
    y2 = int(control_date.split('-')[0])
    m2 = int(control_date.split('-')[1])
    d2 = int(control_date.split('-')[2])
    date1 = datetime.date(y1, m1, d1)
    date2 = datetime.date(y2, m2, d2)
    age = date1 - date2
    return age.days


def checked(variable):
    if variable:
        return 'Checked'
    else:
        return ''

def latinToAscii(unicrap):
    """
    From couch potato
    """
    xlate = {0xc0:'A', 0xc1:'A', 0xc2:'A', 0xc3:'A', 0xc4:'A', 0xc5:'A',
        0xc6:'Ae', 0xc7:'C',
        0xc8:'E', 0xc9:'E', 0xca:'E', 0xcb:'E', 0x86:'e',
        0xcc:'I', 0xcd:'I', 0xce:'I', 0xcf:'I',
        0xd0:'Th', 0xd1:'N',
        0xd2:'O', 0xd3:'O', 0xd4:'O', 0xd5:'O', 0xd6:'O', 0xd8:'O',
        0xd9:'U', 0xda:'U', 0xdb:'U', 0xdc:'U',
        0xdd:'Y', 0xde:'th', 0xdf:'ss',
        0xe0:'a', 0xe1:'a', 0xe2:'a', 0xe3:'a', 0xe4:'a', 0xe5:'a',
        0xe6:'ae', 0xe7:'c',
        0xe8:'e', 0xe9:'e', 0xea:'e', 0xeb:'e', 0x0259:'e',
        0xec:'i', 0xed:'i', 0xee:'i', 0xef:'i',
        0xf0:'th', 0xf1:'n',
        0xf2:'o', 0xf3:'o', 0xf4:'o', 0xf5:'o', 0xf6:'o', 0xf8:'o',
        0xf9:'u', 0xfa:'u', 0xfb:'u', 0xfc:'u',
        0xfd:'y', 0xfe:'th', 0xff:'y',
        0xa1:'!', 0xa2:'{cent}', 0xa3:'{pound}', 0xa4:'{currency}',
        0xa5:'{yen}', 0xa6:'|', 0xa7:'{section}', 0xa8:'{umlaut}',
        0xa9:'{C}', 0xaa:'{^a}', 0xab:'<<', 0xac:'{not}',
        0xad:'-', 0xae:'{R}', 0xaf:'_', 0xb0:'{degrees}',
        0xb1:'{+/-}', 0xb2:'{^2}', 0xb3:'{^3}', 0xb4:"'",
        0xb5:'{micro}', 0xb6:'{paragraph}', 0xb7:'*', 0xb8:'{cedilla}',
        0xb9:'{^1}', 0xba:'{^o}', 0xbb:'>>',
        0xbc:'{1/4}', 0xbd:'{1/2}', 0xbe:'{3/4}', 0xbf:'?',
        0xd7:'*', 0xf7:'/'
        }

    r = ''
    for i in unicrap:
        if xlate.has_key(ord(i)):
            r += xlate[ord(i)]
        elif ord(i) >= 0x80:
            pass
        else:
            r += str(i)
    return r

def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text

def create_https_certificates(ssl_cert, ssl_key):
    """
    Create a pair of self-signed HTTPS certificares and store in them in
    'ssl_cert' and 'ssl_key'. Method assumes pyOpenSSL is installed.
    """
    import os
    from cherrystrap import logger

    from OpenSSL import crypto
    from lib.certgen import createKeyPair, createCertRequest, createCertificate, \
        TYPE_RSA, serial

    # Create the CA Certificate
    cakey = createKeyPair(TYPE_RSA, 2048)
    careq = createCertRequest(cakey, CN="Certificate Authority")
    cacert = createCertificate(careq, (careq, cakey), serial, (0, 60 * 60 * 24 * 365 * 10)) # ten years

    pkey = createKeyPair(TYPE_RSA, 2048)
    req = createCertRequest(pkey, CN="CherryStrap")
    cert = createCertificate(req, (cacert, cakey), serial, (0, 60 * 60 * 24 * 365 * 10)) # ten years

    # Save the key and certificate to disk
    try:
        if not os.path.exists('keys'):
            os.makedirs('keys')
        with open('keys/server.key', "w+") as fp:
            fp.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        with open('keys/server.crt', "w+") as fp:
            fp.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    except IOError:
        logger.error("Error creating SSL key and certificate")
        return False

    return True
