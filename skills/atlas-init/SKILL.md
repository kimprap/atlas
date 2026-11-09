---
name: atlas-init
description: >
  Set up Atlas, the user's local store of web sources: its settings file and
  model roles. Use when an Atlas reply says Atlas is not set up or names
  `atlas-init`, or when the user asks to set up or configure Atlas.
---

# atlas-init

Setup is not built in this Atlas version; it arrives in Atlas build stage 2.

Tell the user that Atlas cannot be set up yet and that setup arrives in the next Atlas build stage. Write nothing: create or change no file under `~/.config/atlas/`, no host settings and no model roles. Done when the user has been told.
