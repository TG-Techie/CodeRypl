# CodeRypl

[![black](https://github.com/TG-Techie/CodeRypl/actions/workflows/black.yml/badge.svg?branch=main)](https://github.com/TG-Techie/CodeRypl/actions/workflows/black.yml)
[![mypy](https://github.com/TG-Techie/CodeRypl/actions/workflows/mypy.yml/badge.svg?branch=main)](https://github.com/TG-Techie/CodeRypl/actions/workflows/mypy.yml)

A code-replacements graphical user interface to make editing replacements quick and easy

# TODO for later review:

- make the meta data fields auto normalize on enter
- ie add methods to the renderer that normalize the raw into to a nicer on. this would be for sport, category, and year
  EX: `Man`, `m`, `Male` -> `Mens` or soemthing like that
- add a hash of file contents on save and expose it as `model.are_unsaved_changes()` for prompting to save on / etc (maybe even expose via gui)
