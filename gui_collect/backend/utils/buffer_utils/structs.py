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


POSITION_FMT = [
    BufferElement({
        'Name': 'POSITION',
        'SemanticName': 'POSITION',
        'SemanticIndex': '0',
        'Format': 'R32G32B32_FLOAT',
        'ByteWidth': 12
    }),
    BufferElement({
        'Name': 'NORMAL',
        'SemanticName': 'NORMAL',
        'SemanticIndex': '0',
        'Format': 'R32G32B32_FLOAT',
        'ByteWidth': 12
    }),
    BufferElement({
        'Name': 'TANGENT',
        'SemanticName': 'TANGENT',
        'SemanticIndex': '0',
        'Format': 'R32G32B32A32_FLOAT',
        'ByteWidth': 16
    }),
]

BLEND_4VGX_FMT = [
    BufferElement({
        'Name': 'BLENDWEIGHTS',
        'SemanticName': 'BLENDWEIGHTS',
        'SemanticIndex': '0',
        'Format': 'R32G32B32A32_FLOAT',
        'ByteWidth': 16
    }),
    BufferElement({
        'Name': 'BLENDINDICES',
        'SemanticName': 'BLENDINDICES',
        'SemanticIndex': '0',
        'Format': 'R32G32B32A32_UINT',
        'ByteWidth': 16
    }),
]

BLEND_2VGX_FMT = [
    BufferElement({
        'Name': 'BLENDWEIGHTS',
        'SemanticName': 'BLENDWEIGHTS',
        'SemanticIndex': '0',
        'Format': 'R32G32_FLOAT',
        'ByteWidth': 8
    }),
    BufferElement({
        'Name': 'BLENDINDICES',
        'SemanticName': 'BLENDINDICES',
        'SemanticIndex': '0',
        'Format': 'R32G32_UINT',
        'ByteWidth': 8
    }),
]

BLEND_1VGX_FMT = [
    BufferElement({
        'Name': 'BLENDINDICES',
        'SemanticName': 'BLENDINDICES',
        'SemanticIndex': '0',
        'Format': 'R32_UINT',
        'ByteWidth': 4
    }),
]
