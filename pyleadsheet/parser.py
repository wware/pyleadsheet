import os
import yaml
import funcy
from .constants import MEASURE, BEAT, HALFBEAT

# def _parse_tag(pls_line, close_char, cursor):
#     last_col = pls_line[cursor[1]:].find(close_char)
#     if last_col == -1:
#         raise ValueError('expected "{0}", found {1} ({2},{3})'.format(
#             close_char, pls_line[-1], cursor[0], len(pls_line))
#         )
#     return pls_line[cursor[1] + 1:last_col].split(':'), last_col


# def parse(pls_string):
#     pls_data = {
#         'sections': {},
#         'form'
#     }
#     pls_raw = pls_string.splitlines()
#     current_section = ''
#     for row in range(len(pls_raw)):
#         pls_line = pls_raw[row]
#         for col in range(len(pls_line)):
#             cursor = (row, col)
#             pls_char = pls_raw[row][col]
#             # print ','.join((str(row), str(col))), pls_char
#             # start of a directive
#             if pls_char == '{':
#                 directive, col = _parse_tag(pls_line, '}', cursor)
#                 if directive[0] == 'section':
#                     current_section = directive[1]
#             # start of a chord
#             elif pls_char == '[':
#                 chord, col = _parse_tag(pls_line, ']', cursor)

#             # start of a form section
#             elif pls_char == '<':
#                 section, col = _parse_tag(pls_line, '>', cursor)


def _parse_progression(progression_str):
    items = funcy.re_all(r'\[([^\]]+)\]', progression_str)
    ret = []
    for item in items:
        tokens = item.split(':')
        ret.append({'chord': tokens[0], 'duration': []})
        if len(tokens) == 1:
            ret[-1]['duration'].append({'number': 1, 'unit': MEASURE})
        else:
            for number, unit in funcy.re_all(r'([\d\.]+)([{0}{1}{2}])'.format(MEASURE, BEAT, HALFBEAT), tokens[1]):
                ret[-1]['duration'].append({'number': int(number), 'unit': unit})
    return ret


def parse(yaml_str):
    pls_data = yaml.load(yaml_str)
    for i in range(len(pls_data['progressions'])):
        progression_name = pls_data['progressions'][i].keys()[0]
        pls_data['progressions'][i][progression_name] = _parse_progression(
            pls_data['progressions'][i][progression_name]
        )
    return pls_data


def parse_file(filepath):
    if not os.path.isfile(filepath):
        raise IOError('could not find any file at {0}'.format(filepath))
    contents = open(filepath, 'r').read()
    return parse(contents)
