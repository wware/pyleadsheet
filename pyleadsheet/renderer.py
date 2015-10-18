import os
import shutil
import jinja2
import filecmp
import datetime
from .constants import MEASURE, BEAT, HALFBEAT

import logging
logger = logging.getLogger(__name__)


class HTMLRenderer(object):

    SONG_TEMPLATE = 'song.jinja2'
    INDEX_TEMPLATE = 'index.jinja2'

    def __init__(self, outputdir):
        logger.debug('initializing HTMLRenderer with outputdir: ' + outputdir)
        self.songs_data = {}
        self.outputdir = os.path.join(outputdir, 'html')
        self.timestamp = datetime.datetime.now()

    def _prepare_output_directory(self):
        if not os.path.exists(self.outputdir):
            logger.debug('creating outputdir')
            os.makedirs(self.outputdir)
        fromfile = os.path.join(os.path.dirname(__file__), 'templates', 'pyleadsheet.css')
        tofile = os.path.join(self.outputdir, 'pyleadsheet.css')
        if not os.path.exists(tofile) or not filecmp.cmp(fromfile, tofile):
            logger.info('copying base files into outputdir')
            shutil.copy(fromfile, tofile)

    def _convert_measures(self, progression_data):
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

    def _prepare_form_section_lyrics(self, form_section):
        if 'lyrics' not in form_section.keys():
            form_section['lyrics'] = form_section['lyrics_hint'] = ''
        else:
            lines = form_section['lyrics'].splitlines()
            form_section['lyrics'] = '<br />'.join(lines)
            form_section['lyrics_hint'] = (lines[0] if len(lines[0]) <= 50 else lines[0][0:50]) + '...'

    def load_song(self, song_data):
        for i in range(len(song_data['progressions'])):
            progression_name = song_data['progressions'][i].keys()[0]
            song_data['progressions'][i] = {
                'name': progression_name,
                'measures': self._convert_measures(song_data['progressions'][i][progression_name])
            }
        for form_section in song_data['form']:
            self._prepare_form_section_lyrics(form_section)
        self.songs_data[song_data['title']] = song_data

    def _get_output_filename(self, song_title):
        return song_title.lower().replace(' ', '_') + '.html'

    def _update_template_data(self, template_data):
        template_data.update({
            'timestamp': self.timestamp
        })

    def _render_template_to_file(self, template, outputfilename, template_data):
        self._prepare_output_directory()
        self._update_template_data(template_data)
        j2env = jinja2.Environment(loader=jinja2.PackageLoader('pyleadsheet', 'templates'))
        output = open(os.path.join(self.outputdir, outputfilename), 'w')
        output.write(j2env.get_template(template).render(**template_data))

    def render_song(self, song_title):
        logger.info('rendering song: ' + song_title)
        self._render_template_to_file(
            self.SONG_TEMPLATE,
            self._get_output_filename(song_title),
            {'song': self.songs_data[song_title]}
        )

    def render_index(self):
        logger.info('rendering index')
        songs_by_first_letter = {}
        current_letter = None
        for title in sorted(self.songs_data.keys()):
            if not current_letter or title[0].upper() > current_letter:
                current_letter = title[0].upper()
                songs_by_first_letter[current_letter] = []
            songs_by_first_letter[current_letter].append(
                {'title': title, 'filename': self._get_output_filename(title)}
            )
        self._render_template_to_file(
            self.INDEX_TEMPLATE,
            'index.html',
            {'songs_by_first_letter': songs_by_first_letter}
        )

    def render_book(self):
        logger.info('rendering HTML book')
        for song_title in self.songs_data.keys():
            self.render_song(song_title)
        self.render_index()
