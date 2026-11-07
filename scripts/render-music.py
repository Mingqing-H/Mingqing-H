"""Render the original MQ FM ambient loop as a small mono PCM track."""

from array import array
from math import exp, pi, sin, tanh
from pathlib import Path
import sys
import wave


RATE = 22050
BEAT = 2 / 3
BAR = 4 * BEAT
CHORDS = ((50, 57, 61, 64, 66), (45, 57, 59, 61, 64),
          (42, 54, 57, 61, 64), (40, 52, 54, 59, 64))
MELODY = ((73, 76, 78), (76, 73, 71), (69, 73, 76), (71, 78, 76),
          (73, 81, 78), (76, 71, 69), (73, 76, 81), (78, 76, 71))
LENGTH = round(RATE * BAR * len(MELODY))
mix = array("f", [0.0]) * LENGTH


def add_note(note, start, duration, volume, pad=False):
    start = round(start * RATE)
    angular = 2 * pi * 440 * 2 ** ((note - 69) / 12)
    for i in range(round(duration * RATE)):
        t = i / RATE
        phase = angular * t
        if pad:
            envelope = min(1, t / .64, (duration - t) / .82)
            sound = sin(phase) + .17 * sin(2 * phase) + .19 * sin(phase * 1.0025)
        else:
            envelope = min(1, t / .035, (duration - t) / .22) * exp(-2.7 * t)
            sound = sin(phase) + .24 * sin(2.01 * phase) + .12 * sin(3.01 * phase)
        mix[(start + i) % LENGTH] += volume * envelope * sound


for bar, melody in enumerate(MELODY):
    start = bar * BAR
    chord = CHORDS[bar % len(CHORDS)]
    for index, note in enumerate(chord):
        add_note(note, start - .32 + .08 * index, BAR + .68, .10 if index == 0 else .046, pad=True)
    for beat, note in zip((.50, 1.75, 3.10), melody):
        onset = start + beat * BEAT
        add_note(note, onset, 1.42, .22)
        add_note(note, onset + .38, 1.15, .055)

samples = array("h", (round(30000 * tanh(sample)) for sample in mix))
if sys.byteorder == "big":
    samples.byteswap()
target = Path(__file__).resolve().parents[1] / "docs" / "night-flight.wav"
with wave.open(str(target), "wb") as audio:
    audio.setparams((1, 2, RATE, len(samples), "NONE", "not compressed"))
    audio.writeframes(samples.tobytes())
print(f"{target.name}: {len(samples) / RATE:.2f} seconds, {target.stat().st_size:,} bytes")
