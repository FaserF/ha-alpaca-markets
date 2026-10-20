"""Alpaca Markets API client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from ..const import API_BASE_URLS, HEADER_KEY_ID, HEADER_SECRET_KEY
from .exceptions import (
    AlpacaAPIError,
    AlpacaAuthError,
    AlpacaConnectionError,
    AlpacaRateLimitError,
    AlpacaTimeoutError,
)

_LOGGER = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 30


class AlpacaAPIClient:
    """Async HTTP client for the Alpaca Markets Trading API v2."""

    def __init__(
        self,
        api_key_id: str,
        api_secret_key: str,
        trading_mode: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the client."""
        self._api_key_id = api_key_id
        self._api_secret_key = api_secret_key
        self._base_url = API_BASE_URLS[trading_mode]
        self._session = session

    @property
    def _headers(self) -> dict[str, str]:
        """Return authentication headers."""
        return {
            HEADER_KEY_ID: self._api_key_id,
            HEADER_SECRET_KEY: self._api_secret_key,
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Perform an authenticated request to the Alpaca API."""
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        try:
            async with asyncio.timeout(_REQUEST_TIMEOUT):
                async with self._session.request(
                    method,
                    url,
                    headers=self._headers,
                    params=params,
                    json=json,
                ) as response:
                    if response.status in (401, 403):
                        text = await response.text()
                        raise AlpacaAuthError(
                            f"Authentication failed ({response.status}): {text}"
                        )
                    if response.status == 429:
                        text = await response.text()
                        raise AlpacaRateLimitError(response.status, text)
                    if response.status == 204:
                        return None
                    if not response.ok:
                        text = await response.text()
                        raise AlpacaAPIError(response.status, text)
                    if response.content_type == "application/json":
                        return await response.json()
                    return await response.text()
        except AlpacaError:
            raise
        except asyncio.TimeoutError as err:
            raise AlpacaTimeoutError("Request timed out") from err
        except aiohttp.ClientConnectionError as err:
            raise AlpacaConnectionError(f"Connection error: {err}") from err
        except aiohttp.ClientError as err:
            raise AlpacaConnectionError(f"HTTP client error: {err}") from err

    # ------------------------------------------------------------------ #
    # Account
    # ------------------------------------------------------------------ #

    async def get_account(self) -> dict[str, Any]:
        """Get account details."""
        result = await self._request("GET", "/account")
        return result  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Market clock
    # ------------------------------------------------------------------ #

    async def get_clock(self) -> dict[str, Any]:
        """Get market clock (open/closed status, next open/close times)."""
        result = await self._request("GET", "/clock")
        return result  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Positions
    # ------------------------------------------------------------------ #

    async def get_positions(self) -> list[dict[str, Any]]:
        """Get all open positions."""
        result = await self._request("GET", "/positions")
        return result or []  # type: ignore[return-value]

    async def get_position(self, symbol: str) -> dict[str, Any]:
        """Get open position for a specific symbol."""
        result = await self._request("GET", f"/positions/{symbol}")
        return result  # type: ignore[return-value]

    async def close_position(
        self,
        symbol: str,
        qty: float | None = None,
        percentage: float | None = None,
    ) -> dict[str, Any]:
        """Close (liquidate) a position for a symbol."""
        params: dict[str, Any] = {}
        if qty is not None:
            params["qty"] = str(qty)
        elif percentage is not None:
            params["percentage"] = str(percentage)
        result = await self._request("DELETE", f"/positions/{symbol}", params=params)
        return result or {}  # type: ignore[return-value]

    async def close_all_positions(self, cancel_orders: bool = True) -> None:
        """Liquidate all open positions."""
        await self._request(
            "DELETE",
            "/positions",
            params={"cancel_orders": str(cancel_orders).lower()},
        )

    # ------------------------------------------------------------------ #
    # Orders
    # ------------------------------------------------------------------ #

    async def get_orders(
        self,
        status: str = "open",
        limit: int = 500,
        direction: str = "desc",
    ) -> list[dict[str, Any]]:
        """Get orders filtered by status."""
        result = await self._request(
            "GET",
            "/orders",
            params={"status": status, "limit": limit, "direction": direction},
        )
        return result or []  # type: ignore[return-value]

    async def get_order(self, order_id: str) -> dict[str, Any]:
        """Get a single order by its ID."""
        result = await self._request("GET", f"/orders/{order_id}")
        return result  # type: ignore[return-value]

    async def place_order(
        self,
        symbol: str,
        qty: float | None,
        side: str,
        order_type: str,
        time_in_force: str,
        limit_price: float | None = None,
        stop_price: float | None = None,
        notional: float | None = None,
    ) -> dict[str, Any]:
        """Place a new order."""
        payload: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force,
        }
        if qty is not None:
            payload["qty"] = str(qty)
        if notional is not None:
            payload["notional"] = str(notional)
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        if stop_price is not None:
            payload["stop_price"] = str(stop_price)
        result = await self._request("POST", "/orders", json=payload)
        return result  # type: ignore[return-value]

    async def cancel_order(self, order_id: str) -> None:
        """Cancel an open order by ID."""
        await self._request("DELETE", f"/orders/{order_id}")

    async def cancel_all_orders(self) -> None:
        """Cancel all open orders."""
        await self._request("DELETE", "/orders")

    # ------------------------------------------------------------------ #
    # Portfolio history
    # ------------------------------------------------------------------ #

    async def get_portfolio_history(
        self,
        period: str = "1D",
        timeframe: str = "1Min",
    ) -> dict[str, Any]:
        """Get historical portfolio equity data."""
        result = await self._request(
            "GET",
            "/account/portfolio/history",
            params={"period": period, "timeframe": timeframe},
        )
        return result or {}  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Account activities
    # ------------------------------------------------------------------ #

    async def get_account_activities(
        self,
        activity_type: str | None = None,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        """Get account activity records."""
        endpoint = (
            f"/account/activities/{activity_type}"
            if activity_type
            else "/account/activities"
        )
        result = await self._request(
            "GET", endpoint, params={"page_size": page_size, "direction": "desc"}
        )
        return result or []  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Watchlists
    # ------------------------------------------------------------------ #

    async def get_watchlists(self) -> list[dict[str, Any]]:
        """Get all watchlists."""
        result = await self._request("GET", "/watchlists")
        return result or []  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Assets
    # ------------------------------------------------------------------ #

    async def get_assets(
        self,
        asset_class: str | None = None,
        status: str = "active",
    ) -> list[dict[str, Any]]:
        """Get tradable assets."""
        params: dict[str, Any] = {"status": status}
        if asset_class:
            params["asset_class"] = asset_class
        result = await self._request("GET", "/assets", params=params)
        return result or []  # type: ignore[return-value]
