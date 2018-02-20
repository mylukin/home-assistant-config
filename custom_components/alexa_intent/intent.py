"""
Support for Alexa skill service end point.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/alexa/
https://developer.amazon.com/docs/custom-skills/audioplayer-interface-reference.html

"""
import asyncio
import enum
import json
import logging

import voluptuous as vol

from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import callback
from homeassistant.components import http
from homeassistant.util.decorator import Registry
from homeassistant.loader import bind_hass

DOMAIN = 'alexa_intent'

SYN_RESOLUTION_MATCH = 'ER_SUCCESS_MATCH'

INTENTS_API_ENDPOINT = '/api/alexa_intent'
HANDLERS = Registry()
_LOGGER = logging.getLogger(__name__)

DATA_KEY = DOMAIN
PLAYLIST_DATA_KEY = "{}_playlist".format(DOMAIN)
PLAYLIST_DATA_FILE = '.alexa_play'

SLOT_SCHEMA = vol.Schema({
}, extra=vol.ALLOW_EXTRA)


class SpeechType(enum.Enum):
    """The Alexa speech types."""

    plaintext = "PlainText"
    ssml = "SSML"


SPEECH_MAPPINGS = {
    'plain': SpeechType.plaintext,
    'ssml': SpeechType.ssml,
}


class DirectiveType(enum.Enum):
    """The Alexa speech types."""

    play = 'AudioPlayer.Play'
    next = 'AudioPlayer.Next'
    stop = 'AudioPlayer.Stop'
    ClearQueue = 'AudioPlayer.ClearQueue'
    PlaybackStarted = 'AudioPlayer.PlaybackStarted'
    PlaybackFinished = 'AudioPlayer.PlaybackFinished'
    PlaybackStopped = 'AudioPlayer.PlaybackStopped'
    PlaybackNearlyFinished = 'AudioPlayer.PlaybackNearlyFinished'
    PlaybackFailed = 'AudioPlayer.PlaybackFailed'


DIRECTIVE_MAPPINGS = {
    'play': DirectiveType.play,
    'next': DirectiveType.next,
    'stop': DirectiveType.stop,
    'clear_queue': DirectiveType.ClearQueue,
    'playback_started': DirectiveType.PlaybackStarted,
    'playback_finished': DirectiveType.PlaybackFinished,
    'playback_stopped': DirectiveType.PlaybackStopped,
    'playback_nearly_finished': DirectiveType.PlaybackNearlyFinished,
    'playback_failed': DirectiveType.PlaybackFailed,
}


class CardType(enum.Enum):
    """The Alexa card types."""

    simple = "Simple"
    link_account = "LinkAccount"


@callback
def async_setup(hass):
    """Activate Alexa component."""
    hass.http.register_view(AlexaIntentsView)


class UnknownRequest(HomeAssistantError):
    """When an unknown Alexa request is passed in."""


class AlexaIntentsView(http.HomeAssistantView):
    """Handle Alexa requests."""

    url = INTENTS_API_ENDPOINT
    name = 'api:alexa_intent'

    @asyncio.coroutine
    def post(self, request):
        """Handle Alexa."""
        hass = request.app['hass']
        message = yield from request.json()

        _LOGGER.debug('Received Alexa request: %s', message)

        try:
            response = yield from async_handle_message(hass, message)
            return b'' if response is None else self.json(response)
        except UnknownRequest as err:
            _LOGGER.warning(str(err))
            return self.json(intent_error_response(
                hass, message, str(err)))

        except UnknownIntent as err:
            _LOGGER.warning(str(err))
            return self.json(intent_error_response(
                hass, message,
                "This intent is not yet configured within Home Assistant."))

        except InvalidSlotInfo as err:
            _LOGGER.error('Received invalid slot data from Alexa: %s', err)
            return self.json(intent_error_response(
                hass, message,
                "Invalid slot information received for this intent."))

        except IntentError as err:
            _LOGGER.exception(str(err))
            return self.json(intent_error_response(
                hass, message, "Error handling intent."))


def intent_error_response(hass, message, error):
    """Return an Alexa response that will speak the error message."""
    alexa_intent_info = message.get('request').get('intent')
    alexa_response = AlexaResponse(hass, alexa_intent_info)
    alexa_response.add_speech(SpeechType.plaintext, error)
    return alexa_response.as_dict()


@asyncio.coroutine
def async_handle_message(hass, message):
    """Handle an Alexa intent.

    Raises:
     - UnknownRequest
     - UnknownIntent
     - InvalidSlotInfo
     - IntentError
    """
    req = message.get('request')
    req_type = req['type']

    handler = HANDLERS.get(req_type)

    if not handler:
        raise UnknownRequest('Received unknown request {}'.format(req_type))

    return (yield from handler(hass, message))


@HANDLERS.register('SessionEndedRequest')
@asyncio.coroutine
def async_handle_session_end(hass, message):
    """Handle a session end request."""
    alexa_response = AlexaResponse(hass, None)

    return alexa_response.as_dict()


@HANDLERS.register('AudioPlayer.PlaybackStopped')
@asyncio.coroutine
def async_handle_audio_player_nothing(hass, message):
    """Handle a session end request."""
    alexa_response = AlexaResponse(hass, None)

    return alexa_response.as_dict()


@HANDLERS.register('AudioPlayer.PlaybackStarted')
@HANDLERS.register('AudioPlayer.PlaybackFinished')
@HANDLERS.register('AudioPlayer.PlaybackNearlyFinished')
@HANDLERS.register('AudioPlayer.PlaybackFailed')
@HANDLERS.register('IntentRequest')
@HANDLERS.register('LaunchRequest')
@asyncio.coroutine
def async_handle_intent(hass, message):
    """Handle an intent request.

    Raises:
     - UnknownIntent
     - InvalidSlotInfo
     - IntentError
    """
    req = message.get('request')
    _LOGGER.info("Intent request: %s", req)
    alexa_intent_info = req.get('intent')
    alexa_response = AlexaResponse(hass, alexa_intent_info)

    if req['type'] == 'LaunchRequest':
        intent_name = message.get('session', {}) \
            .get('application', {}) \
            .get('applicationId')
    elif alexa_intent_info is None:
        intent_name = req['type']
    else:
        intent_name = alexa_intent_info['name']

    _LOGGER.info("intent_name: %s", intent_name)

    intent_response = yield from async_handle(
        hass, DOMAIN, intent_name,
        {key: {'value': value} for key, value
         in alexa_response.variables.items()})

    _LOGGER.info("intent_response: %s", intent_response)

    for intent_speech, alexa_speech in SPEECH_MAPPINGS.items():
        if intent_speech in intent_response.speech:
            alexa_response.add_speech(
                alexa_speech,
                intent_response.speech[intent_speech]['speech'])
            break

    for intent_directive, alexa_directive in DIRECTIVE_MAPPINGS.items():
        #_LOGGER.info("intent_directive: %s, intent_response.directives: %s", intent_directive, intent_response.directives)
        if intent_directive in intent_response.directives:
            _LOGGER.info("Found %s, %s", intent_directive, alexa_directive.value)

            # 开始播放
            if alexa_directive.value == DirectiveType.play.value:
                # 音频类型
                audio_type = intent_response.directives[intent_directive]['audio_type']
                # 音频URL
                audio_url = intent_response.directives[intent_directive]['audio_url']
                _LOGGER.info("audio_type: %s, audio_url: %s", audio_type, audio_url)
                playlist_save(hass, 'play', {
                    'audio_type': audio_type,
                    'audio_url': audio_url,
                })
                alexa_response.add_audio_play(audio_type, audio_url, 'REPLACE_ALL')
            # 自动下一首
            elif alexa_directive.value == DirectiveType.PlaybackNearlyFinished.value:
                # 获取保存的播放列表
                directives = get_playlist(hass, 'play')
                _LOGGER.info("directives: %s", directives)
                # 获取上一次的token
                token = req.get('token')
                # 音频类型
                audio_type = directives['audio_type']
                # 音频URL
                audio_url = directives['audio_url']
                _LOGGER.info("PlaybackNearlyFinished, token: %s, audio_type: %s, audio_url: %s", token, audio_type,
                             audio_url)
                alexa_response.add_audio_play(audio_type, audio_url, 'ENQUEUE', token)
            # 手动下一首
            elif alexa_directive.value == DirectiveType.next.value:
                # 获取保存的播放列表
                directives = get_playlist(hass, 'play')
                _LOGGER.info("directives: %s", directives)
                # 获取上一次的token
                token = req.get('token')
                # 音频类型
                audio_type = directives['audio_type']
                # 音频URL
                audio_url = directives['audio_url']
                _LOGGER.info("Next, token: %s, audio_type: %s, audio_url: %s", token, audio_type, audio_url)
                alexa_response.add_audio_play(audio_type, audio_url, 'REPLACE_ALL', token)
            # 播放开始
            elif alexa_directive.value == DirectiveType.PlaybackStarted.value:
                playlist_save(hass, 'play_state', 'play')
            # 播放
            elif alexa_directive.value == DirectiveType.PlaybackFinished.value:
                pass
            elif alexa_directive.value == DirectiveType.stop.value:
                alexa_response.add_audio_stop()
                playlist_save(hass, 'play_song', {})
                playlist_save(hass, 'play_state', 'stop')

            break

    if 'simple' in intent_response.card:
        alexa_response.add_card(
            CardType.simple, intent_response.card['simple']['title'],
            intent_response.card['simple']['content'])

    # 设置 should_end_session
    alexa_response.should_end_session = (intent_response.keep == False)

    _LOGGER.info("alexa_response: %s", alexa_response)

    response = alexa_response.as_dict()

    _LOGGER.info("response: %s", response)

    return response


def resolve_slot_synonyms(key, request):
    """Check slot request for synonym resolutions."""
    # Default to the spoken slot value if more than one or none are found. For
    # reference to the request object structure, see the Alexa docs:
    # https://tinyurl.com/ybvm7jhs
    resolved_value = request['value']

    if ('resolutions' in request and
                'resolutionsPerAuthority' in request['resolutions'] and
                len(request['resolutions']['resolutionsPerAuthority']) >= 1):

        # Extract all of the possible values from each authority with a
        # successful match
        possible_values = []

        for entry in request['resolutions']['resolutionsPerAuthority']:
            if entry['status']['code'] != SYN_RESOLUTION_MATCH:
                continue

            possible_values.extend([item['value']['name']
                                    for item
                                    in entry['values']])

        # If there is only one match use the resolved value, otherwise the
        # resolution cannot be determined, so use the spoken slot value
        if len(possible_values) == 1:
            resolved_value = possible_values[0]
        else:
            _LOGGER.debug(
                'Found multiple synonym resolutions for slot value: {%s: %s}',
                key,
                request['value']
            )

    return resolved_value


class AlexaResponse(object):
    """Help generating the response for Alexa."""

    def __init__(self, hass, intent_info):
        """Initialize the response."""
        self.hass = hass
        self.speech = None
        self.card = None
        self.reprompt = None
        self.directives = None
        self.session_attributes = {}
        self.should_end_session = True
        self.variables = {}

        # Intent is None if request was a LaunchRequest or SessionEndedRequest
        if intent_info is not None:
            for key, value in intent_info.get('slots', {}).items():
                # Only include slots with values
                if 'value' not in value:
                    continue

                _key = key.replace('.', '_')

                self.variables[_key] = resolve_slot_synonyms(key, value)

    def add_card(self, card_type, title, content):
        """Add a card to the response."""
        assert self.card is None

        card = {
            "type": card_type.value
        }

        if card_type == CardType.link_account:
            self.card = card
            return

        card["title"] = title
        card["content"] = content
        self.card = card

    def add_speech(self, speech_type, text):
        """Add speech to the response."""
        assert self.speech is None

        key = 'ssml' if speech_type == SpeechType.ssml else 'text'

        self.speech = {
            'type': speech_type.value,
            key: text
        }

    def add_reprompt(self, speech_type, text):
        """Add reprompt if user does not answer."""
        assert self.reprompt is None

        key = 'ssml' if speech_type == SpeechType.ssml else 'text'

        self.reprompt = {
            'type': speech_type.value,
            key: text.async_render(self.variables)
        }

    def add_audio_play(self, type, url, behavior='REPLACE_ALL', expectedPreviousToken=None, offsetInMilliseconds=0):
        """
        播放音频

        :param url:
        :param behavior:
        :param expectedPreviousToken:
        :param offsetInMilliseconds:
        :return:
        """

        import hashlib
        token = hashlib.md5(url.encode()).hexdigest()
        if type == 'api':
            import random
            import requests
            resp = requests.get(url)
            _LOGGER.info("status_code: {}".format(resp.status_code))
            if resp.status_code == 200:
                songs = resp.json()
                count = len(songs)
                _LOGGER.info("songs count: {}".format(count))

                songid = random.randint(0, count - 1)
                song = songs[songid]
                _LOGGER.info("song: %s", json.dumps(song, ensure_ascii=False))
                url = song['url']
                # 保存当前正在播放的歌曲
                playlist_save(self.hass, 'play_song', song)

        self.audio_play(behavior, token, url, expectedPreviousToken, offsetInMilliseconds)

    def add_audio_stop(self):
        """
        停止音频

        :return:
        """
        self.audio_stop()

    def as_dict(self):
        """Return response in an Alexa valid dict."""
        response = {
            'shouldEndSession': self.should_end_session
        }

        if self.card is not None:
            response['card'] = self.card

        if self.speech is not None:
            response['outputSpeech'] = self.speech

        if self.reprompt is not None:
            response['reprompt'] = {
                'outputSpeech': self.reprompt
            }

        if self.directives is not None:
            response['directives'] = self.directives

        return {
            'version': '1.0',
            'sessionAttributes': self.session_attributes,
            'response': response,
        }

    def audio_play(self, behavior, token, url, expectedPreviousToken=None, offsetInMilliseconds=0):
        """
        AudioPlayer.Play

        :param behavior:
        :param token:
        :param url:
        :param expectedPreviousToken:
        :param offsetInMilliseconds:
        :return:
        """
        if expectedPreviousToken:
            stream = {
                'token': token,
                'url': url,
                'offsetInMilliseconds': offsetInMilliseconds,
                'expectedPreviousToken': expectedPreviousToken,
            }
        else:
            stream = {
                'token': token,
                'url': url,
                'offsetInMilliseconds': offsetInMilliseconds,
            }
        directive = {
            'type': DirectiveType.play.value,
            'playBehavior': behavior,
            'audioItem': {
                'stream': stream
            }
        }
        _LOGGER.info("directive: %s", directive)
        self.directives = [directive]

    def audio_stop(self):
        """
        AudioPlayer.Stop

        :return:
        """
        self.directives = [{
            'type': DirectiveType.stop.value,
        }]

    def audio_clear_queue(self, clearBehavior='CLEAR_ALL'):
        """
        AudioPlayer.ClearQueue

        :param clearBehavior:
        :return:
        """
        self.directives = [{
            'type': DirectiveType.ClearQueue.value,
            'clearBehavior': clearBehavior,
        }]


@callback
@bind_hass
def async_register(hass, handler):
    """Register an intent with Home Assistant."""
    intents = hass.data.get(DATA_KEY)
    if intents is None:
        intents = hass.data[DATA_KEY] = {}

    if handler.intent_type in intents:
        _LOGGER.warning('Intent %s is being overwritten by %s.',
                        handler.intent_type, handler)

    intents[handler.intent_type] = handler


@bind_hass
def playlist_save(hass, key, playlist):
    """保存播放列表"""
    playlists = hass.data.get(PLAYLIST_DATA_KEY)
    if playlists is None:
        try:
            with open(hass.config.path(PLAYLIST_DATA_FILE)) as fptr:
                playlists = json.loads(fptr.read())
        except FileNotFoundError:
            playlists = hass.data[PLAYLIST_DATA_KEY] = {}

    _LOGGER.info("Playlist save. key:%s, playlist: %s", key, playlist)
    playlists[key] = playlist

    with open(hass.config.path(PLAYLIST_DATA_FILE), 'w') as fptr:
        fptr.write(json.dumps(playlists))


@bind_hass
def get_playlist(hass, key):
    """Load playlist from a file or return None."""

    playlist = hass.data.get(PLAYLIST_DATA_KEY, {}).get(key)
    if playlist is not None:
        return playlist

    # 内存没有，读文件
    try:
        with open(hass.config.path(PLAYLIST_DATA_FILE)) as fptr:
            jsonf = json.loads(fptr.read())
            return jsonf[key]
    except (ValueError, AttributeError):
        return None
    except FileNotFoundError:
        return None


@asyncio.coroutine
@bind_hass
def async_handle(hass, platform, intent_type, slots=None, text_input=None):
    """Handle an intent."""
    handler = hass.data.get(DATA_KEY, {}).get(intent_type)

    if handler is None:
        raise UnknownIntent()

    intent = Intent(hass, platform, intent_type, slots or {}, text_input)

    try:
        _LOGGER.info("Triggering intent handler %s", handler)
        result = yield from handler.async_handle(intent)
        return result
    except vol.Invalid as err:
        raise InvalidSlotInfo from err
    except Exception as err:
        raise IntentHandleError from err


class IntentError(HomeAssistantError):
    """Base class for intent related errors."""

    pass


class UnknownIntent(IntentError):
    """When the intent is not registered."""

    pass


class InvalidSlotInfo(IntentError):
    """When the slot data is invalid."""

    pass


class IntentHandleError(IntentError):
    """Error while handling intent."""

    pass


class IntentHandler:
    """Intent handler registration."""

    intent_type = None
    slot_schema = None
    _slot_schema = None
    platforms = None

    @callback
    def async_can_handle(self, intent_obj):
        """Test if an intent can be handled."""
        return self.platforms is None or intent_obj.platform in self.platforms

    @callback
    def async_validate_slots(self, slots):
        """Validate slot information."""
        if self.slot_schema is None:
            return slots

        if self._slot_schema is None:
            self._slot_schema = vol.Schema({
                key: SLOT_SCHEMA.extend({'value': validator})
                for key, validator in self.slot_schema.items()})

        return self._slot_schema(slots)

    @asyncio.coroutine
    def async_handle(self, intent_obj):
        """Handle the intent."""
        raise NotImplementedError()

    def __repr__(self):
        """String representation of intent handler."""
        return '<{} - {}>'.format(self.__class__.__name__, self.intent_type)


class Intent:
    """Hold the intent."""

    __slots__ = ['hass', 'platform', 'intent_type', 'slots', 'text_input']

    def __init__(self, hass, platform, intent_type, slots, text_input):
        """Initialize an intent."""
        self.hass = hass
        self.platform = platform
        self.intent_type = intent_type
        self.slots = slots
        self.text_input = text_input

    @callback
    def create_response(self):
        """Create a response."""
        return IntentResponse(self)


class IntentResponse:
    """Response to an intent."""

    def __init__(self, intent=None):
        """Initialize an IntentResponse."""
        self.intent = intent
        self.speech = {}
        self.card = {}
        self.directives = {}
        self.keep = False

    @callback
    def async_set_keep(self, value):
        """Set EndSession response."""
        self.keep = value

    @callback
    def async_set_speech(self, speech, speech_type='plain', extra_data=None):
        """Set speech response."""
        self.speech[speech_type] = {
            'speech': speech,
            'extra_data': extra_data,
        }

    @callback
    def async_set_card(self, title, content, card_type='simple'):
        """Set speech response."""
        self.card[card_type] = {
            'title': title,
            'content': content,
        }

    @callback
    def async_set_directive(self, audio_type, audio_url, directive_type='play'):
        """Set directives response."""
        self.directives[directive_type] = {
            'audio_type': audio_type,
            'audio_url': audio_url.async_render(),
        }

    @callback
    def as_dict(self):
        """Return a dictionary representation of an intent response."""
        return {
            'speech': self.speech,
            'card': self.card,
        }
