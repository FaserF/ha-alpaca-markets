"""Config flow for the Alpaca Markets integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .api.client import AlpacaAPIClient
from .api.exceptions import AlpacaAuthError, AlpacaConnectionError, AlpacaError
from .const import (
    CONF_API_KEY_ID,
    CONF_API_SECRET_KEY,
    CONF_TRADING_MODE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_TRADING_MODE,
    DEFAULT_UPDATE_INTERVAL,
    DOCS_URL,
    DOMAIN,
    TRADING_MODE_LIVE,
    TRADING_MODE_PAPER,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY_ID): str,
        vol.Required(CONF_API_SECRET_KEY): str,
        vol.Required(CONF_TRADING_MODE, default=DEFAULT_TRADING_MODE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[TRADING_MODE_PAPER, TRADING_MODE_LIVE],
                translation_key="trading_mode",
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)


class AlpacaMarketsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Alpaca Markets."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._data: dict[str, Any] = {}
        self._account_id: str = ""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AlpacaMarketsOptionsFlow:
        """Return the options flow handler."""
        return AlpacaMarketsOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors, account_id = await self._validate_credentials(user_input)
            if not errors:
                await self.async_set_unique_id(account_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Alpaca Markets ({user_input[CONF_TRADING_MODE].title()})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={"docs_url": DOCS_URL},
        )

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication confirmation step."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            data = {**entry.data, **user_input}
            errors, _ = await self._validate_credentials(data)
            if not errors:
                self.hass.config_entries.async_update_entry(entry, data=data)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY_ID, default=entry.data.get(CONF_API_KEY_ID, "")): str,
                    vol.Required(CONF_API_SECRET_KEY): str,
                }
            ),
            errors=errors,
        )

    async def _validate_credentials(
        self, data: dict[str, Any]
    ) -> tuple[dict[str, str], str]:
        """Validate API credentials by calling /v2/account. Returns (errors, account_id)."""
        session = async_get_clientsession(self.hass)
        client = AlpacaAPIClient(
            api_key_id=data[CONF_API_KEY_ID],
            api_secret_key=data[CONF_API_SECRET_KEY],
            trading_mode=data.get(CONF_TRADING_MODE, DEFAULT_TRADING_MODE),
            session=session,
        )
        try:
            account = await client.get_account()
            return {}, account.get("id", "unknown")
        except AlpacaAuthError:
            return {"base": "invalid_auth"}, ""
        except AlpacaConnectionError:
            return {"base": "cannot_connect"}, ""
        except AlpacaError:
            return {"base": "unknown"}, ""


class AlpacaMarketsOptionsFlow(OptionsFlow):
    """Handle options for Alpaca Markets."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self._config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
                }
            ),
        )
