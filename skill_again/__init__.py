# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

from adapt.intent import IntentBuilder
from mycroft.messagebus.message import Message
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

__author__ = 'jarbas'

LOGGER = getLogger(__name__)


class AgainSkill(MycroftSkill):
    def __init__(self):
        super(AgainSkill, self).__init__()
        self.reload_skill = False
        self.last_skill = 0
        self.last_intent = None
        self.last_intent_data = {}
        self.last_intent_context = {}
        self.message_context = self.get_message_context({"repetition": True})
        self.last_context = self.message_context
        self.last_intent_context = self.message_context
        self.last_utterance = None

    def initialize(self):
        again_intent = IntentBuilder("AgainIntent"). \
            require("AgainKeyword").build()
        self.register_intent(again_intent, self.handle_again_intent)
        self.emitter.on("recognizer_loop:utterance", self.track_utterance)
        self.emitter.on("mycroft.skill.handler.complete", self.track_intent)

    def track_utterance(self, message):
        utterance = message.data.get("utterances", [" "])[0]
        if utterance:
            self.log.info(
                "Tracking last executed utterance: " + utterance)
            self.last_utterance = utterance
            self.last_skill = "utterance"
            self.last_context = self.get_message_context(message.context)

    def track_intent(self, message):
        intent = message.data.get("intent")
        data = message.data.get("data")
        context = message.data.get("context")
        if intent:
            skill, intent = intent.split(":")
            if skill == str(self.skill_id):
                return
            self.log.info("Tracking last executed intent: " + intent)
            self.last_skill = skill
            self.last_intent = intent
            self.last_intent_data = data
            self.last_intent_context = self.get_message_context(context)

    def handle_again_intent(self, message):
        if self.last_skill == "utterance":
            msg = Message("recognizer_loop:utterance",
                          {"utterance": self.last_utterance},
                          self.last_context)
            self.log.info("Repeating last sent utterance")
            self.emitter.emit(msg)
            return
        elif self.last_intent is None:
            self.speak_dialog("again.fail")
            return
        msg = Message(str(self.last_skill) + ":" + self.last_intent,
                      self.last_intent_data, self.last_intent_context)
        # self.speak_dialog("again", {"intent": self.last_intent})
        self.log.info("Repeating last executed intent")
        self.emitter.emit(msg)

    def stop(self):
        pass


def create_skill():
    return AgainSkill()
