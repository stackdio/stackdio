from rest_framework.parsers import BaseParser

class PlainTextParser(BaseParser):
    media_type = 'text/plain'

    def parse(self, stream, media_type, parser_context):
        return stream.read()

class CSVParser(PlainTextParser):
    media_type = 'application/csv'

class XMLParser(PlainTextParser):
    media_type = 'application/xml'

    # TODO: We could use lxml to parse this guy, but I'm using this parser
    # solely to get DRF to check for and raise exceptions when an invalid
    # media_type is given during a request without requiring special
    # modules or heavy lifting
