from enum import Enum, auto


class BufferType(Enum):
    Position_VB = auto()
    Blend_VB    = auto()
    Texcoord_VB = auto()
    Draw_VB     = auto()
    IB          = auto()


BUFFER_NAME = {
    BufferType.Position_VB : 'Position VB',
    BufferType.Blend_VB    : 'Blend VB',
    BufferType.Texcoord_VB : 'Texcoord VB',
    BufferType.Draw_VB     : 'Draw VB',
    BufferType.IB          : 'IB',
}


class BufferElement():
    def __init__(self, data: dict):
        self.Name      = ''
        self.ByteWidth = 0

        self.SemanticName         = ''
        self.SemanticIndex        = ''
        self.Format               = ''
        self.InputSlot            = ''
        self.AlignedByteOffset    = 0
        self.InputSlotClass       = ''
        self.InstanceDataStepRate = ''

        for key, value in data.items():
            key = key.replace(' ', '')
            if self.__getattribute__(key) is None:
                raise Exception('New key encountered {}'.format(key))
            self.__setattr__(key.replace(' ', ''), value)
