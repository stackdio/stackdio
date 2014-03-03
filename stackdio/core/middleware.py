class JSONIndentAcceptHeaderMiddleware(object):

    def process_request(self, request):
        request.META['HTTP_ACCEPT'] = 'application/json; indent=4'
        return None
