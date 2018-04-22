"""
Support for Alexa skill service end point.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/alexa/
"""
import asyncio
import copy
import logging

import voluptuous as vol

from homeassistant.helpers import (template, script, config_validation as cv)

from . import intent

REQUIREMENTS = ['requests==2.18.4']

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['http']

DOMAIN = 'alexa_intent'

CONF_SPEECH = 'speech'
CONF_DIRECTIVES = 'directives'

CONF_ACTION = 'action'
CONF_CARD = 'card'
CONF_TYPE = 'type'
CONF_TITLE = 'title'
CONF_CONTENT = 'content'
CONF_TEXT = 'text'
CONF_KEEP = 'keep'
CONF_AUDIO_TYPE = 'audio_type'
CONF_AUDIO_URL = 'audio_url'
CONF_ASYNC_ACTION = 'async_action'

DEFAULT_CONF_ASYNC_ACTION = False

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: {
        cv.string: {
            vol.Optional(CONF_ACTION): cv.SCRIPT_SCHEMA,
            vol.Optional(CONF_ASYNC_ACTION, default=DEFAULT_CONF_ASYNC_ACTION): cv.boolean,
            vol.Optional(CONF_CARD): {
                vol.Optional(CONF_TYPE, default='simple'): cv.string,
                vol.Required(CONF_TITLE): cv.template,
                vol.Required(CONF_CONTENT): cv.template,
            },
            vol.Optional(CONF_SPEECH): {
                vol.Optional(CONF_TYPE, default='plain'): cv.string,
                vol.Required(CONF_TEXT): cv.template,
            },
            vol.Optional(CONF_DIRECTIVES): {
                vol.Required(CONF_TYPE): cv.string,
                vol.Optional(CONF_AUDIO_TYPE, default='mp3'): cv.string,
                vol.Optional(CONF_AUDIO_URL, default=''): cv.template,
            },
            vol.Optional(CONF_KEEP, default=False): cv.boolean
        }
    }
}, extra=vol.ALLOW_EXTRA)


@asyncio.coroutine
def async_setup(hass, config):
    """Activate Alexa component."""

    intents = copy.deepcopy(config[DOMAIN])
    template.attach(hass, intents)

    for intent_type, conf in intents.items():
        if CONF_ACTION in conf:
            conf[CONF_ACTION] = script.Script(
                hass, conf[CONF_ACTION],
                "Intent Script {}".format(intent_type))

        intent.async_register(hass, ScriptIntentHandler(intent_type, conf))

    audio_player = {
        'AudioPlayer.PlaybackStarted': 'playback_started',
        'AudioPlayer.PlaybackFinished': 'playback_finished',
        'AudioPlayer.PlaybackNearlyFinished': 'playback_nearly_finished',
        'AudioPlayer.PlaybackFailed': 'playback_failed',
    }

    for (intent_type, value) in audio_player.items():
        handler = hass.data.get(intent.DATA_KEY, {}).get(intent_type)
        if handler is None:
            _LOGGER.info("Intent register %s", intent_type)
            intent.async_register(hass, ScriptIntentHandler(intent_type, {
                'directives': {
                    CONF_AUDIO_TYPE: 'api',
                    CONF_AUDIO_URL: '',
                    CONF_TYPE: value
                }
            }))

    intent.async_setup(hass)

    return True


class ScriptIntentHandler(intent.IntentHandler):
    """Respond to an intent with a script."""

    def __init__(self, intent_type, config):
        """Initialize the script intent handler."""
        self.intent_type = intent_type
        self.config = config

    @asyncio.coroutine
    def async_handle(self, intent_obj):
        """Handle the intent."""
        speech = self.config.get(CONF_SPEECH)
        card = self.config.get(CONF_CARD)
        directives = self.config.get(CONF_DIRECTIVES)
        action = self.config.get(CONF_ACTION)
        keep = self.config.get(CONF_KEEP)
        is_async_action = self.config.get(CONF_ASYNC_ACTION)
        slots = {key: value['value'] for key, value
                 in intent_obj.slots.items()}

        if action is not None:
            if is_async_action:
                intent_obj.hass.async_add_job(action.async_run(slots))
            else:
                yield from action.async_run(slots)

        response = intent_obj.create_response()

        if speech is not None:
            response.async_set_speech(speech[CONF_TEXT].async_render(slots),
                                      speech[CONF_TYPE])

        if card is not None:
            response.async_set_card(
                card[CONF_TITLE].async_render(slots),
                card[CONF_CONTENT].async_render(slots),
                card[CONF_TYPE])

        if directives is not None:
            response.async_set_directive(
                directives[CONF_AUDIO_TYPE],
                directives[CONF_AUDIO_URL],
                directives[CONF_TYPE])

        # 设置 should_end_session
        if keep is not None:
            response.async_set_keep(keep)

        _LOGGER.info("Intent %s response %s", intent_obj, response)

        return response
