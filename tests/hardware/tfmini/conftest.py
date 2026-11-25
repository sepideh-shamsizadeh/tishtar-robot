"""Pytest configuration for TFmini hardware tests.

Scripts that talk to the physical sensor are excluded from automatic test
discovery so that running ``pytest`` never opens a serial port. Only the
hardware-independent ``test_tfmini_*.py`` unit tests are collected.
"""

# test_tfmini.py matches pytest's default pattern but is a hardware script.
collect_ignore = ["test_tfmini.py"]
