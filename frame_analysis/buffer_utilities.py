import re
from pathlib import Path

def extract_from_txt(key, filepath) -> int:
    if key not in ['vertex count', 'first index']:
        raise Exception('Unexpected key: {}'.format(key))
    
    # Scyll: readline() is **extremely** fast compared to readlines() with early loop break
    with open(filepath, "r") as f:
        pattern = re.compile(r'^{}: (\d+)$'.format(key))
        line = f.readline()
        while line:
            m = pattern.match(line)
            if m: return int(m.group(1))
            line = f.readline()

    return -1

# Generalized function to collect data from buffer .txt
# This is more annoying to parse when compared to the raw .buf files, but the benefit is that each line already
#   has the corresponding name for the line as the prefix
# Empty filters to collect everything that appears in data
def collect_buffer_data(filepath: Path, filters=()):
    result = []
    ignore_normals = False
    with open(filepath, "r") as f:
        headers, data = f.read().split("vertex-data:\n")
        element_format, garbage = parse_buffer_headers(headers, data, tuple(filters))
        group_size = len(element_format)

        # for element in element_format:
        #     print('\t\t'+'{:14} {:3} {}'.format(element['element_name'], element['bytewidth'], element['format']))

        filtered_data = []
        for d in data.split('\n'):
            element_name = d.split(':', maxsplit=1)[0].split(' ')[-1]
            if (
                not d
                or (filters and element_name not in filters)
                or (garbage and element_name in garbage)
            ): continue
            filtered_data.append(d.strip())

        data = filtered_data

        vertex_group = []
        for i in range(len(data)):
            vertex = data[i].split(":")[1].strip().split(", ")
            if ignore_normals and element_format[i%len(element_format)]["semantic_name"] == "NORMAL":
                vertex[-1] = "0"
            elif element_format[i%len(element_format)]["semantic_name"] == "NORMAL" and len(vertex) == 4 and not vertex[-1] == '0':
                print(vertex)
                print("\nERROR: Incorrect NORMAL identified")
                print("The program is mis-identifying some other component as NORMAL")
                print("Usually the best solution to this is to force the program to run on a different relevant id using --force")

                print("If you want to continue dumping the object like this anyway, type y (will have to recalculate normals in blender, and will likely run into issues with reimporting)")
                user_input = input()
                if user_input == "y":
                    ignore_normals = True
                    vertex[-1] = "0"
                else:
                    print("Exiting")
                    exit()

            # Scyll: ZZZ has -nan(ind) values for its texcoords
            vertex = [v if v != '-nan(ind)' else '0' for v in vertex]

            vertex_group.append(vertex)

            if (i + 1) % group_size == 0:
                result.append(vertex_group)
                vertex_group = []

    return result, element_format


# Parsing the headers for vb0 txt files
# Note that the data in the headers is not super reliable - the byteoffset is almost always wrong, and the header
#   can contain more information than is actually in the file
def parse_buffer_headers(headers, data, filters: set):
    results = []
    garbage_element_names = set()
    prev_aligned_byte_offset = -1

    # Scyll: Identify what elements are actually used in the data
    # using the first vertex alone instead of the searching through
    # all the data
    # TODO this is awful, find another way to shave off 0.05s :teriderp: 
    line = ''
    in_use_elements = set()
    for i in range(1, len(data)):
        if data[i] == ':':
            in_use_elements.add(line.split(' ')[-1])

        line += data[i]
        if data[i] == '\n':
            line = ''
            if data[i+1] == '\n':
                break
    
    # https://docs.microsoft.com/en-us/windows/win32/api/dxgiformat/ne-dxgiformat-dxgi_format
    for i, element in enumerate(headers.split("]:")[1:]):
        lines = [l.strip() for l in element.strip().splitlines()]
        name = lines[0].split(": ")[1]
        index = lines[1].split(': ')[1]
        aligned_byte_offset = int(lines[4].split(': ')[1])
        if index == '0': index = ''
        
        # A bit annoying, but names can be very similar so need to match filter format exactly
        element_name = name
        if index != "0":
            element_name += index

        if (
            element_name not in in_use_elements
            or (filters and element_name not in filters)
        ):
            continue

        # Scyll: Identify and refuse garbage!
        if prev_aligned_byte_offset >= aligned_byte_offset:
            # print('\t\tFound garbage', element_name, aligned_byte_offset)
            garbage_element_names.add(element_name)
            continue
        else:
            prev_aligned_byte_offset = aligned_byte_offset

        index = lines[1].split(": ")[1]
        data_format = lines[2].split(": ")[1]
        # This value does not make any sense, so skip - it is not actually the normal but something else
        # if name == "NORMAL" and data_format == "R8G8B8A8_UNORM":
        #     print("WARNING: unrecognized normal format, skipping collection")
        #     continue
        bytewidth = sum([int(x) for x in re.findall("([0-9]*)[^0-9]", data_format.split("_")[0]+"_") if x])//8

        results.append({"semantic_name": name, "element_name": element_name, "index": index, "format": data_format, "bytewidth": bytewidth})

    return results, garbage_element_names


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
def construct_combined_buffer(buffer_data, element_format):
    vb_merged = ""
    stride = 0
    for element in element_format:
        stride += element['bytewidth']
    vb_merged += f"stride: {stride}\n"
    vb_merged += f"first vertex: 0\nvertex count: {len(buffer_data)}\ntopology: trianglelist\n"

    element_offset, byte_offset = 0, 0
    byte_offsets, element_names = [], []
    for element in element_format:
        # Scyll: Prepare these 2 lists early to allow for direct retrieval in the next stage
        byte_offsets.append(f'{str(byte_offset).zfill(3)}')
        element_names.append(element["element_name"])

        vb_merged += f"element[{element_offset}]:\n  SemanticName: {element['semantic_name']}\n  SemanticIndex: {element['index']}\n  Format: {element['format']}\n  InputSlot: 0\n  AlignedByteOffset: {byte_offset}\n  InputSlotClass: per-vertex\n  InstanceDataStepRate: 0\n"
        element_offset += 1
        byte_offset += element['bytewidth']

    vb_merged += "\nvertex-data:\n\n"
    
    # Scyll: Extremely fast - avoid excessive string concatenation with +=
    vb_merged += '\n'.join([
        ''.join(
            f'vb0[{i}]+{byte_offsets[j]} {element_names[j]}: {", ".join(buffer_data[i][j])}\n'
            for j in range(len(element_format))
        ) for i in range(len(buffer_data))
    ])

    # Scyll: Equivalent to (Slow):
    # for i in range(len(buffer_data)):
    #     byte_offset = 0
    #     for j, element in enumerate(element_format):
    #         vb_merged += f'vb0[{i}]+{str(byte_offset).zfill(3)} {element["element_name"]}: {", ".join(buffer_data[i][j])}\n'
    #         byte_offset += element['bytewidth']
    #     vb_merged += "\n"

    return vb_merged[:-1]

def handle_no_weight_blend(blend, blend_format):
    if blend_format == [{'semantic_name': 'BLENDINDICES', 'element_name': 'BLENDINDICES', 'index': '0', 'format': 'R32_UINT', 'bytewidth': 4}]:
        blend_format.append({'semantic_name': 'BLENDWEIGHTS', 'element_name': 'BLENDWEIGHTS', 'index': '0', 'format': 'R32_UINT', 'bytewidth': 4})
        for vertex_i in range(len(blend)):
            blend[vertex_i] += ['1']

        print('\n\tBLENDINDICES has only 1 index (R32_UINT), and no BLENDWEIGHTS exist.')
        print('\tManually inserted BLENDWEIGHTS = 1 for each vertex.\n')


def parse_buffer_file_name(file_name: str):
    draw_id, file_name = file_name.split('-', maxsplit=1)

    resource_pattern = re.compile(r'^(.*?)(=!.!)?=(.*?)-')
    m = re.search(resource_pattern, file_name)
    if not m: raise Exception('Unexpected file name format ' + file_name)
    file_name = re.sub(resource_pattern, '', file_name)

    resource        = m.group(1)
    is_contaminated = m.group(2) is not None
    resource_hash   = m.group(3)

    shaders = {}
    shader_pattern = re.compile(r'(.*?)=(.*?)[-\.]')
    for shader_match in shader_pattern.finditer(file_name):
        shaders[shader_match.group(1)] = shader_match.group(2)

    return draw_id, resource, resource_hash, is_contaminated, shaders
