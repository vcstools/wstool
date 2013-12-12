class StringIO:
    """
    StringIO.StringIO does not exist in python3
    io.StringIO cannot cope with unicode
    """

    def __init__(self):
        self.stream = ''

    def write(self, data):
        self.stream += data

    def flush(self):
        pass

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

    def getvalue(self):
        return self.stream
