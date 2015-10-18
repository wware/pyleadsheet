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


def _get_output_filename(song_title):
    return song_title.lower().replace(' ', '_') + '.html'


@funcy.memoize
def _get_timestamp():
    return datetime.datetime.now()


def _update_template_data(template_data):
    template_data.update({
        'timestamp': _get_timestamp()
    })


def _render_template_to_file(template, outputfile, template_data):
    _update_template_data(template_data)
    j2env = jinja2.Environment(loader=jinja2.PackageLoader('pyleadsheet', 'templates'))
    output = open(outputfile, 'w')
    output.write(j2env.get_template(template).render(**template_data))


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
    outputfile = os.path.join(outputdir, _get_output_filename(song_data['title']))
    _render_template_to_file('song.jinja2', outputfile, {'song': song_data})


def render_index(song_titles, outputdir):
    _prepare_output_directory(outputdir)
    songs_by_first_letter = {}
    current_letter = None
    for title in sorted(song_titles):
        if not current_letter or title[0].upper() > current_letter:
            current_letter = title[0].upper()
            songs_by_first_letter[current_letter] = []
        songs_by_first_letter[current_letter].append({'title': title, 'filename': _get_output_filename(title)})
    outputfile = os.path.join(outputdir, 'index.html')
    _render_template_to_file('index.jinja2', outputfile, {'songs_by_first_letter': songs_by_first_letter})

