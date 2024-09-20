import re
from pathlib import Path
from io import TextIOWrapper

from .structs import BufferElement
from .exceptions import InvalidTextBufferException


from frontend.state import State


def read_header(buffer: TextIOWrapper):
    key_value_pattern = re.compile(r'^\s*(.*?): (.*)$')
    element_pattern   = re.compile(r'^element\[(\d+)\]:$')

    header  : dict[str, str]      = {}
    elements: list[BufferElement] = []

    while line := buffer.readline():
        if key_value_match := key_value_pattern.match(line):
            key, value = key_value_match.groups()
            header[key] = value

        elif element_pattern.match(line):

            data = {}
            pos  = buffer.tell()
            line = buffer.readline()
            while key_value_match := key_value_pattern.match(line):
                key, value = key_value_match.groups()
                data[key] = value
                pos  = buffer.tell()
                line = buffer.readline()
            buffer.seek(pos)
            
            elements.append(BufferElement(data))
        
        else:
            # vertex data starts at this position
            vertex_data_start_pos = buffer.tell()
            break
    else:
        # if we read all the lines without breaking then the .txt
        # has only a header with no vertex data
        return header, elements, -1

    return header, elements, vertex_data_start_pos


def read_active_element_names(buffer: TextIOWrapper, vertex_data_start_pos: int):
    key_pattern = re.compile(r'vb\d+\[(\d+)\]\+(\d+) (.*)')
    element_names = set()

    if vertex_data_start_pos < 0:
        return element_names

    buffer.seek(vertex_data_start_pos)
    buffer.readline()
    buffer.readline()

    prev_byte_offset  = -1
    while line := buffer.readline():
        if len(line.strip()) == 0: break

        key_match = key_pattern.match(line.split(':')[0])
        byte_offset  = int(key_match.group(2))
        if prev_byte_offset >= byte_offset:
            continue

        element_name = key_match.group(3)
        element_names.add(element_name)
        prev_byte_offset = byte_offset
    
    return element_names


def read_vertex_data(buffer: TextIOWrapper, vertex_data_start_pos: int, valid_element_names: set):
    all_vertex_data = []

    if vertex_data_start_pos < 0:
        return all_vertex_data

    buffer.seek(vertex_data_start_pos)
    buffer.readline()
    buffer.readline()

    vertex_data = []
    while line := buffer.readline():
        if len(line.strip()) == 0:
            all_vertex_data.append(vertex_data)
            vertex_data = []
            continue

        key, value = line.split(':')

        element_name = key.split(' ')[1]
        if element_name not in valid_element_names:
            continue

        element_values = value.strip().split(', ')
        if element_name.startswith('TEXCOORD'):
            element_values = [v if v != '-nan(ind)' else '0' for v in element_values]

        elif element_name == 'TANGENT':
            if element_values[-1] not in ['-1', '1']:
                State.get_instance().get_terminal().print('<WARNING>WARNING: TANGENT has invalid data.</WARNING>')
        
        vertex_data.append(element_values)

    all_vertex_data.append(vertex_data)

    return all_vertex_data


def get_clean_buffer_elements(buffer_elements: list[BufferElement], valid_element_names):
    byte_offset = 0
    filtered_elements: list[BufferElement] = []

    for element in buffer_elements:
        element_name = element.SemanticName
        if element.SemanticIndex != '0':
            element_name += element.SemanticIndex
        
        if element_name not in valid_element_names:
            continue

        matches = re.findall(r'([0-9]+)', element.Format.split("_", maxsplit=1)[0])

        element.Name              = element_name
        # TODO remove
        element.ByteWidth         = sum([int(x) for x in matches]) // 8
        element.AlignedByteOffset = byte_offset

        byte_offset += element.ByteWidth

        filtered_elements.append(element)

    return filtered_elements


def collect_text_buffer_data(buffer_path: Path, filter_element_names: set = None):
    with open(buffer_path, 'r') as buffer:
        header, buffer_elements, vertex_data_start_pos = read_header(buffer)
        active_element_names = read_active_element_names(buffer, vertex_data_start_pos)
        valid_element_names  = (
            filter_element_names.intersection(active_element_names)
            if filter_element_names else active_element_names
        )
        buffer_elements = get_clean_buffer_elements(buffer_elements, valid_element_names)
        assert(len(buffer_elements) == len(valid_element_names))

        vertex_data = read_vertex_data(buffer, vertex_data_start_pos, valid_element_names)
        assert(int(header['vertex count']) == len(vertex_data))

    return header, buffer_elements, vertex_data


def read_clean_header(buffer_path: Path):
    with open(buffer_path, 'r') as buffer:
        header, buffer_elements, vertex_data_start_pos = read_header(buffer)
        active_element_names = read_active_element_names(buffer, vertex_data_start_pos)
        buffer_elements = get_clean_buffer_elements(buffer_elements, active_element_names)
        assert(len(buffer_elements) == len(active_element_names))

    return header, buffer_elements


def get_buffer_elements(buffer_paths: list[Path]):
    min_trash_buffer_elements = None
    max_expressed_stride      = -1
    buffer_stride             = -1

    for buffer_path in buffer_paths:
        header, buffer_elements = read_clean_header(buffer_path)

        if int(header['stride']) == 0:
            continue

        expressed_stride = sum(element.ByteWidth for element in buffer_elements)
        buffer_stride    = int(header['stride'])

        if buffer_stride == expressed_stride:
            return buffer_stride, buffer_elements

        if expressed_stride > max_expressed_stride:
            min_trash_buffer_elements = buffer_elements
            max_expressed_stride      = expressed_stride

    if buffer_stride == -1:
        State.get_instance().get_terminal().print('<ERROR>ERROR: Failed to find any valid buffer format.</ERROR>')
        raise InvalidTextBufferException

    State.get_instance().get_terminal().print(
        f'<WARNING>WARNING: Failed to find ideal buffer format. '
        f'Buffer </WARNING><PATH>{buffer_paths[0].with_suffix(".buf").name}"</PATH><WARNING> has stride = {buffer_stride}, '
        f'but only {max_expressed_stride} bytes out of those {buffer_stride} can be extracted.</WARNING>'
    )
    return buffer_stride, min_trash_buffer_elements


def extract_from_txt(key, filepath) -> int:
    if key not in ['vertex count', 'first index']:
        raise Exception('Unexpected key: {}'.format(key))
    
    # Scyll: readline() is **extremely** fast compared to readlines() with early loop break
    with open(filepath, "r") as f:
        pattern = re.compile(r'^{}: (\d+)$'.format(key))
        i = 0
        line = f.readline()
        while line:
            m = pattern.match(line)
            if m: return int(m.group(1))
            if i >= 6: break
            line = f.readline()
            i += 1

    return -1
