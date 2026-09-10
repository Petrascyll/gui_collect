import logging
import re
from pathlib import Path

from .buffer_decoder import get_encoder
from .structs import BufferElement

logger = logging.getLogger(__name__)


def merge_buffers(buffers, buffer_formats: list[list[BufferElement]]):
    merged_data, merged_format = _merge_buffer_data(buffers, buffer_formats)
    return construct_combined_buffer(merged_data, merged_format)


def merge_buffers_binary(buffers, buffer_formats: list[list[BufferElement]]):
    merged_data, merged_format = _merge_buffer_data(buffers, buffer_formats)
    return (
        construct_combined_buffer_header(merged_data, merged_format),
        construct_combined_buffer_binary(merged_data, merged_format),
    )


def _merge_buffer_data(buffers, buffer_formats: list[list[BufferElement]]):
    vertex_counts = [len(buffer) for buffer in buffers]
    if len(set(vertex_counts)) != 1:
        raise Exception(f"Buffer vertex count mismatch: {vertex_counts}")

    vertex_count = vertex_counts[0]
    merged_data = []
    for j in range(vertex_count):
        temp = []
        for buffer in buffers:
            temp.extend(buffer[j])
        merged_data.append(temp)

    merged_format = []
    for buffer_format in buffer_formats:
        merged_format.extend(buffer_format)

    return merged_data, merged_format


def construct_combined_buffer_header(buffer_data, buffer_elements: list[BufferElement]):
    stride = sum([element.ByteWidth for element in buffer_elements])

    vb_merged = "\n".join([
        "stride: {}".format(stride),
        "first vertex: 0",
        "vertex count: {}".format(len(buffer_data)),
        "topology: trianglelist",
        "",
    ])

    byte_offset = 0
    for i, element in enumerate(buffer_elements):
        vb_merged += "\n".join([
            f"element[{i}]:",
            f"  SemanticName: {element.SemanticName}",
            f"  SemanticIndex: {element.SemanticIndex}",
            f"  Format: {element.Format}",
            f"  InputSlot: 0",
            f"  AlignedByteOffset: {byte_offset}",
            f"  InputSlotClass: per-vertex",
            f"  InstanceDataStepRate: 0",
            "",
        ])
        byte_offset += element.ByteWidth

        logger.info(
            f"{element.Name:12} - {element.ByteWidth:2} - {element.Format}",
            extra={"TIMESTAMP": False},
        )

    logger.info(f"Total Stride: %s\n", stride, extra={"TIMESTAMP": False})

    return vb_merged


def construct_combined_buffer_binary(
    buffer_data, buffer_elements: list[BufferElement]
):
    encoders = [get_encoder(element.Format) for element in buffer_elements]

    return b"".join([
        b"".join([
            encoder(vertex_data[j]) for j, encoder in enumerate(encoders)
        ])
        for vertex_data in buffer_data
    ])


def construct_combined_buffer(buffer_data, buffer_elements: list[BufferElement]):

    vb_merged = construct_combined_buffer_header(buffer_data, buffer_elements)

    byte_offset = 0
    byte_offsets, element_names = [], []
    for element in buffer_elements:
        byte_offsets.append(f"{str(byte_offset).zfill(3)}")
        element_names.append(element.Name)
        byte_offset += element.ByteWidth

    vb_merged += "\nvertex-data:\n\n"

    # Scyll: Extremely fast - avoid excessive string concatenation with +=
    vb_merged += "\n".join([
        "".join([
            f"vb0[{i}]+{byte_offsets[j]} {element_names[j]}: {', '.join(map(str, buffer_data[i][j]))}\n"
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


# Fallback for frame analysis dumps which are missing the ib .buf file:
# repacks the index data of the ib .txt into its binary representation.
def construct_ib_binary(ib_path: Path, index_data_start_pos: int, dxgi_format: str):
    if index_data_start_pos < 0:
        raise Exception(f"{ib_path.name} has no index data")
    if not dxgi_format:
        raise Exception(f"{ib_path.name} has no index format")

    encoder = get_encoder(dxgi_format.removeprefix("DXGI_FORMAT_"))

    with open(ib_path, "r") as ib:
        ib.seek(index_data_start_pos)
        return b"".join([
            encoder((int(index),)) for line in ib for index in line.split()
        ])


def handle_no_weight_blend(blend, blend_elements: list[BufferElement]):
    if (
        len(blend_elements) == 1
        and blend_elements[0].Name == "BLENDINDICES"
        and blend_elements[0].Format == "R32_UINT"
    ):
        logger.info(
            "BENDINDICES has only 1 index (R32_UINT), and no BLENDWEIGHTS exist."
        )
        logger.info("Manually inserted BLENDWEIGHTS = 1 for each vertex.")
        logger.info("")

        blend = [blend[vertex_idx] + ["1"] for vertex_idx in range(len(blend))]

        blend_elements = [
            *blend_elements,
            BufferElement({
                "Name": "BLENDWEIGHTS",
                "SemanticName": "BLENDWEIGHTS",
                "SemanticIndex": "0",
                "Format": "R32_UINT",
                "ByteWidth": 4,
            }),
        ]

    return blend, blend_elements


def parse_buffer_file_name(file_name: str):
    draw_id, file_name = file_name.split("-", maxsplit=1)

    resource_pattern = re.compile(r"^(.*?)=?(!.!)?=(.*?)-")
    m = re.search(resource_pattern, file_name)
    if not m:
        raise Exception("Unexpected file name format " + file_name)
    file_name = re.sub(resource_pattern, "", file_name)

    resource = m.group(1)
    contamination = m.group(2)
    resource_hash = m.group(3)

    shaders = {}
    shader_pattern = re.compile(r"(.*?)=(.*?)[-\.]")
    for shader_match in shader_pattern.finditer(file_name):
        shaders[shader_match.group(1)] = shader_match.group(2)

    return draw_id, resource, resource_hash, contamination, shaders
