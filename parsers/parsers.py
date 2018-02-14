import sys, os, glob, traceback, io

from StringIO import StringIO
from email.parser import Parser as EmailParser
import email.utils

from rest_framework.parsers import BaseParser
from rest_framework.exceptions import ParseError

from django.utils.six import text_type

from olefile import OleFileIO


def windowsUnicode(string):
    if string is None:
        return None
    if sys.version_info[0] >= 3:  # Python 3
        return str(string, 'utf_16_le')
    else:  # Python 2
        return unicode(string, 'utf_16_le')


class Attachment:
    def __init__(self, msg, dir_):
        # Get long filename
        self.longFilename = msg._getStringStream([dir_, '__substg1.0_3707'])

        # Get short filename
        self.shortFilename = msg._getStringStream([dir_, '__substg1.0_3704'])

        # Get attachment data
        self.data = msg._getStream([dir_, '__substg1.0_37010102'])

    def save(self):
        # Use long filename as first preference
        filename = self.longFilename
        # Otherwise use the short filename
        if filename is None:
            filename = self.shortFilename
        # Otherwise just make something up!
        if filename is None:
            import random
            import string
            filename = 'UnknownFilename ' + \
                ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(5)) + ".bin"
        f = open(filename, 'wb')
        f.write(self.data)
        f.close()
        return filename

class Message(OleFileIO):
    def __init__(self, filename):
        OleFileIO.__init__(self, filename)

    def _getStream(self, filename):
        if self.exists(filename):
            stream = self.openstream(filename)
            return stream.read()
        else:
            return None

    def _getStringStream(self, filename, prefer='unicode'):
        """Gets a string representation of the requested filename.
        Checks for both ASCII and Unicode representations and returns
        a value if possible.  If there are both ASCII and Unicode
        versions, then the parameter /prefer/ specifies which will be
        returned.
        """

        if isinstance(filename, list):
            # Join with slashes to make it easier to append the type
            filename = "/".join(filename)

        asciiVersion = self._getStream(filename + '001E')
        unicodeVersion = windowsUnicode(self._getStream(filename + '001F'))
        if asciiVersion is None:
            return unicodeVersion
        elif unicodeVersion is None:
            return asciiVersion
        else:
            if prefer == 'unicode':
                return unicodeVersion
            else:
                return asciiVersion

    @property
    def subject(self):
        return self._getStringStream('__substg1.0_0037')

    @property
    def header(self):
        try:
            return self._header
        except Exception:
            headerText = self._getStringStream('__substg1.0_007D')
            if headerText is not None:
                self._header = EmailParser().parsestr(headerText)
            else:
                self._header = None
            return self._header

    @property
    def date(self):
        # Get the message's header and extract the date
        if self.header is None:
            return None
        else:
            return self.header['date']

    @property
    def parsedDate(self):
        return email.utils.parsedate(self.date)

    @property
    def sender(self):
        try:
            return self._sender
        except Exception:
            # Check header first
            if self.header is not None:
                headerResult = self.header["from"]
                if headerResult is not None:
                    self._sender = headerResult
                    return headerResult

            # Extract from other fields
            text = self._getStringStream('__substg1.0_0C1A')
            email = self._getStringStream('__substg1.0_0C1F')
            result = None
            if text is None:
                result = email
            else:
                result = text
                if email is not None:
                    result = result + " <" + email + ">"

            self._sender = result
            return result

    @property
    def to(self):
        try:
            return self._to
        except Exception:
            # Check header first
            if self.header is not None:
                headerResult = self.header["to"]
                if headerResult is not None:
                    self._to = headerResult
                    return headerResult

            # Extract from other fields
            # TODO: This should really extract data from the recip folders,
            # but how do you know which is to/cc/bcc?
            display = self._getStringStream('__substg1.0_0E04')
            self._to = display
            return display

    @property
    def cc(self):
        try:
            return self._cc
        except Exception:
            # Check header first
            if self.header is not None:
                headerResult = self.header["cc"]
                if headerResult is not None:
                    self._cc = headerResult
                    return headerResult

            # Extract from other fields
            # TODO: This should really extract data from the recip folders,
            # but how do you know which is to/cc/bcc?
            display = self._getStringStream('__substg1.0_0E03')
            self._cc = display
            return display

    @property
    def body(self):
        # Get the message body
        return self._getStringStream('__substg1.0_1000')

    @property
    def attachments(self):
        try:
            return self._attachments
        except Exception:
            # Get the attachments
            attachmentDirs = []

            for dir_ in self.listdir():
                if dir_[0].startswith('__attach') and dir_[0] not in attachmentDirs:
                    attachmentDirs.append(dir_[0])

            self._attachments = []

            for attachmentDir in attachmentDirs:
                self._attachments.append(Attachment(self, attachmentDir))

            return self._attachments

    def save(self, toJson=False, useFileName=False, raw=False):
        '''Saves the message body and attachments found in the message.  Setting toJson
        to true will output the message body as JSON-formatted text.  The body and
        attachments are stored in a folder.  Setting useFileName to true will mean that
        the filename is used as the name of the folder; otherwise, the message's date
        and subject are used as the folder name.'''

        if useFileName:
            # strip out the extension
            dirName = filename.split('/').pop().split('.')[0]
        else:
            # Create a directory based on the date and subject of the message
            d = self.parsedDate
            if d is not None:
                dirName = '{0:02d}-{1:02d}-{2:02d}_{3:02d}{4:02d}'.format(*d)
            else:
                dirName = "UnknownDate"

            if self.subject is None:
                subject = "[No subject]"
            else:
                subject = "".join(i for i in self.subject if i not in r'\/:*?"<>|')

            dirName = dirName + " " + subject

        def addNumToDir(dirName):
            # Attempt to create the directory with a '(n)' appended

            for i in range(2, 100):
                try:
                    newDirName = dirName + " (" + str(i) + ")"
                    os.makedirs(newDirName)
                    return newDirName
                except Exception:
                    pass
            return None

        try:
            os.makedirs(dirName)
        except Exception:
            newDirName = addNumToDir(dirName)
            if newDirName is not None:
                dirName = newDirName
            else:
                raise Exception(
                    "Failed to create directory '%s'. Does it already exist?" %
                    dirName
                    )

        oldDir = os.getcwd()
        try:
            os.chdir(dirName)

            # Save the message body
            fext = 'json' if toJson else 'text'
            f = open("message." + fext, "w")
            # From, to , cc, subject, date

            def xstr(s):
                return '' if s is None else str(s)

            attachmentNames = []
            # Save the attachments
            for attachment in self.attachments:
                attachmentNames.append(attachment.save())

            if toJson:
                import json
                from imapclient.imapclient import decode_utf7

                emailObj = {'from': xstr(self.sender),
                            'to': xstr(self.to),
                            'cc': xstr(self.cc),
                            'subject': xstr(self.subject),
                            'date': xstr(self.date),
                            'attachments': attachmentNames,
                            'body': decode_utf7(self.body)}

                f.write(json.dumps(emailObj, ensure_ascii=True))
            else:
                f.write("From: " + xstr(self.sender) + "\n")
                f.write("To: " + xstr(self.to) + "\n")
                f.write("CC: " + xstr(self.cc) + "\n")
                f.write("Subject: " + xstr(self.subject) + "\n")
                f.write("Date: " + xstr(self.date) + "\n")
                f.write("-----------------\n\n")
                f.write(self.body)

            f.close()

        except Exception:
            self.saveRaw()
            raise

        finally:
            # Return to previous directory
            os.chdir(oldDir)

    def saveRaw(self):
        # Create a 'raw' folder
        oldDir = os.getcwd()
        try:
            rawDir = "raw"
            os.makedirs(rawDir)
            os.chdir(rawDir)
            sysRawDir = os.getcwd()

            # Loop through all the directories
            for dir_ in self.listdir():
                sysdir = "/".join(dir_)
                code = dir_[-1][-8:-4]
                global properties
                if code in properties:
                    sysdir = sysdir + " - " + properties[code]
                os.makedirs(sysdir)
                os.chdir(sysdir)

                # Generate appropriate filename
                if dir_[-1].endswith("001E"):
                    filename = "contents.txt"
                else:
                    filename = "contents"

                # Save contents of directory
                f = open(filename, 'wb')
                f.write(self._getStream(dir_))
                f.close()

                # Return to base directory
                os.chdir(sysRawDir)

        finally:
            os.chdir(oldDir)

    def dump(self):
        # Prints out a summary of the message
        print('Message')
        print('Subject:', self.subject)
        print('Date:', self.date)
        print('Body:')
        print(self.body)

    def save_attachments(self, raw=False):
        """Saves only attachments in the same folder.
        """
        for attachment in self.attachments:
            attachment.save()




class MailParser(BaseParser):
    """
        parses email serialized data
    """

    media_type = "multipart/form-data"

    def parse(self, stream, media_type = None, parser_context = None):
        # print stream.body.decode()
        # print dir(stream)
        # print "FILES ", stream.FILES
        # print "META ", stream.META
        # print "POST ", stream.POST
        # print "_encoding ", stream._encoding
        # print "CONTENT PARAMS ", stream.content_params
        # print "ENCODING ", stream.encoding
        # # print "PARSER ", stream.parse_file_upload()
        # print "STREAM READ ", stream.read()
        # print "________"
        # print dir(stream.body)
        # print "________"

        try:
            f = io.BytesIO(stream.read())
            print f
            # print f.getvalue()
            # print f.read()
            print dir(f)
            # with open("/tmp/2.msg", 'wb') as msgFile:
            #     msgFile.write(stream.body)
            return Message(f.read())
            # return Message(stream.body)
        except Exception as exc:
            print exc
            raise ParseError("Email parse error - %s" % text_type(exc))
