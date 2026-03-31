import os
import sys
from unittest.mock import MagicMock, patch

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


def test_validate_config_valid():
    """validate_config returns None when all Twitter keys are present."""
    from scripts.platforms.twitter import validate_config

    config = {
        "twitter": {
            "api_key": "key",
            "api_secret": "secret",
            "access_token": "token",
            "access_secret": "asecret",
        }
    }
    assert validate_config(config) is None


def test_validate_config_missing_section():
    """validate_config returns error when twitter section is missing."""
    from scripts.platforms.twitter import validate_config

    assert validate_config({}) is not None
    assert "twitter" in validate_config({}).lower()


def test_validate_config_missing_key():
    """validate_config returns error when a key is empty."""
    from scripts.platforms.twitter import validate_config

    config = {
        "twitter": {
            "api_key": "key",
            "api_secret": "",
            "access_token": "token",
            "access_secret": "asecret",
        }
    }
    error = validate_config(config)
    assert error is not None
    assert "api_secret" in error


@patch("scripts.platforms.twitter.tweepy")
def test_post_single_tweet(mock_tweepy):
    """post() with a single content part posts one tweet."""
    from scripts.platforms.twitter import post

    mock_client = MagicMock()
    mock_client.create_tweet.return_value = MagicMock(
        data={"id": "111", "text": "Hello world"}
    )
    mock_tweepy.Client.return_value = mock_client

    config = {
        "twitter": {
            "api_key": "k",
            "api_secret": "s",
            "access_token": "t",
            "access_secret": "a",
        }
    }
    result = post(config, ["Hello world"])
    assert result["success"] is True
    assert result["post_ids"] == ["111"]
    mock_client.create_tweet.assert_called_once_with(text="Hello world")


@patch("scripts.platforms.twitter.tweepy")
def test_post_thread(mock_tweepy):
    """post() with multiple content parts posts a thread (each reply to previous)."""
    from scripts.platforms.twitter import post

    mock_client = MagicMock()
    mock_client.create_tweet.side_effect = [
        MagicMock(data={"id": "111", "text": "First"}),
        MagicMock(data={"id": "222", "text": "Second"}),
    ]
    mock_tweepy.Client.return_value = mock_client

    config = {
        "twitter": {
            "api_key": "k",
            "api_secret": "s",
            "access_token": "t",
            "access_secret": "a",
        }
    }
    result = post(config, ["First", "Second"])
    assert result["success"] is True
    assert result["post_ids"] == ["111", "222"]
    # Second tweet should reply to first
    calls = mock_client.create_tweet.call_args_list
    assert calls[1][1]["in_reply_to_tweet_id"] == "111"


@patch("scripts.platforms.twitter.tweepy")
def test_post_with_images(mock_tweepy):
    """post() uploads images via v1.1 API and attaches media IDs."""
    from scripts.platforms.twitter import post

    mock_client = MagicMock()
    mock_client.create_tweet.return_value = MagicMock(
        data={"id": "111", "text": "With image"}
    )
    mock_tweepy.Client.return_value = mock_client

    mock_api_v1 = MagicMock()
    mock_media = MagicMock()
    mock_media.media_id = 999
    mock_api_v1.media_upload.return_value = mock_media
    mock_tweepy.OAuth1UserHandler.return_value = MagicMock()
    mock_tweepy.API.return_value = mock_api_v1

    config = {
        "twitter": {
            "api_key": "k",
            "api_secret": "s",
            "access_token": "t",
            "access_secret": "a",
        }
    }
    result = post(config, ["With image"], images=["/path/to/img.png"])
    assert result["success"] is True
    mock_api_v1.media_upload.assert_called_once_with("/path/to/img.png")
    call_kwargs = mock_client.create_tweet.call_args[1]
    assert call_kwargs["media_ids"] == [999]
