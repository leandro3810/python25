from __future__ import absolute_import, division, unicode_literals

from pip._vendor.six import text_type
from pip._vendor.six.moves import http_client, urllib

import codecs
import re
from io import BytesIO, StringIO

from pip._vendor import webencodings

from .constants import EOF, spaceCharacters, asciiLetters, asciiUppercase
from .constants import _ReparseException
from . import _utils

# Non-unicode versions of constants for use in the pre-parser
spaceCharactersBytes = frozenset(item.encode("ascii") for item in spaceCharacters)
asciiLettersBytes = frozenset(item.encode("ascii") for item in asciiLetters)
asciiUppercaseBytes = frozenset(item.encode("ascii") for item in asciiUppercase)
spacesAngleBrackets = spaceCharactersBytes | frozenset([b">", b"<"])



if _utils.supports_lone_surrogates:
    assert invalid_unicode_no_surrogate[-1] == "]" and invalid_unicode_no_surrogate.count("]") == 1
    invalid_unicode_re = re.compile(invalid_unicode_no_surrogate[:-1] + r"\\uD800-\\uDFFF]")
else:
    invalid_unicode_re = re.compile(invalid_unicode_no_surrogate)

non_bmp_invalid_codepoints = {0x1FFFE, 0x1FFFF, 0x2FFFE, 0x2FFFF, 0x3FFFE,
                              0x3FFFF, 0x4FFFE, 0x4FFFF, 0x5FFFE, 0x5FFFF,
                              0x6FFFE, 0x6FFFF, 0x7FFFE, 0x7FFFF, 0x8FFFE,
                              0x8FFFF, 0x9FFFE, 0x9FFFF, 0xAFFFE, 0xAFFFF,
                              0xBFFFE, 0xBFFFF, 0xCFFFE, 0xCFFFF, 0xDFFFE,
                              0xDFFFF, 0xEFFFE, 0xEFFFF, 0xFFFFE, 0xFFFFF,
                              0x10FFFE, 0x10FFFF}

ascii_punctuation_re = re.compile("[\u0009-\u000D\u0020-\u002F\u003A-\u0040\u005C\u005B-\u0060\u007B-\u007E]")

# Cache for charsUntil()
charsUntilRegEx = {}

class BufferedStream(object):
    def __init__(self, stream):
        self.stream = stream
        self.buffer = []
        self.position = 0

    def tell(self):
        return self.position

    def seek(self, pos):
        self.position = pos

    def read(self, bytes):
        data = self._readStream(bytes)
        self.position += len(data)
        return data

    def _readStream(self, bytes):
        return self.stream.read(bytes)

class BaseHTMLInputStream(object):
    _defaultChunkSize = 10240

    def __init__(self, source):
        if not _utils.supports_lone_surrogates:
            self.reportCharacterErrors = None
        elif len("\U0010FFFF") == 1:
            self.reportCharacterErrors = self.characterErrorsUCS4
        else:
            self.reportCharacterErrors = self.characterErrorsUCS2

        self.newLines = [0]
        self.dataStream = self.openStream(source)
        self.reset()

    def reset(self):
        self.chunk = ""
        self.chunkSize = 0
        self.chunkOffset = 0
        self.errors = []
        self.prevNumLines = 0
        self.prevNumCols = 0
        self._bufferedCharacter = None

    def openStream(self, source):
        return source if hasattr(source, 'read') else StringIO(source)

    def _position(self, offset):
        chunk = self.chunk
        nLines = chunk.count('\n', 0, offset)
        positionLine = self.prevNumLines + nLines
        lastLinePos = chunk.rfind('\n', 0, offset)
        if lastLinePos == -1:
            positionColumn = self.prevNumCols + offset
        else:
            positionColumn = offset - (lastLinePos + 1)
        return (positionLine, positionColumn)

    def position(self):
        line, col = self._position(self.chunkOffset)
        return (line + 1, col)

    def char(self):
        if self.chunkOffset >= self.chunkSize and not self.readChunk():
            return EOF

        char = self.chunk[self.chunkOffset]
        self.chunkOffset += 1
        return char

    def readChunk(self, chunkSize=None):
        if chunkSize is None:
            chunkSize = self._defaultChunkSize

        self.prevNumLines, self.prevNumCols = self._position(self.chunkSize)
        self.chunk = ""
        self.chunkSize = 0
        self.chunkOffset = 0

        data = self.dataStream.read(chunkSize)

        if self._bufferedCharacter:
            data = self._bufferedCharacter + data
            self._bufferedCharacter = None
        elif not data:
            return False

        if len(data) > 1:
            lastv = ord(data[-1])
            if lastv == 0x0D or 0xD800 <= lastv <= 0xDBFF:
                self._bufferedCharacter = data[-1]
                data = data[:-1]

        if self.reportCharacterErrors:
            self.reportCharacterErrors(data)

        data = data.replace("\r\n", "\n").replace("\r", "\n")
        self.chunk = data
        self.chunkSize = len(data)
        return True

    def characterErrorsUCS4(self, data):
        for _ in range(len(invalid_unicode_re.findall(data))):
            self.errors.append("invalid-codepoint")

    def characterErrorsUCS2(self, data):
        skip = False
        for match in invalid_unicode_re.finditer(data):
            if skip:
                continue
            codepoint = ord(match.group())
            pos = match.start()
            if _utils.isSurrogatePair(data[pos:pos + 2]):
                char_val = _utils.surrogatePairToCodepoint(data[pos:pos + 2])
                if char_val in non_bmp_invalid_codepoints:
                    self.errors.append("invalid-codepoint")
                skip = True
            elif codepoint >= 0xD800 and codepoint <= 0xDFFF and pos == len(data) - 1:
                self.errors.append("invalid-codepoint")
            else:
                skip = False
                self.errors.append("invalid-codepoint")

    def charsUntil(self, characters, opposite=False):
        try:
            chars = charsUntilRegEx[(characters, opposite)]
        except KeyError:
            regex = "".join(["\\x%02x" % ord(c) for c in characters])
            if not opposite:
                regex = "^%s" % regex
            chars = charsUntilRegEx[(characters, opposite)] = re.compile("[%s]+" % regex)

        rv = []
        while True:
            m = chars.match(self.chunk, self.chunkOffset)
            if m is None:
                if self.chunkOffset != self.chunkSize:
                    break
            else:
                end = m.end()
                if end != self.chunkSize:
                    rv.append(self.chunk[self.chunkOffset:end])
                    self.chunkOffset = end
                    break
            rv.append(self.chunk[self.chunkOffset:])
            if not self.readChunk():
                break

        return "".join(rv)

    def unget(self, char):
        if char is not EOF:
            if self.chunkOffset == 0:
                self.chunk = char + self.chunk
                self.chunkSize += 1
            else:
                self.chunkOffset -= 1
                assert self.chunk[self.chunkOffset] == char

class HTMLUnicodeInputStream(BaseHTMLInputStream):
    def __init__(self, source):
        super().__init__(source)

class HTMLBinaryInputStream(BaseHTMLInputStream):
    def __init__(self, source, override_encoding=None, transport_encoding=None,
                 same_origin_parent_encoding=None, likely_encoding=None,
                 default_encoding="windows-1252", useChardet=True):
        self.rawStream = self.openStream(source)
        super().__init__(self.rawStream)
        self.override_encoding = override_encoding
        self.transport_encoding = transport_encoding
        self.same_origin_parent_encoding = same_origin_parent_encoding
        self.likely_encoding = likely_encoding
        self.default_encoding = default_encoding
        self.charEncoding = self.determineEncoding(useChardet)
        assert self.charEncoding[0] is not None
        self.reset()

    def reset(self):
        self.dataStream = self.charEncoding[0].codec_info.streamreader(self.rawStream, 'replace')
        super().reset()

    def openStream(self, source):
        stream = source if hasattr(source, 'read') else BytesIO(source)
        try:
            stream.seek(stream.tell())
        except Exception:
            stream = BufferedStream(stream)
        return stream

    def determineEncoding(self, chardet=True):
        charEncoding = self.detectBOM(), "certain"
        if charEncoding[0] is not None:
            return charEncoding

        charEncoding = lookupEncoding(self.override_encoding), "certain"
        if charEncoding[0] is not None:
            return charEncoding

        charEncoding = lookupEncoding(self.transport_encoding), "certain"
        if charEncoding[0] is not None:
            return charEncoding

        charEncoding = self.detectEncodingMeta(), "tentative"
        if charEncoding[0] is not None:
            return charEncoding

        charEncoding = lookupEncoding(self.same_origin_parent_encoding), "tentative"
        if charEncoding[0] is not None and not charEncoding[0].name.startswith("utf-16"):
            return charEncoding

        charEncoding = lookupEncoding(self.likely_encoding), "tentative"
        if charEncoding[0] is not None:
            return charEncoding

        if chardet:
            try:
                from pip._vendor.chardet.universaldetector import UniversalDetector
            except ImportError:
                pass
            else:
                buffers = []
                detector = UniversalDetector()
                while not detector.done:
                    buffer = self.rawStream.read(self.numBytesChardet)
                    assert isinstance(buffer, bytes)
                    if not buffer:
                        break
                    buffers.append(buffer)
                    detector.feed(buffer)
                detector.close()
                encoding = lookupEncoding(detector.result['encoding'])
                self.rawStream.seek(0)
                if encoding is not None:
                    return encoding, "tentative"

        charEncoding = lookupEncoding(self.default_encoding), "tentative"
        if charEncoding[0] is not None:
            return charEncoding

        return lookupEncoding("windows-1252"), "tentative"

    def changeEncoding(self, newEncoding):
        assert self.charEncoding[1] != "certain"
        newEncoding = lookupEncoding(newEncoding)
        if newEncoding is None:
            return
        if newEncoding.name in ("utf-16be", "utf-16le"):
            newEncoding = lookupEncoding("utf-8")
            assert newEncoding is not None
        elif newEncoding == self.charEncoding[0]:
            self.charEncoding = (self.charEncoding[0], "certain")
        else:
            self.rawStream.seek(0)
            self.charEncoding = (newEncoding, "certain")
            self.reset()
            raise _ReparseException(f"Encoding changed from {self.charEncoding[0]} to {newEncoding}")

    def detectBOM(self):
        bomDict = {
            codecs.BOM_UTF8: 'utf-8',
            codecs.BOM_UTF16_LE: 'utf-16le', codecs.BOM_UTF16_BE: 'utf-16be',
            codecs.BOM_UTF32_LE: 'utf-32le', codecs.BOM_UTF32_BE: 'utf-32be'
        }

        string = self.rawStream.read(4)
        assert isinstance(string, bytes)

        encoding = bomDict.get(string[:3])
        seek = 3
        if not encoding:
            encoding = bomDict.get(string)
            seek = 4
        if not encoding:
            encoding = bomDict.get(string[:2])
            seek = 2

        if encoding:
            self.rawStream.seek(seek)
            return lookupEncoding(encoding)
        else:
            self.rawStream.seek(0)
            return None

    def detectEncodingMeta(self):
        buffer = self.rawStream.read(self.numBytesMeta)
        assert isinstance(buffer, bytes)
        parser = EncodingParser(buffer)
        self.rawStream.seek(0)
        encoding = parser.getEncoding()

        if encoding is not None and encoding.name in ("utf-16be", "utf-16le"):
            encoding = lookupEncoding("utf-8")

        return encoding

def lookupEncoding(encoding):
    if isinstance(encoding, bytes):
        try:
            encoding = encoding.decode("ascii")
        except UnicodeDecodeError:
            return None

    if encoding is not None:
        try:
            return webencodings.lookup(encoding)
        except AttributeError:
            return None
    return None
