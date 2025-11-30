# ... (imports and STEP_USER_DATA_SCHEMA remain the same) ...

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # *** CRITICAL FIX: Strip whitespace from inputs ***
    username = data["username"].strip()
    raw_api_key = data.get("api_key", "").strip() # Ensure it's treated as string and stripped

    # --- TROUBLESHOOTING CHECKPOINT ---
    # We will log the length of the key to see if any unexpected characters are present.
    _LOGGER.info("Attempting validation for user: %s (API key length: %d)", username, len(raw_api_key))


    headers = {}
    # Use the cleaned key for the check
    if raw_api_key and raw_api_key.lower() != "none":
        # 1. Use the standard custom API key header (X-API-Key)
        headers["X-API-Key"] = raw_api_key

        # 2. **If the fix above fails, UNCOMMENT the line below and try 'Authorization'**
        # headers["Authorization"] = f"Bearer {raw_api_key}"


    # Test the credentials by making a request to the lookup endpoint
    test_url = API_LOOKUP_URL.format(username)
    
    try:
        # We must set a timeout here, especially for a validation step
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(test_url) as response:
                
                # Check for 404 first
                if response.status == 404:
                    _LOGGER.warning("User not found: %s", username)
                    raise InvalidAuth("user_not_found")
                
                response.raise_for_status() # Raises for 4xx/5xx status codes (e.g., 401 Unauthorized)

                data = await response.json()
                
                if not data or not data.get("uuid"):
                    raise InvalidAuth("user_not_found") 

    except aiohttp.ClientConnectorError as err:
        _LOGGER.error("Connection error: %s", err)
        raise CannotConnect from err
    except aiohttp.ClientResponseError as err:
        _LOGGER.error("API response error (status %s) for user %s: %s", err.status, username, err)
        if err.status == 401:
            raise InvalidAuth("invalid_api_key")
        # Handle other 4xx/5xx errors
        raise InvalidAuth("unknown_api_error") from err
    except InvalidAuth:
        # Re-raise explicit InvalidAuth exceptions
        raise
    except Exception as err:
        _LOGGER.error("An unexpected error occurred during validation: %s", err)
        raise InvalidAuth("unknown_api_error") from err

    # Return info that you want to store in the config entry.
    return {"title": f"Donut SMP: {username}", "uuid": data["uuid"]}

# ... (ConfigFlow class and Exception classes remain the same) ...
