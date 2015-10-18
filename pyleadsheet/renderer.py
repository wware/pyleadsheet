import os
import shutil
import jinja2
import funcy
import datetime
from .constants import MEASURE, BEAT, HALFBEAT


def _prepare_output_directory(outputdir):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
        shutil.copy(
            os.path.join(os.path.dirname(__file__), 'templates', 'pyleadsheet.css'),
            os.path.join(outputdir, 'pyleadsheet.css')
        )


def _convert_measures(progression_data):
    # for now, all measures are divided into 8 discrete buckets
    multipliers = {MEASURE: 8, BEAT: 2, HALFBEAT: 1}
    measures = []
    cur = 0
    for datum in progression_data:
        subdivisions = 0
        for duration_part in datum['duration']:
            subdivisions += duration_part['number'] * multipliers[duration_part['unit']]
        for i in range(subdivisions):
            if cur % 8 == 0:
                measures.append([datum['chord']])
            elif i == 0:
                measures[-1].append(datum['chord'])
            else:
                measures[-1].append('')
            cur += 1
    return measures


def _prepare_form_section_lyrics(form_section):
    if 'lyrics' not in form_section.keys():
        form_section['lyrics'] = form_section['lyrics_hint'] = ''
    else:
        lines = form_section['lyrics'].splitlines()
        form_section['lyrics'] = '<br />'.join(lines)
        form_section['lyrics_hint'] = (lines[0] if len(lines[0]) <= 50 else lines[0][0:50]) + '...'


def _get_output_filename(song_data):
    return song_data['title'].lower().replace(' ', '_') + '.html'


def render_song(song_data, outputdir):
    _prepare_output_directory(outputdir)
    for i in range(len(song_data['progressions'])):
        progression_name = song_data['progressions'][i].keys()[0]
        song_data['progressions'][i] = {
            'name': progression_name,
            'measures': _convert_measures(song_data['progressions'][i][progression_name])
        }
    for form_section in song_data['form']:
        _prepare_form_section_lyrics(form_section)
    template_data = {
        'song': song_data,
        'timestamp': datetime.datetime.now()
    }
    j2env = jinja2.Environment(loader=jinja2.PackageLoader('pyleadsheet', 'templates'))
    output = open(os.path.join(outputdir, _get_output_filename(song_data)), 'w')
    output.write(j2env.get_template('base.jinja2').render(**template_data))
