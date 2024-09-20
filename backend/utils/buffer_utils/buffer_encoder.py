import re

from .structs import BufferElement

from frontend.state import State


def merge_buffers(buffers, buffer_formats: list[dict]):
    vertex_count = len(buffers[0])

    merged_data = []
    for j in range(vertex_count):
        temp = []
        for buffer in buffers:
            temp.extend(buffer[j])
        merged_data.append(temp)

    merged_format = []
    for buffer_format in buffer_formats:
        merged_format.extend(buffer_format)

    return construct_combined_buffer(merged_data, merged_format)


# Constructs the output file that will be loaded into 3dmigoto
def construct_combined_buffer(buffer_data, buffer_elements: list[BufferElement]):

    stride = sum([element.ByteWidth for element in buffer_elements])

    vb_merged = '\n'.join([
        'stride: {}'       .format(stride),
        'first vertex: 0',
        'vertex count: {}' .format(len(buffer_data)),
        'topology: trianglelist',
        '',
    ])

    terminal = State.get_instance().get_terminal()

    byte_offset = 0
    byte_offsets, element_names = [], []
    for i, element in enumerate(buffer_elements):

        byte_offsets .append(f'{str(byte_offset).zfill(3)}')
        element_names.append(element.Name)

        vb_merged += '\n'.join([
            f'element[{i}]:',
            f'  SemanticName: {element.SemanticName}',
            f'  SemanticIndex: {element.SemanticIndex}',
            f'  Format: {element.Format}',
            f'  InputSlot: 0',
            f'  AlignedByteOffset: {byte_offset}',
            f'  InputSlotClass: per-vertex',
            f'  InstanceDataStepRate: 0',
            ''
        ])
        byte_offset += element.ByteWidth

        terminal.print(f'{element.Name:12} - {element.ByteWidth:2} - {element.Format}', timestamp=False)

    terminal.print(f'Total Stride: {stride}\n', timestamp=False)

    vb_merged += '\nvertex-data:\n\n'
    
    # Scyll: Extremely fast - avoid excessive string concatenation with +=
    vb_merged += '\n'.join([
        ''.join([
            f'vb0[{i}]+{byte_offsets[j]} {element_names[j]}: {", ".join(map(str, buffer_data[i][j]))}\n'
            for j in range(len(buffer_elements))
        ])
        for i in range(len(buffer_data))
    ])

    # Scyll: Equivalent to (Slow):
    # for i in range(len(buffer_data)):
    #     byte_offset = 0
    #     for j, element in enumerate(element_format):
    #         vb_merged += f'vb0[{i}]+{str(byte_offset).zfill(3)} {element["element_name"]}: {", ".join(buffer_data[i][j])}\n'
    #         byte_offset += element['bytewidth']
    #     vb_merged += "\n"

    return vb_merged


def handle_no_weight_blend(blend, blend_elements: list[BufferElement]):
    if (
        len(blend_elements) == 1
        and blend_elements[0].Name   == 'BLENDINDICES'
        and blend_elements[0].Format == 'R32_UINT'
    ):
        blend_elements.append(BufferElement({
            'Name':          'BLENDWEIGHTS',
            'SemanticName':  'BLENDWEIGHTS',
            'SemanticIndex': '0',
            'Format':        'R32_UINT',
            'ByteWidth': 4
        }))
        for vertex_i in range(len(blend)):
            blend[vertex_i] += ['1']

        terminal = State.get_instance().get_terminal()
        terminal.print('BENDINDICES has only 1 index (R32_UINT), and no BLENDWEIGHTS exist.')
        terminal.print('Manually inserted BLENDWEIGHTS = 1 for each vertex.')
        terminal.print()


def parse_buffer_file_name(file_name: str):
    draw_id, file_name = file_name.split('-', maxsplit=1)

    resource_pattern = re.compile(r'^(.*?)=?(!.!)?=(.*?)-')
    m = re.search(resource_pattern, file_name)
    if not m: raise Exception('Unexpected file name format ' + file_name)
    file_name = re.sub(resource_pattern, '', file_name)

    resource      = m.group(1)
    contamination = m.group(2)
    resource_hash = m.group(3)

    shaders = {}
    shader_pattern = re.compile(r'(.*?)=(.*?)[-\.]')
    for shader_match in shader_pattern.finditer(file_name):
        shaders[shader_match.group(1)] = shader_match.group(2)

    return draw_id, resource, resource_hash, contamination, shaders
