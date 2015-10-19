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

    FILENAME_SUFFIX_COMBINED = 'combined'
    FILENAME_SUFFIX_NO_LYRICS = 'nolyrics'
    FILENAME_SUFFIX_LYRICS_ONLY = 'lyrics'

    MODES = {
        'no_lyrics': {'filename_suffix': 'nolyrics', 'display_name': 'Lead Sheet', 'display_order': 1},
        'lyrics_only': {'filename_suffix': 'lyrics', 'display_name': 'Lyrics', 'display_order': 2},
        'combined': {'filename_suffix': 'combined', 'display_name': 'Combined', 'display_order': 3},
    }

    def __init__(self, outputdir, combined=False, no_lyrics=False, lyrics_only=False):
        logger.debug('initializing HTMLRenderer with outputdir: ' + outputdir)
        self.songs_data = {}
        self.outputdir = os.path.join(outputdir, 'html')
        self.mode_flags = {'combined': combined, 'no_lyrics': no_lyrics, 'lyrics_only': lyrics_only}
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

    def _get_output_filename(self, song_title, suffix=None):
        ret = song_title.lower().replace(' ', '_')
        ret += '_' + suffix if suffix else ''
        return ret + '.html'

    def _update_template_data(self, template_data):
        template_data.update({
            'timestamp': self.timestamp,
            'modes': self.MODES,
            'mode_keys': sorted(self.MODES.keys(), key=lambda(k): self.MODES[k]['display_order']),
            'mode_flags': self.mode_flags
        })

    def _render_template_to_file(self, template, outputfilename, template_data):
        self._prepare_output_directory()
        self._update_template_data(template_data)
        j2env = jinja2.Environment(loader=jinja2.PackageLoader('pyleadsheet', 'templates'))
        output = open(os.path.join(self.outputdir, outputfilename), 'w')
        output.write(j2env.get_template(template).render(**template_data))

    def render_song(self, song_title):
        logger.info('rendering song: ' + song_title)
        if self.mode_flags['combined']:
            self._render_template_to_file(
                self.SONG_TEMPLATE,
                self._get_output_filename(song_title, self.MODES['combined']['filename_suffix']),
                {'song': self.songs_data[song_title], 'render_leadsheet': True, 'render_lyrics': True}
            )
        if self.mode_flags['no_lyrics']:
            self._render_template_to_file(
                self.SONG_TEMPLATE,
                self._get_output_filename(song_title, self.FILENAME_SUFFIX_NO_LYRICS),
                {'song': self.songs_data[song_title], 'render_leadsheet': True, 'render_lyrics': False}
            )
        if self.mode_flags['lyrics_only']:
            self._render_template_to_file(
                self.SONG_TEMPLATE,
                self._get_output_filename(song_title, self.FILENAME_SUFFIX_LYRICS_ONLY),
                {'song': self.songs_data[song_title], 'render_leadsheet': False, 'render_lyrics': True}
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
                {'title': title, 'filenames': {}}
            )
            for mode in self.MODES.keys():
                songs_by_first_letter[current_letter][-1]['filenames'][mode] = \
                        self._get_output_filename(title, self.MODES[mode]['filename_suffix'])
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
