
class Constant(type):
    _constants = {}

    def __new__(mcs, *args, **kwargs):
        self = super(Constant, mcs).__new__(mcs, *args, **kwargs)
        mcs._constants[self] = args[2]
        return self

    def __getitem__(self, item):
        return self._constants[self][item]

class Role(metaclass=Constant):
    ADMIN           = [0]
    MOD             = [0]
    BOT_DEV         = [0]
    TICKET_PING     =  0

class Channel(metaclass=Constant):
    REPORTS         = 0
    MOD_LOGS        = 0
    CUSTOM_VC_CATEGORY = 0
    TICKETS         = 0


class Misc(metaclass=Constant):
    GUILD_ID        = 0
