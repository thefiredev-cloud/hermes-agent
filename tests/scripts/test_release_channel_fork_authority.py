"""published_channel_identity under a shared channel store.

The protected channel objects live in one store and name the repository that published them. A fork reads
the same objects, so the record's authority differs from the reader's repository. That case used to raise
"Channel repository authority mismatch" and fail the daily canary before it could cut a tag; it now resolves
under the record's own repository.
"""
from __future__ import annotations

import json

import pytest

from hermes_cli.release_channels import ChannelError, ChannelNotFound, channel_key
from scripts.releases.versioning import published_channel_identity

FORK = "thefiredev-cloud/hermes-agent"
OWNER = "NousResearch/hermes-agent"


def record(repository: str, version: str = "0.22.0", channel: str = "stable") -> dict:
    return {
        "name": channel,
        "repository": repository,
        "policy": f"{channel}-release",
        "state": "active",
        "revision": 7,
        "nextSequence": 9,
        "identity": {"version": version, "commit": "a" * 40},
        "head": None,
    }


class StubReader:
    """Serves one channel record and enforces the repository authority check the HTTP reader applies."""

    objects: dict = {}
    reads: list = []

    def __init__(self, base_url, repository=None):
        self.repository = repository

    def read_bytes(self, key: str) -> bytes:
        type(self).reads.append((self.repository, key))
        if key not in type(self).objects:
            raise ChannelNotFound(f"Channel object not found: {key}")
        return type(self).objects[key]

    def resolve(self, channel: str):
        body = json.loads(self.read_bytes(channel_key(channel)))
        if self.repository is not None and body["repository"].casefold() != self.repository.casefold():
            raise ChannelError("Channel repository authority mismatch")

        class Resolved:
            manifest = {"request": {"version": body["identity"]["version"], "commit": body["identity"]["commit"]}}
            terminal = {"policy": body["policy"]}

        return Resolved()


@pytest.fixture(autouse=True)
def clean():
    StubReader.objects = {}
    StubReader.reads = []


def test_foreign_channel_resolves_under_its_own_repository():
    StubReader.objects[channel_key("stable")] = json.dumps(record(OWNER)).encode()
    assert published_channel_identity(FORK, "stable", base_url="http://stub", reader_type=StubReader) == (
        "0.22.0",
        "a" * 40,
    )
    assert (OWNER, channel_key("stable")) in StubReader.reads, "it retries under the record's own repository"


def test_same_repository_reads_once():
    StubReader.objects[channel_key("stable")] = json.dumps(record(FORK)).encode()
    assert published_channel_identity(FORK, "stable", base_url="http://stub", reader_type=StubReader)[0] == "0.22.0"
    assert [r for r in StubReader.reads if r[1] == channel_key("stable")] == [(FORK, channel_key("stable"))]


def test_missing_channel_is_none():
    assert published_channel_identity(FORK, "canary", base_url="http://stub", reader_type=StubReader) is None


def test_other_channel_errors_still_raise():
    StubReader.objects[channel_key("stable")] = json.dumps(record(OWNER, channel="canary")).encode()
    with pytest.raises(ValueError):
        published_channel_identity(FORK, "stable", base_url="http://stub", reader_type=StubReader)
