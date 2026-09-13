"""Conversation platform for Jarvis Router.

This entity is deliberately thin.

It does NOT attach Home Assistant tools itself. Instead:
1. Home Assistant sends the user's text here.
2. This entity calls the external Jarvis Router API.
3. Jarvis selects a downstream Home Assistant conversation agent.
4. Jarvis calls Home Assistant's /api/conversation/process endpoint.
5. The selected downstream agent owns the appropriate tools and prompt.
6. Jarvis returns final speech to this entity.

That "bounce back" is the central architecture of this project.
"""

from typing import Literal

import aiohttp

from homeassistant.components import conversation
from homeassistant.components.conversation import (
    AssistantContent,
    ChatLog,
    ConversationEntity,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_API_KEY, CONF_URL


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Jarvis Router conversation entity."""

    async_add_entities(
        [
            JarvisRouterConversationEntity(
                hass,
                entry,
            )
        ]
    )


class JarvisRouterConversationEntity(ConversationEntity):
    """Home Assistant front-end for Jarvis Router."""

    _attr_name = "Jarvis Router"
    _attr_unique_id = "jarvis_router_conversation"
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Store router URL and bearer token from the config entry."""
        self.hass = hass
        self._url = entry.data[CONF_URL].rstrip("/")
        self._api_key = entry.data[CONF_API_KEY]

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Accept all HA languages.

        The reference router currently sends en-GB downstream, so adapt
        jarvis-route if you want true multilingual routing.
        """
        return MATCH_ALL

    async def _async_handle_message(
        self,
        user_input: ConversationInput,
        chat_log: ChatLog,
    ) -> ConversationResult:
        """Send the user's utterance to Jarvis and return final speech."""

        session = async_get_clientsession(self.hass)

        try:
            async with session.post(
                f"{self._url}/route",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": user_input.text,
                },
                timeout=aiohttp.ClientTimeout(total=90),
            ) as response:

                if response.status != 200:
                    body = await response.text()
                    raise RuntimeError(
                        f"Jarvis Router returned "
                        f"HTTP {response.status}: {body}"
                    )

                data = await response.json()

        except Exception:
            # Keep the voice pipeline graceful if the external router is down.
            speech = "Sorry, the Jarvis router is unavailable."

            chat_log.async_add_assistant_content_without_tools(
                AssistantContent(
                    agent_id=user_input.agent_id,
                    content=speech,
                )
            )

            result = intent.IntentResponse(
                language=user_input.language
            )
            result.async_set_speech(speech)

            return conversation.ConversationResult(
                conversation_id=user_input.conversation_id,
                response=result,
                continue_conversation=False,
            )

        speech = data.get("speech")

        if not speech:
            speech = "Sorry, I didn't receive a response."

        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id=user_input.agent_id,
                content=speech,
            )
        )

        result = intent.IntentResponse(
            language=user_input.language
        )
        result.async_set_speech(speech)

        return conversation.ConversationResult(
            conversation_id=user_input.conversation_id,
            response=result,
            continue_conversation=False,
        )
