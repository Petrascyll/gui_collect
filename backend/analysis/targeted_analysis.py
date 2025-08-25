from pathlib import Path


_filepath      = Path('include', 'auto_generated.ini')

def get_include_path():
    return _filepath

def get_status():
    exists = _filepath.exists()
    enabled = False
    if exists:
        text = _filepath.read_text()
        enabled = len(text) > 0
    return exists, enabled

def clear(terminal=None):
    _filepath      .write_text('', encoding='utf-8')

    if terminal:
        terminal.print(f'Cleared targeted ini content from <PATH>{_filepath.absolute()}</PATH>')

def generate(export_name, model_hashes, component_names, terminal, dump_rt = True, force_dump_dds = False, symlink = False, share_dupes = False):
    targeted_content = '\n\n'.join([
        '\n'.join([
            '[TextureOverrideModel{}]'.format(i+1),
            'hash = {}'               .format(model_hash),
            'match_priority = 0',
            'filter_index = 70111102111',
            '$model_{} = 1'           .format(i+1),
            'if vb0 > 0 && ib > 0',
            '    $modded_model_{} = 1'.format(i+1),
            'endif',
            '{}run = CommandListRT'.format('; ' if not dump_rt else ''),
            'run = CommandListModel',
            'run = CommandListTexture.jpg.dds' if not force_dump_dds else 'run = CommandListTexture.dds',
        ])
        for i, model_hash in enumerate(model_hashes)
    ])

    text_print_content = (
        f'[ResourceText.Model]\ntype = Buffer\ndata = "Targeted Analysis: {export_name}"\n\n'
        +'\n'.join([
            f'[ResourceText.Model{i+1}]\ntype = Buffer\ndata = "- {model_hash}  ({component_name})"\n'
            for i, (model_hash, component_name) in enumerate(zip(model_hashes, component_names))
        ])
        +'\n'
        +'\n'.join([
            f'[ResourceText.ModdedModel{i+1}]\ntype = Buffer\ndata = "- {model_hash}  ({component_name}) MOD ACTIVE"\n'
            for i, (model_hash, component_name) in enumerate(zip(model_hashes, component_names))
        ])
        +'\n'
        +'[ResourcePosParams.Model]\ntype = StructuredBuffer\narray = 1\ndata = R32_FLOAT  -0.99 -0.00 +1.00 +1.00  0.005 0.005  1 2  0\n\n'
        +'\n'.join([
            f'[ResourcePosParams.Model{i+1}]\ntype = StructuredBuffer\narray = 1\ndata = R32_FLOAT  -0.99 {-0.0785*(i+1)} +1.00 +1.00  0.005 0.005  1 2  0\n'
            for i in range(len(model_hashes))
        ])
        +'\n'
        +'[CommandListPrintModel]\n'
        +'Resource\\gui_collect\\internal\\Text          = ref ResourceText.Model\n'
        +'Resource\\gui_collect\\internal\\TextPosParams = ref ResourcePosParams.Model\n'
        +'Resource\\gui_collect\\internal\\TextParams    = ref ResourceColorParams.White\n'
        +'run = CommandList\\gui_collect\\internal\\PrintText\n'
        +'\n'
        +'\n'.join([
            '\n'.join([
                f'[CommandListPrintModel{i+1}]',
                f'Resource\\gui_collect\\internal\\TextPosParams  = ref ResourcePosParams.Model{i+1}',
                f'if $modded_model_{i+1}',
                f'    Resource\\gui_collect\\internal\\Text       = ref ResourceText.ModdedModel{i+1}',
                f'    Resource\\gui_collect\\internal\\TextParams = ref ResourceColorParams.YellowGreen',
                f'elif $model_{i+1}',
                f'    Resource\\gui_collect\\internal\\Text       = ref ResourceText.Model{i+1}',
                f'    Resource\\gui_collect\\internal\\TextParams = ref ResourceColorParams.Green',
                f'else',
                f'    Resource\\gui_collect\\internal\\Text       = ref ResourceText.Model{i+1}',
                f'    Resource\\gui_collect\\internal\\TextParams = ref ResourceColorParams.Red',
                f'endif',
                f'run = CommandList\\gui_collect\\internal\\PrintText',
                f''
            ])
            for i in range(len(model_hashes))
        ])
        +'\n'
        +'[Constants]\n'
        +''.join([f'global $model_{i+1} = 0\n' for i in range(len(model_hashes))])
        +''.join([f'global $modded_model_{i+1} = 0\n' for i in range(len(model_hashes))])
        +'\n'
        +'[Present]\n'
        +''.join([f'post $model_{i+1} = 0\n'            for i in range(len(model_hashes))])
        +''.join([f'post $modded_model_{i+1} = 0\n'            for i in range(len(model_hashes))])
        +'if hunting == 1\n'
        +'    run = CommandListPrintModel\n'
        +''.join([f'    run = CommandListPrintModel{i+1}\n' for i in range(len(model_hashes))])
        +'endif\n'
    )

    targeted = TARGETED
    if symlink or share_dupes:
        extra_options = '{}{}'.format(
            ' symlink'     if symlink     else '',
            ' share_dupes' if share_dupes else '',
        )

        targeted = '\n'.join([
            line
            if not line.startswith('analyse_options')
            else line + extra_options
            for line in TARGETED.splitlines()
        ] + [''])

    with open(_filepath, 'w') as f:
        f.write(targeted)
        f.write(targeted_content)
        f.write('\n\n')
        f.write(TEXT_PRINT)
        f.write(text_print_content)
        f.write('\n\n')
        f.write(';-------------FILE END--------------\n')


    terminal.print(f'Wrote targeted ini content to <PATH>{_filepath.absolute()}</PATH>')

TARGETED = '''
; AUTOGENERATED: DO NOT MANUALLY EDIT

[Includes]
include = ./Internal.ini

[Hunting]
hunting = 1
analyse_options = mono

[ShaderRegexEnableTargetedTextureOverrides]
shader_model = vs_4_0 vs_4_1 vs_5_0 vs_5_1
if !$costume_mods
    if vb0 == 70111102111
        checktextureoverride = vb0
    endif
    if ib == 70111102111
        checktextureoverride = ib
    endif
endif

;----------TARGET SHADERS-----------
[ShaderOverridePose]
; GI+HI Pose Shader One
hash = 653c63ba4a73ca8b
allow_duplicate_hash = overrule
analyse_options = dump_vb txt buf

[ShaderOverridePose1]
; ZZZ+SR Pose Shader One
hash = e8425f64cfb887cd
allow_duplicate_hash = overrule
analyse_options = dump_vb txt buf

[ShaderOverridePose2]
; ZZZ+SR Pose Shader Two
hash = a0b21a8e787c5a98
allow_duplicate_hash = overrule
analyse_options = dump_vb txt buf

[ShaderOverridePose3]
; ZZZ+SR Pose Shader Three
hash = 9684c4091fc9e35a
allow_duplicate_hash = overrule
analyse_options = dump_vb txt buf

[ShaderOverridePose4]
; HI3 part 2
hash = 10905ed856e6b621
allow_duplicate_hash = overrule
analyse_options = dump_vb txt buf

[ShaderOverridePose5]
; HI Pose Shader One
hash = 4123d77c48627b98
allow_duplicate_hash = overrule
analyse_options = dump_vb txt buf

[ShaderOverrideShapekey.CS_SK_ZZZ]
hash = 743108cc03f39cbf
allow_duplicate_hash = overrule
analyse_options = dump_rt dump_tex dump_cb buf txt

[ShaderOverride.HSR.CS.GodKnows]
hash = f72bbc44b525a73a
allow_duplicate_hash = overrule
analyse_options = dump_rt dump_tex dump_cb buf txt

[ShaderOverride.HSR.CS.Shapekey]
hash = 893b6d8f0a84ca0d
allow_duplicate_hash = overrule
analyse_options = dump_rt dump_tex dump_cb buf txt

[ShaderOverride.HSR.CS.SingleSK4VGs]
hash = fee307b98a965c16
allow_duplicate_hash = overrule
analyse_options = dump_rt dump_tex dump_cb buf txt

[ShaderOverride.HSR.CS.MultiNoSK4VGs]
hash = 1c932707d4d8df41
allow_duplicate_hash = overrule
analyse_options = dump_rt dump_tex dump_cb buf txt

[ShaderOverride.HSR.CS.MultiYesSK4VGs]
hash = d50694eedd2a8595
allow_duplicate_hash = overrule
analyse_options = dump_rt dump_tex dump_cb buf txt

[ShaderOverride.HSR.CS.Multi1VGs]
hash = 4d9c23fd387846c7
allow_duplicate_hash = overrule
analyse_options = dump_rt dump_tex dump_cb buf txt

[ShaderOverride.HSR.CS.Multi2VGs]
hash = c9f2b46571d22858
allow_duplicate_hash = overrule
analyse_options = dump_rt dump_tex dump_cb buf txt


;----------PRESET COMMANDS----------
[CommandListModel]
analyse_options = dump_ib dump_vb txt buf

[CommandListRT]
analyse_options = dump_rt

[CommandListTexture.jpg.dds]
analyse_options = dump_tex

[CommandListTexture.dds]
analyse_options = dump_tex dds

;------------TARGET MODEL----------
'''

TEXT_PRINT = '''
;-------------TEXT PRINT------------
[ResourceColorParams.White]
type = StructuredBuffer
array = 1
data = R32_FLOAT 1 1.00 1.00 1   0 0 0 0.8   1.0

[ResourceColorParams.Green]
type = StructuredBuffer
array = 1
data = R32_FLOAT 0 1.00 0.00 1   0 0 0 0.8   1.0

[ResourceColorParams.Red]
type = StructuredBuffer
array = 1
data = R32_FLOAT 1.00 0 0.00 1   0 0 0 0.8   1.0

[ResourceColorParams.YellowGreen]
type = StructuredBuffer
array = 1
data = R32_FLOAT 0.80 1 0.00 1   0 0 0 0.8   1.0

'''
