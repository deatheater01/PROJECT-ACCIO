#
# created by Tarun and Pitchappan on 20/10/18
#
# Project Accio
#

def chunk(iterable, chunk_size=20):
    items = []
    for value in iterable:
        items.append(value)
        if len(items) == chunk_size:
            yield items
            items = []
    if items:
        yield items


class MessageRouter(object):
    node = None
    routes = []

    def route(self, pattern):
        def wrapper(handler):
            self.routes.append((pattern, handler))
            return handler
        return wrapper

    def recv(self, program, message, interface=None):

        def default_route(program, message=None, interface=None):
            pass

        for pattern, handler in self.routes:
            if hasattr(pattern, 'match') and pattern.match(message):
                break
            if message == pattern:
                break
        else:
            handler = default_route

        handler(program, message, interface)
