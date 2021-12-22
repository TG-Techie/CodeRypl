# CodeRypl

[![black](https://github.com/TG-Techie/CodeRypl/actions/workflows/black.yml/badge.svg?branch=main)](https://github.com/TG-Techie/CodeRypl/actions/workflows/black.yml)
[![mypy](https://github.com/TG-Techie/CodeRypl/actions/workflows/mypy.yml/badge.svg?branch=main)](https://github.com/TG-Techie/CodeRypl/actions/workflows/mypy.yml)

A code-replacements graphical user interface to make editing replacements quick and easy

# meta-data:
- School
- Sport
- Sex
- Intended Season(s) (arbitrary user-input string) Ex: "2021-2022"

# coaches:
- turns the tbale in into a tabbed area
- 

# todo:
- add a backend to generate the exported file
- make the RplmFileModel class handle file io (excluding export)
- move the Table and event filer into it's own class to better segment the program
- add a way to enter the metadata? (school etc)
- save as a file outside of exporting to the text format
    - There is some discussion to be had over if .rplm files should be a thing
    - it means opening a file doesn't need to parse code replacements but can just load the interal represention
    - it also mean it could export to several format
    - If that funcationality is desired it could be performed with a different button/function
 
