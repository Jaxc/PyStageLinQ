"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""

from dataclasses import dataclass
import asyncio
from typing import Callable

from . import DataClasses, Token
from .MessageClasses import StageLinQServiceAnnouncement, StageLinQMessage
from .DataClasses import StageLinQServiceAnnouncementData
import json

prime_go = {
    "ClientLibrarianDevicesControllerCurrentDevice": "/Client/Librarian/DevicesController/CurrentDevice",
    "ClientLibrarianDevicesControllerHasSDCardConnected": "/Client/Librarian/DevicesController/HasSDCardConnected",
    "ClientLibrarianDevicesControllerHasUsbDeviceConnected": "/Client/Librarian/DevicesController/HasUsbDeviceConnected",
    "ClientPreferencesLayerB": "/Client/Preferences/LayerB",
    "ClientPreferencesPlayer": "/Client/Preferences/Player",
    "ClientPreferencesProfileApplicationPlayerColor1": "/Client/Preferences/Profile/Application/PlayerColor1",
    "ClientPreferencesProfileApplicationPlayerColor1A": "/Client/Preferences/Profile/Application/PlayerColor1A",
    "ClientPreferencesProfileApplicationPlayerColor1B": "/Client/Preferences/Profile/Application/PlayerColor1B",
    "ClientPreferencesProfileApplicationPlayerColor2": "/Client/Preferences/Profile/Application/PlayerColor2",
    "ClientPreferencesProfileApplicationPlayerColor2A": "/Client/Preferences/Profile/Application/PlayerColor2A",
    "ClientPreferencesProfileApplicationPlayerColor2B": "/Client/Preferences/Profile/Application/PlayerColor2B",
    "ClientPreferencesProfileApplicationPlayerColor3A": "/Client/Preferences/Profile/Application/PlayerColor3A",
    "ClientPreferencesProfileApplicationPlayerColor3B": "/Client/Preferences/Profile/Application/PlayerColor3B",
    "ClientPreferencesProfileApplicationPlayerColor4A": "/Client/Preferences/Profile/Application/PlayerColor4A",
    "ClientPreferencesProfileApplicationPlayerColor4B": "/Client/Preferences/Profile/Application/PlayerColor4B",
    "ClientPreferencesProfileApplicationSyncMode": "/Client/Preferences/Profile/Application/SyncMode",
    "EngineDeck1CurrentBPM": "/Engine/Deck1/CurrentBPM",
    "EngineDeck1ExternalMixerVolume": "/Engine/Deck1/ExternalMixerVolume",
    "EngineDeck1ExternalScratchWheelTouch": "/Engine/Deck1/ExternalScratchWheelTouch",
    "EngineDeck1PadsView": "/Engine/Deck1/Pads/View",
    "EngineDeck1Play": "/Engine/Deck1/Play",
    "EngineDeck1PlayState": "/Engine/Deck1/PlayState",
    "EngineDeck1Speed": "/Engine/Deck1/Speed",
    "EngineDeck1SpeedNeutral": "/Engine/Deck1/SpeedNeutral",
    "EngineDeck1SpeedOffsetDown": "/Engine/Deck1/SpeedOffsetDown",
    "EngineDeck1SpeedOffsetUp": "/Engine/Deck1/SpeedOffsetUp",
    "EngineDeck1SpeedRange": "/Engine/Deck1/SpeedRange",
    "EngineDeck1SpeedState": "/Engine/Deck1/SpeedState",
    "EngineDeck1SyncMode": "/Engine/Deck1/SyncMode",
    "EngineDeck1TrackArtistName": "/Engine/Deck1/Track/ArtistName",
    "EngineDeck1TrackBleep": "/Engine/Deck1/Track/Bleep",
    "EngineDeck1TrackCuePosition": "/Engine/Deck1/Track/CuePosition",
    "EngineDeck1TrackCurrentBPM": "/Engine/Deck1/Track/CurrentBPM",
    "EngineDeck1TrackCurrentKeyIndex": "/Engine/Deck1/Track/CurrentKeyIndex",
    "EngineDeck1TrackCurrentLoopInPosition": "/Engine/Deck1/Track/CurrentLoopInPosition",
    "EngineDeck1TrackCurrentLoopOutPosition": "/Engine/Deck1/Track/CurrentLoopOutPosition",
    "EngineDeck1TrackCurrentLoopSizeInBeats": "/Engine/Deck1/Track/CurrentLoopSizeInBeats",
    "EngineDeck1TrackKeyLock": "/Engine/Deck1/Track/KeyLock",
    "EngineDeck1TrackLoopEnableState": "/Engine/Deck1/Track/LoopEnableState",
    "EngineDeck1TrackLoopQuickLoop1": "/Engine/Deck1/Track/Loop/QuickLoop1",
    "EngineDeck1TrackLoopQuickLoop2": "/Engine/Deck1/Track/Loop/QuickLoop2",
    "EngineDeck1TrackLoopQuickLoop3": "/Engine/Deck1/Track/Loop/QuickLoop3",
    "EngineDeck1TrackLoopQuickLoop4": "/Engine/Deck1/Track/Loop/QuickLoop4",
    "EngineDeck1TrackLoopQuickLoop5": "/Engine/Deck1/Track/Loop/QuickLoop5",
    "EngineDeck1TrackLoopQuickLoop6": "/Engine/Deck1/Track/Loop/QuickLoop6",
    "EngineDeck1TrackLoopQuickLoop7": "/Engine/Deck1/Track/Loop/QuickLoop7",
    "EngineDeck1TrackLoopQuickLoop8": "/Engine/Deck1/Track/Loop/QuickLoop8",
    "EngineDeck1TrackPlayPauseLEDState": "/Engine/Deck1/Track/PlayPauseLEDState",
    "EngineDeck1TrackSampleRate": "/Engine/Deck1/Track/SampleRate",
    "EngineDeck1TrackSongAnalyzed": "/Engine/Deck1/Track/SongAnalyzed",
    "EngineDeck1TrackSongLoaded": "/Engine/Deck1/Track/SongLoaded",
    "EngineDeck1TrackSongName": "/Engine/Deck1/Track/SongName",
    "EngineDeck1TrackSoundSwitchGUID": "/Engine/Deck1/Track/SoundSwitchGuid",
    "EngineDeck1TrackTrackBytes": "/Engine/Deck1/Track/TrackBytes",
    "EngineDeck1TrackTrackData": "/Engine/Deck1/Track/TrackData",
    "EngineDeck1TrackTrackLength": "/Engine/Deck1/Track/TrackLength",
    "EngineDeck1TrackTrackName": "/Engine/Deck1/Track/TrackName",
    "EngineDeck1TrackTrackNetworkPath": "/Engine/Deck1/Track/TrackNetworkPath",
    "EngineDeck1TrackTrackURI": "/Engine/Deck1/Track/TrackUri",
    "EngineDeck1TrackTrackWasPlayed": "/Engine/Deck1/Track/TrackWasPlayed",
    "EngineDeck2CurrentBPM": "/Engine/Deck2/CurrentBPM",
    "EngineDeck2ExternalMixerVolume": "/Engine/Deck2/ExternalMixerVolume",
    "EngineDeck2ExternalScratchWheelTouch": "/Engine/Deck2/ExternalScratchWheelTouch",
    "EngineDeck2PadsView": "/Engine/Deck2/Pads/View",
    "EngineDeck2Play": "/Engine/Deck2/Play",
    "EngineDeck2PlayState": "/Engine/Deck2/PlayState",
    "EngineDeck2Speed": "/Engine/Deck2/Speed",
    "EngineDeck2SpeedNeutral": "/Engine/Deck2/SpeedNeutral",
    "EngineDeck2SpeedOffsetDown": "/Engine/Deck2/SpeedOffsetDown",
    "EngineDeck2SpeedOffsetUp": "/Engine/Deck2/SpeedOffsetUp",
    "EngineDeck2SpeedRange": "/Engine/Deck2/SpeedRange",
    "EngineDeck2SpeedState": "/Engine/Deck2/SpeedState",
    "EngineDeck2SyncMode": "/Engine/Deck2/SyncMode",
    "EngineDeck2TrackArtistName": "/Engine/Deck2/Track/ArtistName",
    "EngineDeck2TrackBleep": "/Engine/Deck2/Track/Bleep",
    "EngineDeck2TrackCuePosition": "/Engine/Deck2/Track/CuePosition",
    "EngineDeck2TrackCurrentBPM": "/Engine/Deck2/Track/CurrentBPM",
    "EngineDeck2TrackCurrentKeyIndex": "/Engine/Deck2/Track/CurrentKeyIndex",
    "EngineDeck2TrackCurrentLoopInPosition": "/Engine/Deck2/Track/CurrentLoopInPosition",
    "EngineDeck2TrackCurrentLoopOutPosition": "/Engine/Deck2/Track/CurrentLoopOutPosition",
    "EngineDeck2TrackCurrentLoopSizeInBeats": "/Engine/Deck2/Track/CurrentLoopSizeInBeats",
    "EngineDeck2TrackKeyLock": "/Engine/Deck2/Track/KeyLock",
    "EngineDeck2TrackLoopEnableState": "/Engine/Deck2/Track/LoopEnableState",
    "EngineDeck2TrackLoopQuickLoop1": "/Engine/Deck2/Track/Loop/QuickLoop1",
    "EngineDeck2TrackLoopQuickLoop2": "/Engine/Deck2/Track/Loop/QuickLoop2",
    "EngineDeck2TrackLoopQuickLoop3": "/Engine/Deck2/Track/Loop/QuickLoop3",
    "EngineDeck2TrackLoopQuickLoop4": "/Engine/Deck2/Track/Loop/QuickLoop4",
    "EngineDeck2TrackLoopQuickLoop5": "/Engine/Deck2/Track/Loop/QuickLoop5",
    "EngineDeck2TrackLoopQuickLoop6": "/Engine/Deck2/Track/Loop/QuickLoop6",
    "EngineDeck2TrackLoopQuickLoop7": "/Engine/Deck2/Track/Loop/QuickLoop7",
    "EngineDeck2TrackLoopQuickLoop8": "/Engine/Deck2/Track/Loop/QuickLoop8",
    "EngineDeck2TrackPlayPauseLEDState": "/Engine/Deck2/Track/PlayPauseLEDState",
    "EngineDeck2TrackSampleRate": "/Engine/Deck2/Track/SampleRate",
    "EngineDeck2TrackSongAnalyzed": "/Engine/Deck2/Track/SongAnalyzed",
    "EngineDeck2TrackSongLoaded": "/Engine/Deck2/Track/SongLoaded",
    "EngineDeck2TrackSongName": "/Engine/Deck2/Track/SongName",
    "EngineDeck2TrackSoundSwitchGUID": "/Engine/Deck2/Track/SoundSwitchGuid",
    "EngineDeck2TrackTrackBytes": "/Engine/Deck2/Track/TrackBytes",
    "EngineDeck2TrackTrackData": "/Engine/Deck2/Track/TrackData",
    "EngineDeck2TrackTrackLength": "/Engine/Deck2/Track/TrackLength",
    "EngineDeck2TrackTrackName": "/Engine/Deck2/Track/TrackName",
    "EngineDeck2TrackTrackNetworkPath": "/Engine/Deck2/Track/TrackNetworkPath",
    "EngineDeck2TrackTrackURI": "/Engine/Deck2/Track/TrackUri",
    "EngineDeck2TrackTrackWasPlayed": "/Engine/Deck2/Track/TrackWasPlayed",
    "EngineDeck3CurrentBPM" "EngineDeckCount": "/Engine/DeckCount",
    "MixerCH1faderPosition": "/Mixer/CH1faderPosition",
    "MixerCH2faderPosition": "/Mixer/CH2faderPosition",
    "MixerCH3faderPosition": "/Mixer/CH3faderPosition",
    "MixerCH4faderPosition": "/Mixer/CH4faderPosition",
    "MixerCrossfaderPosition": "/Mixer/CrossfaderPosition",
}

common_functions = {
    "ClientLibrarianDevicesControllerCurrentDevice": "/Client/Librarian/DevicesController/CurrentDevice",
    "ClientLibrarianDevicesControllerHasSDCardConnected": "/Client/Librarian/DevicesController/HasSDCardConnected",
    "ClientLibrarianDevicesControllerHasUsbDeviceConnected": "/Client/Librarian/DevicesController/HasUsbDeviceConnected",
    "ClientPreferencesLayerB": "/Client/Preferences/LayerB",
    "ClientPreferencesPlayer": "/Client/Preferences/Player",
    "ClientPreferencesProfileApplicationPlayerColor1": "/Client/Preferences/Profile/Application/PlayerColor1",
    "ClientPreferencesProfileApplicationPlayerColor1A": "/Client/Preferences/Profile/Application/PlayerColor1A",
    "ClientPreferencesProfileApplicationPlayerColor1B": "/Client/Preferences/Profile/Application/PlayerColor1B",
    "ClientPreferencesProfileApplicationPlayerColor2": "/Client/Preferences/Profile/Application/PlayerColor2",
    "ClientPreferencesProfileApplicationPlayerColor2A": "/Client/Preferences/Profile/Application/PlayerColor2A",
    "ClientPreferencesProfileApplicationPlayerColor2B": "/Client/Preferences/Profile/Application/PlayerColor2B",
    "ClientPreferencesProfileApplicationPlayerColor3": "/Client/Preferences/Profile/Application/PlayerColor3",
    "ClientPreferencesProfileApplicationPlayerColor3A": "/Client/Preferences/Profile/Application/PlayerColor3A",
    "ClientPreferencesProfileApplicationPlayerColor3B": "/Client/Preferences/Profile/Application/PlayerColor3B",
    "ClientPreferencesProfileApplicationPlayerColor4": "/Client/Preferences/Profile/Application/PlayerColor4",
    "ClientPreferencesProfileApplicationPlayerColor4A": "/Client/Preferences/Profile/Application/PlayerColor4A",
    "ClientPreferencesProfileApplicationPlayerColor4B": "/Client/Preferences/Profile/Application/PlayerColor4B",
    "ClientPreferencesProfileApplicationSyncMode": "/Client/Preferences/Profile/Application/SyncMode",
    "EngineDeck1CurrentBPM": "/Engine/Deck1/CurrentBPM",
    "EngineDeck1ExternalMixerVolume": "/Engine/Deck1/ExternalMixerVolume",
    "EngineDeck1ExternalScratchWheelTouch": "/Engine/Deck1/ExternalScratchWheelTouch",
    "EngineDeck1PadsView": "/Engine/Deck1/Pads/View",
    "EngineDeck1Play": "/Engine/Deck1/Play",
    "EngineDeck1PlayState": "/Engine/Deck1/PlayState",
    "EngineDeck1PlayStatePath": "/Engine/Deck1/PlayStatePath",
    "EngineDeck1Speed": "/Engine/Deck1/Speed",
    "EngineDeck1SpeedNeutral": "/Engine/Deck1/SpeedNeutral",
    "EngineDeck1SpeedOffsetDown": "/Engine/Deck1/SpeedOffsetDown",
    "EngineDeck1SpeedOffsetUp": "/Engine/Deck1/SpeedOffsetUp",
    "EngineDeck1SpeedRange": "/Engine/Deck1/SpeedRange",
    "EngineDeck1SpeedState": "/Engine/Deck1/SpeedState",
    "EngineDeck1SyncMode": "/Engine/Deck1/SyncMode",
    "EngineDeck1TrackArtistName": "/Engine/Deck1/Track/ArtistName",
    "EngineDeck1TrackBleep": "/Engine/Deck1/Track/Bleep",
    "EngineDeck1TrackCuePosition": "/Engine/Deck1/Track/CuePosition",
    "EngineDeck1TrackCurrentBPM": "/Engine/Deck1/Track/CurrentBPM",
    "EngineDeck1TrackCurrentKeyIndex": "/Engine/Deck1/Track/CurrentKeyIndex",
    "EngineDeck1TrackCurrentLoopInPosition": "/Engine/Deck1/Track/CurrentLoopInPosition",
    "EngineDeck1TrackCurrentLoopOutPosition": "/Engine/Deck1/Track/CurrentLoopOutPosition",
    "EngineDeck1TrackCurrentLoopSizeInBeats": "/Engine/Deck1/Track/CurrentLoopSizeInBeats",
    "EngineDeck1TrackKeyLock": "/Engine/Deck1/Track/KeyLock",
    "EngineDeck1TrackLoopEnableState": "/Engine/Deck1/Track/LoopEnableState",
    "EngineDeck1TrackLoopQuickLoop1": "/Engine/Deck1/Track/Loop/QuickLoop1",
    "EngineDeck1TrackLoopQuickLoop2": "/Engine/Deck1/Track/Loop/QuickLoop2",
    "EngineDeck1TrackLoopQuickLoop3": "/Engine/Deck1/Track/Loop/QuickLoop3",
    "EngineDeck1TrackLoopQuickLoop4": "/Engine/Deck1/Track/Loop/QuickLoop4",
    "EngineDeck1TrackLoopQuickLoop5": "/Engine/Deck1/Track/Loop/QuickLoop5",
    "EngineDeck1TrackLoopQuickLoop6": "/Engine/Deck1/Track/Loop/QuickLoop6",
    "EngineDeck1TrackLoopQuickLoop7": "/Engine/Deck1/Track/Loop/QuickLoop7",
    "EngineDeck1TrackLoopQuickLoop8": "/Engine/Deck1/Track/Loop/QuickLoop8",
    "EngineDeck1TrackPlayPauseLEDState": "/Engine/Deck1/Track/PlayPauseLEDState",
    "EngineDeck1TrackSampleRate": "/Engine/Deck1/Track/SampleRate",
    "EngineDeck1TrackSongAnalyzed": "/Engine/Deck1/Track/SongAnalyzed",
    "EngineDeck1TrackSongLoaded": "/Engine/Deck1/Track/SongLoaded",
    "EngineDeck1TrackSongName": "/Engine/Deck1/Track/SongName",
    "EngineDeck1TrackSoundSwitchGUID": "/Engine/Deck1/Track/SoundSwitchGuid",
    "EngineDeck1TrackTrackBytes": "/Engine/Deck1/Track/TrackBytes",
    "EngineDeck1TrackTrackData": "/Engine/Deck1/Track/TrackData",
    "EngineDeck1TrackTrackLength": "/Engine/Deck1/Track/TrackLength",
    "EngineDeck1TrackTrackName": "/Engine/Deck1/Track/TrackName",
    "EngineDeck1TrackTrackNetworkPath": "/Engine/Deck1/Track/TrackNetworkPath",
    "EngineDeck1TrackTrackURI": "/Engine/Deck1/Track/TrackUri",
    "EngineDeck1TrackTrackWasPlayed": "/Engine/Deck1/Track/TrackWasPlayed",
    "EngineDeck2CurrentBPM": "/Engine/Deck2/CurrentBPM",
    "EngineDeck2ExternalMixerVolume": "/Engine/Deck2/ExternalMixerVolume",
    "EngineDeck2ExternalScratchWheelTouch": "/Engine/Deck2/ExternalScratchWheelTouch",
    "EngineDeck2PadsView": "/Engine/Deck2/Pads/View",
    "EngineDeck2Play": "/Engine/Deck2/Play",
    "EngineDeck2PlayState": "/Engine/Deck2/PlayState",
    "EngineDeck2PlayStatePath": "/Engine/Deck2/PlayStatePath",
    "EngineDeck2Speed": "/Engine/Deck2/Speed",
    "EngineDeck2SpeedNeutral": "/Engine/Deck2/SpeedNeutral",
    "EngineDeck2SpeedOffsetDown": "/Engine/Deck2/SpeedOffsetDown",
    "EngineDeck2SpeedOffsetUp": "/Engine/Deck2/SpeedOffsetUp",
    "EngineDeck2SpeedRange": "/Engine/Deck2/SpeedRange",
    "EngineDeck2SpeedState": "/Engine/Deck2/SpeedState",
    "EngineDeck2SyncMode": "/Engine/Deck2/SyncMode",
    "EngineDeck2TrackArtistName": "/Engine/Deck2/Track/ArtistName",
    "EngineDeck2TrackBleep": "/Engine/Deck2/Track/Bleep",
    "EngineDeck2TrackCuePosition": "/Engine/Deck2/Track/CuePosition",
    "EngineDeck2TrackCurrentBPM": "/Engine/Deck2/Track/CurrentBPM",
    "EngineDeck2TrackCurrentKeyIndex": "/Engine/Deck2/Track/CurrentKeyIndex",
    "EngineDeck2TrackCurrentLoopInPosition": "/Engine/Deck2/Track/CurrentLoopInPosition",
    "EngineDeck2TrackCurrentLoopOutPosition": "/Engine/Deck2/Track/CurrentLoopOutPosition",
    "EngineDeck2TrackCurrentLoopSizeInBeats": "/Engine/Deck2/Track/CurrentLoopSizeInBeats",
    "EngineDeck2TrackKeyLock": "/Engine/Deck2/Track/KeyLock",
    "EngineDeck2TrackLoopEnableState": "/Engine/Deck2/Track/LoopEnableState",
    "EngineDeck2TrackLoopQuickLoop1": "/Engine/Deck2/Track/Loop/QuickLoop1",
    "EngineDeck2TrackLoopQuickLoop2": "/Engine/Deck2/Track/Loop/QuickLoop2",
    "EngineDeck2TrackLoopQuickLoop3": "/Engine/Deck2/Track/Loop/QuickLoop3",
    "EngineDeck2TrackLoopQuickLoop4": "/Engine/Deck2/Track/Loop/QuickLoop4",
    "EngineDeck2TrackLoopQuickLoop5": "/Engine/Deck2/Track/Loop/QuickLoop5",
    "EngineDeck2TrackLoopQuickLoop6": "/Engine/Deck2/Track/Loop/QuickLoop6",
    "EngineDeck2TrackLoopQuickLoop7": "/Engine/Deck2/Track/Loop/QuickLoop7",
    "EngineDeck2TrackLoopQuickLoop8": "/Engine/Deck2/Track/Loop/QuickLoop8",
    "EngineDeck2TrackPlayPauseLEDState": "/Engine/Deck2/Track/PlayPauseLEDState",
    "EngineDeck2TrackSampleRate": "/Engine/Deck2/Track/SampleRate",
    "EngineDeck2TrackSongAnalyzed": "/Engine/Deck2/Track/SongAnalyzed",
    "EngineDeck2TrackSongLoaded": "/Engine/Deck2/Track/SongLoaded",
    "EngineDeck2TrackSongName": "/Engine/Deck2/Track/SongName",
    "EngineDeck2TrackSoundSwitchGUID": "/Engine/Deck2/Track/SoundSwitchGuid",
    "EngineDeck2TrackTrackBytes": "/Engine/Deck2/Track/TrackBytes",
    "EngineDeck2TrackTrackData": "/Engine/Deck2/Track/TrackData",
    "EngineDeck2TrackTrackLength": "/Engine/Deck2/Track/TrackLength",
    "EngineDeck2TrackTrackName": "/Engine/Deck2/Track/TrackName",
    "EngineDeck2TrackTrackNetworkPath": "/Engine/Deck2/Track/TrackNetworkPath",
    "EngineDeck2TrackTrackURI": "/Engine/Deck2/Track/TrackUri",
    "EngineDeck2TrackTrackWasPlayed": "/Engine/Deck2/Track/TrackWasPlayed",
    "EngineDeck3CurrentBPM": "/Engine/Deck3/CurrentBPM",
    "EngineDeck3ExternalMixerVolume": "/Engine/Deck3/ExternalMixerVolume",
    "EngineDeck3ExternalScratchWheelTouch": "/Engine/Deck3/ExternalScratchWheelTouch",
    "EngineDeck3PadsView": "/Engine/Deck3/Pads/View",
    "EngineDeck3Play": "/Engine/Deck3/Play",
    "EngineDeck3PlayState": "/Engine/Deck3/PlayState",
    "EngineDeck3PlayStatePath": "/Engine/Deck3/PlayStatePath",
    "EngineDeck3Speed": "/Engine/Deck3/Speed",
    "EngineDeck3SpeedNeutral": "/Engine/Deck3/SpeedNeutral",
    "EngineDeck3SpeedOffsetDown": "/Engine/Deck3/SpeedOffsetDown",
    "EngineDeck3SpeedOffsetUp": "/Engine/Deck3/SpeedOffsetUp",
    "EngineDeck3SpeedRange": "/Engine/Deck3/SpeedRange",
    "EngineDeck3SpeedState": "/Engine/Deck3/SpeedState",
    "EngineDeck3SyncMode": "/Engine/Deck3/SyncMode",
    "EngineDeck3TrackArtistName": "/Engine/Deck3/Track/ArtistName",
    "EngineDeck3TrackBleep": "/Engine/Deck3/Track/Bleep",
    "EngineDeck3TrackCuePosition": "/Engine/Deck3/Track/CuePosition",
    "EngineDeck3TrackCurrentBPM": "/Engine/Deck3/Track/CurrentBPM",
    "EngineDeck3TrackCurrentKeyIndex": "/Engine/Deck3/Track/CurrentKeyIndex",
    "EngineDeck3TrackCurrentLoopInPosition": "/Engine/Deck3/Track/CurrentLoopInPosition",
    "EngineDeck3TrackCurrentLoopOutPosition": "/Engine/Deck3/Track/CurrentLoopOutPosition",
    "EngineDeck3TrackCurrentLoopSizeInBeats": "/Engine/Deck3/Track/CurrentLoopSizeInBeats",
    "EngineDeck3TrackKeyLock": "/Engine/Deck3/Track/KeyLock",
    "EngineDeck3TrackLoopEnableState": "/Engine/Deck3/Track/LoopEnableState",
    "EngineDeck3TrackLoopQuickLoop1": "/Engine/Deck3/Track/Loop/QuickLoop1",
    "EngineDeck3TrackLoopQuickLoop2": "/Engine/Deck3/Track/Loop/QuickLoop2",
    "EngineDeck3TrackLoopQuickLoop3": "/Engine/Deck3/Track/Loop/QuickLoop3",
    "EngineDeck3TrackLoopQuickLoop4": "/Engine/Deck3/Track/Loop/QuickLoop4",
    "EngineDeck3TrackLoopQuickLoop5": "/Engine/Deck3/Track/Loop/QuickLoop5",
    "EngineDeck3TrackLoopQuickLoop6": "/Engine/Deck3/Track/Loop/QuickLoop6",
    "EngineDeck3TrackLoopQuickLoop7": "/Engine/Deck3/Track/Loop/QuickLoop7",
    "EngineDeck3TrackLoopQuickLoop8": "/Engine/Deck3/Track/Loop/QuickLoop8",
    "EngineDeck3TrackPlayPauseLEDState": "/Engine/Deck3/Track/PlayPauseLEDState",
    "EngineDeck3TrackSampleRate": "/Engine/Deck3/Track/SampleRate",
    "EngineDeck3TrackSongAnalyzed": "/Engine/Deck3/Track/SongAnalyzed",
    "EngineDeck3TrackSongLoaded": "/Engine/Deck3/Track/SongLoaded",
    "EngineDeck3TrackSongName": "/Engine/Deck3/Track/SongName",
    "EngineDeck3TrackSoundSwitchGUID": "/Engine/Deck3/Track/SoundSwitchGuid",
    "EngineDeck3TrackTrackBytes": "/Engine/Deck3/Track/TrackBytes",
    "EngineDeck3TrackTrackData": "/Engine/Deck3/Track/TrackData",
    "EngineDeck3TrackTrackLength": "/Engine/Deck3/Track/TrackLength",
    "EngineDeck3TrackTrackName": "/Engine/Deck3/Track/TrackName",
    "EngineDeck3TrackTrackNetworkPath": "/Engine/Deck3/Track/TrackNetworkPath",
    "EngineDeck3TrackTrackURI": "/Engine/Deck3/Track/TrackUri",
    "EngineDeck3TrackTrackWasPlayed": "/Engine/Deck3/Track/TrackWasPlayed",
    "EngineDeck4CurrentBPM": "/Engine/Deck4/CurrentBPM",
    "EngineDeck4ExternalMixerVolume": "/Engine/Deck4/ExternalMixerVolume",
    "EngineDeck4ExternalScratchWheelTouch": "/Engine/Deck4/ExternalScratchWheelTouch",
    "EngineDeck4PadsView": "/Engine/Deck4/Pads/View",
    "EngineDeck4Play": "/Engine/Deck4/Play",
    "EngineDeck4PlayState": "/Engine/Deck4/PlayState",
    "EngineDeck4PlayStatePath": "/Engine/Deck4/PlayStatePath",
    "EngineDeck4Speed": "/Engine/Deck4/Speed",
    "EngineDeck4SpeedNeutral": "/Engine/Deck4/SpeedNeutral",
    "EngineDeck4SpeedOffsetDown": "/Engine/Deck4/SpeedOffsetDown",
    "EngineDeck4SpeedOffsetUp": "/Engine/Deck4/SpeedOffsetUp",
    "EngineDeck4SpeedRange": "/Engine/Deck4/SpeedRange",
    "EngineDeck4SpeedState": "/Engine/Deck4/SpeedState",
    "EngineDeck4SyncMode": "/Engine/Deck4/SyncMode",
    "EngineDeck4TrackArtistName": "/Engine/Deck4/Track/ArtistName",
    "EngineDeck4TrackBleep": "/Engine/Deck4/Track/Bleep",
    "EngineDeck4TrackCuePosition": "/Engine/Deck4/Track/CuePosition",
    "EngineDeck4TrackCurrentBPM": "/Engine/Deck4/Track/CurrentBPM",
    "EngineDeck4TrackCurrentKeyIndex": "/Engine/Deck4/Track/CurrentKeyIndex",
    "EngineDeck4TrackCurrentLoopInPosition": "/Engine/Deck4/Track/CurrentLoopInPosition",
    "EngineDeck4TrackCurrentLoopOutPosition": "/Engine/Deck4/Track/CurrentLoopOutPosition",
    "EngineDeck4TrackCurrentLoopSizeInBeats": "/Engine/Deck4/Track/CurrentLoopSizeInBeats",
    "EngineDeck4TrackKeyLock": "/Engine/Deck4/Track/KeyLock",
    "EngineDeck4TrackLoopEnableState": "/Engine/Deck4/Track/LoopEnableState",
    "EngineDeck4TrackLoopQuickLoop1": "/Engine/Deck4/Track/Loop/QuickLoop1",
    "EngineDeck4TrackLoopQuickLoop2": "/Engine/Deck4/Track/Loop/QuickLoop2",
    "EngineDeck4TrackLoopQuickLoop3": "/Engine/Deck4/Track/Loop/QuickLoop3",
    "EngineDeck4TrackLoopQuickLoop4": "/Engine/Deck4/Track/Loop/QuickLoop4",
    "EngineDeck4TrackLoopQuickLoop5": "/Engine/Deck4/Track/Loop/QuickLoop5",
    "EngineDeck4TrackLoopQuickLoop6": "/Engine/Deck4/Track/Loop/QuickLoop6",
    "EngineDeck4TrackLoopQuickLoop7": "/Engine/Deck4/Track/Loop/QuickLoop7",
    "EngineDeck4TrackLoopQuickLoop8": "/Engine/Deck4/Track/Loop/QuickLoop8",
    "EngineDeck4TrackPlayPauseLEDState": "/Engine/Deck4/Track/PlayPauseLEDState",
    "EngineDeck4TrackSampleRate": "/Engine/Deck4/Track/SampleRate",
    "EngineDeck4TrackSongAnalyzed": "/Engine/Deck4/Track/SongAnalyzed",
    "EngineDeck4TrackSongLoaded": "/Engine/Deck4/Track/SongLoaded",
    "EngineDeck4TrackSongName": "/Engine/Deck4/Track/SongName",
    "EngineDeck4TrackSoundSwitchGUID": "/Engine/Deck4/Track/SoundSwitchGuid",
    "EngineDeck4TrackTrackBytes": "/Engine/Deck4/Track/TrackBytes",
    "EngineDeck4TrackTrackData": "/Engine/Deck4/Track/TrackData",
    "EngineDeck4TrackTrackLength": "/Engine/Deck4/Track/TrackLength",
    "EngineDeck4TrackTrackName": "/Engine/Deck4/Track/TrackName",
    "EngineDeck4TrackTrackNetworkPath": "/Engine/Deck4/Track/TrackNetworkPath",
    "EngineDeck4TrackTrackURI": "/Engine/Deck4/Track/TrackUri",
    "EngineDeck4TrackTrackWasPlayed": "/Engine/Deck4/Track/TrackWasPlayed",
    "EngineDeckCount": "/Engine/DeckCount",
    "GUIDecksDeckActiveDeck": "/GUI/Decks/Deck/ActiveDeck",
    "GUIViewLayerLayerB": "/GUI/ViewLayer/LayerB",
    "MixerCH1faderPosition": "/Mixer/CH1faderPosition",
    "MixerCH2faderPosition": "/Mixer/CH2faderPosition",
    "MixerCH3faderPosition": "/Mixer/CH3faderPosition",
    "MixerCH4faderPosition": "/Mixer/CH4faderPosition",
    "MixerCrossfaderPosition": "/Mixer/CrossfaderPosition",
}


@dataclass
class ServiceHandle:
    device: str
    ip: str
    service: str
    port: int


class StateMapSubscription:
    def __init__(
        self,
        service_handle: ServiceHandle,
        subscription_list: dict,
        data_callback: Callable[[list[DataClasses.StageLinQStateMapData]], None],
    ) -> None:
        self.service_handle: ServiceHandle = service_handle
        self._callback = data_callback
        self._subscription_list = subscription_list
        self.reader = None
        self.writer = None
        self.state_map_task = None

    def get_task(self) -> asyncio.Task:
        return self.state_map_task

    async def read_state_map(self) -> None:
        trailing_data = bytearray()
        while True:
            frame = await self.read_frame(trailing_data)

            if len(frame) == 0:
                return

            blocks, trailing_data = self.decode_frame(frame)

            self.handle_data(blocks)

    def decode_frame(self, frame: bytes) -> [list[bytes], bytearray]:
        blocks = self.decode_multi_block(frame)
        trailing_data = bytearray()
        if len(blocks[-1]) < 4:
            trailing_data = blocks.pop()
        elif len(blocks[-1]) != int.from_bytes(blocks[-1][0:4], byteorder="big") + 4:
            # Last block not completely received
            trailing_data = blocks.pop()
        return blocks, trailing_data

    def handle_data(self, blocks: list[bytes]) -> None:
        received_fields = []
        verify_error = None
        for block in blocks:
            try:
                received_fields.append(self.verify_block(block))

            except RuntimeError as err:
                # block corrupted, send error to callback if it exists
                received_fields = err
                verify_error = err
                break

        if self._callback is not None:
            self._callback(received_fields)
        else:
            # To avoid failing silently, the error is reraised if no callback has been defined.
            if verify_error is not None:
                raise verify_error from None

    async def read_frame(self, trailing_data) -> bytes:
        # Massive buffer because I have not figured out how to handle messages over multiple buffers
        frame = await self.reader.read(8192 * 4)
        # Add data from last received frame
        frame = trailing_data + frame
        return frame

    @staticmethod
    def decode_multi_block(frame: bytes) -> list[bytes]:
        blocks = []
        while len(frame) > 4:
            block_len = int.from_bytes(frame[0:4], byteorder="big") + 4
            blocks.append(frame[0:block_len])
            frame = frame[block_len:]

        if len(frame) > 0:
            # Frame not completely received, appending trailing block
            blocks.append(frame)

        return blocks

    @staticmethod
    def verify_block(block: bytes) -> DataClasses.StageLinQStateMapData:
        if len(block) < 4:
            raise RuntimeError("Block is to short to contain length")

        block_length = int.from_bytes(block[0:4], byteorder="big")

        if block_length == 0:
            # No data in the block, this most likely is due to other problem, or will cause problems later.
            return

        # Note: -4 is needed as block_length does not include its own length.
        if len(block) - 4 != block_length:
            raise RuntimeError(
                "Block invalid: Block length inconsistent with its header"
            )

        magic_flag = block[4:8].decode()

        if magic_flag != "smaa":
            raise RuntimeError("Block invalid: Could not find magic flag")

        # magic_flag2 is not checked as I have no idea what it is, it is all 0's for my PrimeGo, but it seems to be
        # different in the Go implementation
        magic_flag2 = block[8:12]

        path_len = int.from_bytes(block[12:16], byteorder="big")
        value_len_offset = 16 + path_len
        path = block[16:value_len_offset].decode(encoding="UTF-16be")

        value_offset = value_len_offset + 4
        value_len = int.from_bytes(
            block[value_len_offset:value_offset], byteorder="big"
        )

        value = json.loads(
            block[value_offset : value_offset + value_len].decode(encoding="UTF-16be")
        )

        return DataClasses.StageLinQStateMapData(
            block_length, magic_flag, magic_flag2, path_len, path, value_len, value
        )

    async def subscribe(self, own_token: Token.StageLinQToken) -> None:
        self.reader, self.writer = await asyncio.open_connection(
            self.service_handle.ip, self.service_handle.port
        )
        self.writer.write(
            StageLinQServiceAnnouncement().encode_frame(
                StageLinQServiceAnnouncementData(
                    Token=own_token,
                    Service=self.service_handle.service,
                    Port=self.writer.transport.get_extra_info("sockname")[1],
                )
            )
        )
        await self.writer.drain()

        self.state_map_task = asyncio.create_task(self.read_state_map())

        await self._send_subscription_requests()

    async def _send_subscription_requests(self):
        for service in self._subscription_list.values():
            msg = (len(service) * 2 + 8 * 2).to_bytes(4, byteorder="big")
            msg += bytearray([0x73, 0x6D, 0x61, 0x61])
            msg += bytearray([0x00, 0x00, 0x07, 0xD2])
            msg += StageLinQMessage().write_network_string(service)
            msg += (0).to_bytes(4, byteorder="big")
            self.writer.write(msg)
            await self.writer.drain()
        # small sleep to actually send frame
        await asyncio.sleep(0.001)
