class JSONIndentAcceptHeaderMiddleware(object):

    def process_request(self, request):
        if request.META.get('HTTP_ACCEPT') == 'application/json':
            request.META['HTTP_ACCEPT'] = 'application/json; indent=4'
        return None
