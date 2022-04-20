class METException(Exception):
    def __init__(self, message="There is an exception fetching the MET data"):
        self.message = message
        super().__init__(self.message)


class ExpiredMETAR(METException):
    def __init__(self, message="METAR is too old"):
        self.message = message
        super().__init__(self.message)


class METARNotAvailable(METException):
    def __init__(self, message="No METAR was found"):
        self.message = message
        super().__init__(self.message)


class ExpiredTAF(METException):
    def __init__(self, message="TAF is too old"):
        self.message = message
        super().__init__(self.message)


class TAFNotAvailable(METException):
    def __init__(self, message="No TAF was found"):
        self.message = message
        super().__init__(self.message)
