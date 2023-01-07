# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

import simplemedia
from future.utils import iteritems

from .utilities import Utilities
from .utilities import plugin

__all__ = ['MainMenuItem', 'ItemInfo', 'PostInfo', 'SeasonInfo', 'VideoInfo', 'EmptyListItem', 'ListItem', 'FilterItem']

addon = simplemedia.Addon()
_ = addon.initialize_gettext()


class ItemInfo(simplemedia.VideoInfo):
    _path = None
    _trailer = None
    _mediatype = None
    _post_info = None
    post_id = 0  # type: int
    content_name = ''  # type: str

    def __init__(self, item_info, for_play=False, atl_names=False):
        self._item_info = item_info

        self._for_play = for_play
        self._atl_names = atl_names and not for_play

        self.post_id = item_info['id']
        self.content_name = '{0}-{1}'.format(item_info['id'], item_info['alt_name'])

    @property
    def date(self):
        if self.mediatype in ['movie', 'tvshow']:
            date_atom = self._item_info['date_atom']
            return '.'.join([date_atom[8:10], date_atom[5:7], date_atom[0:4]])

    @property
    def genre(self):
        return self._item_info['categories']

    @property
    def country(self):
        return self._item_info['countries']

    @property
    def year(self):
        if self.mediatype in ['movie', 'tvshow']:
            year = self._item_info['year']
            if year:
                return int(year)

    @property
    def episode(self):
        if self.mediatype in ['tvshow']:
            return 0

    @property
    def season(self):
        if self.mediatype in ['tvshow', 'season']:
            return 1

    @property
    def cast(self):
        actors = self._item_info['actors']
        if isinstance(actors, list):
            return actors
        elif isinstance(actors, dict):
            cast = []
            for key, val in iteritems(actors):
                cast.append(val)
            return cast

    @property
    def title(self):
        if self._atl_names:
            title = self._atl_title()
        else:
            title = self._title()
        return title

    @property
    def original_title(self):
        if self.mediatype in ['tvshow', 'movie']:
            if self._item_info['original_title']:
                title = self._item_info['original_title']
            else:
                title = self._item_info['title']

            return title

    @property
    def tvshowtitle(self):
        if self.mediatype in ['tvshow', 'season', 'episode']:
            if self._item_info['title']:
                return self._item_info['title']

    @property
    def status(self):
        if self.mediatype == 'tvshow':
            serial_stats = self._item_info.get('serial_stats')
            if serial_stats is not None:
                return serial_stats['comment']

    @property
    def path(self):
        return self._path

    @property
    def trailer(self):
        return self._trailer

    @property
    def dateadded(self):
        if self.mediatype in ['movie', 'tvshow']:
            date_atom = self._item_info['date_atom']
            return '{0} {1}'.format(date_atom[0:10], date_atom[11:19])

    @property
    def mediatype(self):
        _mediatype = self._mediatype
        if _mediatype is None:
            if Utilities.is_movie(self._item_info):
                _mediatype = 'movie'
            else:
                _mediatype = 'tvshow'

            self._mediatype = _mediatype

        return self._mediatype

    def _title(self):
        if self._item_info['quality'] \
                and not self._for_play:
            title = '{0} [{1}]'.format(self._item_info['title'], self._item_info['quality'])
        else:
            title = self._item_info['title']
        return title

    def _atl_title(self):

        title_parts = []
        if self.mediatype == 'movie':
            title_parts.append(self.original_title)
            if self.year is not None:
                title_parts.append('({0})'.format(self.year))

        elif self.mediatype == 'episode':
            if self._item_info['original_title']:
                title = self._item_info['original_title']
            else:
                title = self._item_info['title']
            title_parts.append(title)
            title_parts.append('s%02de%02d' % (self.season, self.episode))
        else:
            title_parts.append(self._title())

        return '.'.join(title_parts)

    def get_poster(self):
        return self._item_info['poster'].replace('thumbs/w220', 'orig')

    @staticmethod
    def get_thumb():
        return None

    def get_fanart(self):
        return self.get_thumb()

    def set_path(self, path):
        self._path = path

    def set_trailer(self, trailer):
        self._trailer = trailer

    @property
    def item_info(self):
        return self._item_info

    @property
    def for_play(self):
        return self._for_play

    def get_section(self):
        section_id = self._item_info['section']
        if section_id in [0, 999]:
            section = 'movies'
        elif section_id == 7:
            section = 'serials'
        elif section_id == 14:
            section = 'multfilms'
        elif section_id == 93:
            section = 'multserials'
        else:
            section = 'none'
        return section


class PostInfo(ItemInfo):

    def __init__(self, item_info):
        super(PostInfo, self).__init__(item_info, False, False)

    @property
    def plot(self):
        return addon.remove_html(self._item_info['short_story'])

    @property
    def director(self):
        if isinstance(self._item_info['directors'], dict):
            directors = []
            for key, val in iteritems(self._item_info['directors']):
                directors.append(val)
        else:
            directors = self._item_info['directors']
        return directors

    @property
    def episode(self):
        if self.mediatype == 'tvshow':
            total_episodes = 0
            playlist = self._item_info['player_links']['playlist']
            if isinstance(playlist, dict):
                for season, season_translations in iteritems(playlist):
                    episode = 0
                    for translation, episodes in iteritems(season_translations):
                        episode = max(episode, len(episodes))
                    total_episodes += episode

            return total_episodes

    @property
    def season(self):
        if self.mediatype == 'tvshow':
            playlist = self._item_info['player_links']['playlist']
            return len(playlist)

    def _title(self):
        if self._item_info['rip']:
            title = '{0} [{1}]'.format(self._item_info['title'], self._item_info['rip'])
        else:
            title = self._item_info['title']
        return title


class SeasonInfo(ItemInfo):
    _season = None
    _episodes = None
    _translation = None

    def __init__(self, item_info):
        super(SeasonInfo, self).__init__(item_info, False, False)

        self._mediatype = 'season'

    @property
    def plot(self):
        return addon.remove_html(self._item_info['short_story'])

    @property
    def director(self):
        if isinstance(self._item_info['directors'], dict):
            directors = []
            for key, val in iteritems(self._item_info['directors']):
                directors.append(val)
        else:
            directors = self._item_info['directors']
        return directors

    @property
    def episode(self):
        return self._episodes

    @property
    def season(self):
        return max(1, int(self._season))

    @property
    def title(self):
        return '{0} {1}'.format(_('Season'), self._season)

    def get_translation(self):
        return self._translation

    def get_season(self):
        return self._season

    def set_season_info(self, translation, season, episodes):
        self._translation = translation
        self._season = season
        self._episodes = episodes


class VideoInfo(ItemInfo):
    _episode = None
    _season = None
    _translation = None

    def __init__(self, item_info, for_play=False, atl_names=False):
        super(VideoInfo, self).__init__(item_info, for_play, atl_names)

    @property
    def episode(self):
        if self.mediatype == 'episode':
            return int(self._episode)

    @property
    def season(self):
        if self.mediatype == 'episode'\
                and self._season is not None:
            return max(1, int(self._season))

    @property
    def originaltitle(self):
        if self.mediatype == 'episode':
            return self.title
        else:
            return super(VideoInfo, self).originaltitle

    @property
    def duration(self):
        return self._item_info['duration'] * 60

    @property
    def mediatype(self):
        _mediatype = self._mediatype
        if _mediatype is None:
            _mediatype = super(VideoInfo, self).mediatype
            if _mediatype == 'tvshow':
                _mediatype = 'episode'

            self._mediatype = _mediatype

        return self._mediatype

    def _title(self):
        if self.mediatype == 'episode':
            title = '{0} {1}'.format(_('Episode'), self.episode)
        else:
            title = super(VideoInfo, self)._title()

        return title

    def set_episode_info(self, season, episode, translation):
        self._season = season
        self._episode = episode
        self._translation = translation

    def get_translation(self):
        return self._translation

    def get_season(self):
        return self._season

    def get_episode(self):
        return self._episode


class EmptyListItem(simplemedia.ListItemInfo):
    _url = None
    _path = None
    _info = None

    @property
    def path(self):
        return self._path

    @property
    def url(self):
        return self._url

    def set_url(self, url):
        self._url = url

    def set_path(self, path):
        self._path = path


class ListItem(EmptyListItem):
    _properties = None
    _context_menu = None

    def __init__(self, video_info):

        self._info = video_info

        self._item_info = video_info.item_info
        self._mediatype = video_info.mediatype
        self._for_play = video_info.for_play

        self.post_id = video_info.post_id

    @property
    def label(self):
        return self._info.title

    @property
    def path(self):
        return self._path

    @property
    def is_folder(self):
        if isinstance(self._info, VideoInfo):
            return False
        else:
            return self._mediatype in ['season', 'tvshow']

    @property
    def is_playable(self):
        if isinstance(self._info, VideoInfo):
            return True
        else:
            return self._mediatype in ['movie', 'episode']

    @property
    def art(self):
        art = {}

        if self._mediatype in ['season', 'episode']:
            art['tvshow.poster'] = self._info.get_poster()
        elif self._mediatype in ['tvshow', 'movie']:
            art['poster'] = self._info.get_poster()

        return art

    @property
    def thumb(self):
        if self._mediatype in ['movie', 'tvshow', 'season']:
            return self._info.get_poster()
        elif self._mediatype in ['episode']:
            return self._info.get_thumb()

    @property
    def fanart(self):
        return self._info.get_fanart()

    @property
    def info(self):
        return {'video': self._info.get_info()}

    @property
    def context_menu(self):
        return self._context_menu

    @property
    def properties(self):
        properties = {}

        if isinstance(self._properties, dict):
            properties.update(self._properties)

        if self._mediatype == 'season':
            properties['TotalSeasons'] = '{0}'.format(self._info.season)
            properties['TotalEpisodes'] = '{0}'.format(self._info.episode)
            properties['WatchedEpisodes'] = '0'
            properties['UnWatchedEpisodes'] = '{0}'.format(self._info.episode)
            properties['NumEpisodes'] = '{0}'.format(self._info.episode)

        return properties

    @property
    def season(self):
        if self._mediatype in ['season', 'episode'] \
                and self._info.season is not None:
            return {'number': self._info.season}

    @property
    def ratings(self):
        if self._mediatype in ['movie', 'tvshow']:
            default_source = self._get_rating_source()
            items = []
            for rating in self._rating_sources():
                rating_item = self._make_rating(self._item_info, **rating)
                rating_item['defaultt'] = (rating_item['type'] == default_source)
                items.append(rating_item)
            return items

    @staticmethod
    def _get_rating_source():
        rating_source = addon.get_setting('video_rating')
        if rating_source == 0:
            return 'imdb'
        elif rating_source == 1:
            return 'kinopoisk'

    @staticmethod
    def _rating_sources():
        yield {'rating_source': 'kinopoisk',
               'field': 'kp',
               }
        yield {'rating_source': 'imdb',
               'field': 'imdb',
               }

    @staticmethod
    def _make_rating(item, rating_source, field):
        rating_field = '_'.join([field, 'rating'])
        rating = item.get(rating_field, '0')
        if rating \
                and rating != '-':
            rating = float(rating)
        else:
            rating = 0

        votes_field = '_'.join([field, 'votes'])
        votes = item.get(votes_field, '0')
        if votes \
                and votes != '-':
            votes = int(votes)
        else:
            votes = 0

        return {'type': rating_source,
                'rating': rating,
                'votes': votes,
                'defaultt': False,
                }

    def set_properties(self, properties):
        self._properties = properties

    def set_context_menu(self, context_menu):
        self._context_menu = context_menu


class MainMenuItem(EmptyListItem):

    def __init__(self, section_info):
        self._info = section_info

    @property
    def label(self):
        return self._info.get('label')

    @property
    def content_lookup(self):
        return False

    @property
    def icon(self):
        return self._info.get('icon')

    @property
    def fanart(self):
        return plugin.fanart


class FilterItem(EmptyListItem):
    _filter_name = ''
    _values = None

    def __init__(self, filter_name, values):
        self._filter_name = filter_name
        self._values = values

    @property
    def label(self):
        title = Utilities.get_filter_title(self._filter_name)
        label = self._make_label('yellowgreen', title, self._values)
        return label

    @property
    def content_lookup(self):
        return False

    @property
    def icon(self):
        return Utilities.get_filter_icon(self._filter_name)

    @property
    def fanart(self):
        return plugin.fanart

    @property
    def is_folder(self):
        return False

    @property
    def is_playable(self):
        return False

    @staticmethod
    def _make_label(color, title, values):
        return '[COLOR={0}][B]{1}:[/B] {2}[/COLOR]'.format(color, title, values)
