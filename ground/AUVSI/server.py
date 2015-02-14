from twisted.internet import reactor, protocol
from twisted.web.client import getPage


def printPage(result):
    print result


def printError(failure):
    print failure


class EchoClient(protocol.Protocol):
    def connectionMade(self):
        self.factory.app.on_connection(self.transport)

    def connectionLost(self, reason):
        self.factory.app.on_disconnection(self.transport)

    def dataReceived(self, data):
        self.factory.app.print_message(data)


class ServerFactory(protocol.ReconnectingClientFactory):
    protocol = EchoClient
    maxDelay = 1
    initialDelay = 0.1
    
    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        self.app.print_message("connection lost")
        self.retry(conn)

    def clientConnectionFailed(self, conn, reason):
        self.app.print_message("connection failed")
        self.retry(conn)


def connect(app):
    reactor.connectTCP('192.168.1.13', 8000, ServerFactory(app))
    

def access(page):
    d = getPage('http://192.168.1.13:8000/'+page)
    d.addCallbacks(printPage, printError)
