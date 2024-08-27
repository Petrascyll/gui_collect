import re
from pathlib import Path
from io import TextIOWrapper


def read_header(buffer: TextIOWrapper):
    key_value_pattern = re.compile(r'^\s*(.*?): (.*)$')
    element_pattern   = re.compile(r'^element\[(\d+)\]:$')

    header: dict[str, str] = {
        # key: value,
        # ...
    }
    elements: list[dict[str, str]] = [
        # {
        #   key: value,
        #   ...
        # },
        # ...
    ]

    # with open(filepath, 'r') as f:
    while line := buffer.readline():
        if key_value_match := key_value_pattern.match(line):
            key, value = key_value_match.groups()
            header[key] = value

        elif element_pattern.match(line):

            element_data = {}
            pos  = buffer.tell()
            line = buffer.readline()
            while key_value_match := key_value_pattern.match(line):
                key, value = key_value_match.groups()
                element_data[key] = value
                pos  = buffer.tell()
                line = buffer.readline()
            buffer.seek(pos)

            elements.append(element_data)
        
        else:
            # vertex data starts at this position
            vertex_data_start_pos = buffer.tell()
            break

    return header, elements, vertex_data_start_pos


def read_active_element_names(buffer: TextIOWrapper, vertex_data_start_pos: int):
    key_pattern = re.compile(r'vb\d+\[(\d+)\]\+(\d+) (.*)')
    element_names = set()

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

        if element_name.startswith('TEXCOORD'):
            element_values = [
                v if v != '-nan(ind)' else '0'
                for v in value.strip().split(', ')
            ]

        # elif element_name == 'TANGENT':
        #     element_values = value.strip().split(', ')
        #     if element_values[-1] not in ['-1', '1']:
        #         print('WARNING: TANGENT has invalid data.')

        else:
            element_values = value.strip().split(', ')
        
        vertex_data.append(element_values)

    all_vertex_data.append(vertex_data)

    return all_vertex_data


def prepare_header_elements(elements, valid_element_names):
    filtered_elements = []
    for element in elements:
        element_name = element['SemanticName']
        if element['SemanticIndex'] != '0':
            element_name += element['SemanticIndex']
        
        if element_name not in valid_element_names:
            continue

        matches = re.findall(r'([0-9]+)', element['Format'].split("_", maxsplit=1)[0])
        byte_width = sum([int(x) for x in matches]) // 8

        element['Name']       = element_name
        element['ByteWidth'] = byte_width
    
        filtered_elements.append(element)

    return filtered_elements


def read_text_buffer(buffer_path: Path, filter_element_names: set = None):
    header, elements, vertex_data_start_pos = read_header(buffer_path)

    active_element_names = read_active_element_names(buffer_path, vertex_data_start_pos)
    if filter_element_names:
        valid_element_names = filter_element_names.intersection(active_element_names)
    else:
        valid_element_names = active_element_names

    vertex_data = read_vertex_data(buffer_path, vertex_data_start_pos, valid_element_names)
    assert(int(header['vertex count']) == len(vertex_data))

    elements = prepare_header_elements(elements, valid_element_names)
    assert(len(elements) == len(valid_element_names))

    return header, elements, vertex_data


def read_buffer_info(buffer_path: Path):
    with open(buffer_path, 'r') as buffer:
        header, header_elements, vertex_data_start_pos = read_header(buffer)
        active_element_names = read_active_element_names(buffer, vertex_data_start_pos)

    filtered_header_elements = prepare_header_elements(header_elements, active_element_names)
    real_stride = sum(element['ByteWidth'] for element in filtered_header_elements)

    return int(header['vertex count']), int(header['stride']), real_stride


def get_best_buffer_path(buffer_paths: list[Path]):
    prev_vertex_count = None

    for path in buffer_paths:
        vertex_count, header_stride, real_stride = read_buffer_info(path)

        assert(not prev_vertex_count or (vertex_count == prev_vertex_count))
        prev_vertex_count = vertex_count

        if real_stride == header_stride:
            return path
