# OPLA

[![DOI](https://zenodo.org/badge/1206993619.svg)](https://doi.org/10.5281/zenodo.20849881)


This tool allows users to create easy & fast Life Cycle Assessments (LCA) based on imported datasets. Users can define materials, processes, and end-of-life (EOL) scenarios, and the tool provides LCA results such as midpoints, endpoints, and contribution analyses.

It is designed to run in any browser, completely offline, from a single HTML file.

## Important note

EcoInvent datasets are proprietary licensed and cannot be provided within this open-source project. Therefor this repository serves as a tool for processing and analyzing datasets but does not include any datasets by default. 

To use this tool, you will need to supply your own datasets. Refer to the [Generating datasets](#generating-datasets) section below for instructions on how to provide and integrate the required datasets.

## Features

- Import datasets from any source via a custom JSON format
- Define custom materials, processes, and EOL scenarios
- Perform detailed Life Cycle Assessments (LCA)
- Generate midpoints, endpoints, and contribution analyses
- Run entirely offline in any modern browser
- Export results for further analysis or reporting
- User-friendly interface for quick assessments

# Generating datasets

To generate datasets in the format of the tool, you have two options:

1. **Using the `export-adapter` script**
    Use the `export-adapter` script to convert an export from EcoInvent into the custom JSON format required by the tool. This script automates the transformation process, ensuring compatibility with the tool.

2. **Manually creating a custom JSON file**
    Alternatively, you can create the custom JSON formatted file manually. This method allows you to use any source or approach to generate the dataset, as long as it adheres to the required JSON format. To assist you, we provide some template datasets in the `datasets-templates` folder located at the root of the repository. You can use these templates as a reference or starting point for creating your own datasets.

# Overwrite folder

All the data you want to add should go into an `overwrite` folder at the root of the repository and follow this format:

```
Overwrite
└── datasets
    └──***.js
    └──***.js
└── js-files
    └──***.js
    └──***.js
└── parametrized-scripts
    └── ***.js
    └── ***.js
```

## Datasets

The folder `./overwrite/datasets` allow you to add all the datasets via `.js` file, you could for example add the material endpoints dataset by adding a `.js` file containing

```javascript
window.MATERIALS_ENDPOINTS = [...]
```

Feel free to check the folder `./datasets-templates` to see some examples of content.

## Parametrized Scripts

Parametrizable materials work as materials with "params", you need two things to make them work:

 - A list of params (ie: name, type, condition, default value, etc..)
 - A `.js` script that take these params in input and output a list of internal requirements from the datasets

You can define new parametrizable material by overwriting the list of choice `window.PARAMETRIZABLE_MATERIALS_DATABASE` and by adding you custom scripts into the folder `./overwrite/parametrized-scripts`. Feel free to check the `parametrized-process-modules` folder to see some available parametrized processes.

## JS Files

You can use the `./overwrite/js-files` folder to add any `.js` file you want/need. It allow you to add custom logic into the system, for example to redefine `window.PARAMETRIZABLE_MATERIALS_DATABASE` with your own list.

Feel free to use this subfolder as you want, as soon as you know what you are editing.

# How to release a new version

To create a new release, you can use the automated script like this: `./compile-release.sh [VERSION]`

Example: `./compile-release.sh 1.0.0`

You should get a new `./dist/index.html` file, with everything embedded.

# Running the tests

The comparison mode (Results Comparator) is covered by a browser test in `tests/compare/`. It opens the built `dist/opla.html` in headless Chromium and follows the same flow as a user: it builds a project in OPLA, downloads it with **Export project** (`lca_study.json`), drops exported project files on the comparison mode, checks the numbers, exercises every view (scrolling, hiding candidates, sessions, exports) and saves screenshots to `tests/compare/shots/`.

## 1. Install the requirements (once)

You need Python 3 and Playwright with its Chromium build:

```bash
python3 -m venv tests/.venv
tests/.venv/bin/pip install playwright
tests/.venv/bin/playwright install chromium
```

To use a Chromium already installed on your machine instead, skip the last command and set `CHROMIUM_PATH` when running the test (for example `CHROMIUM_PATH=/usr/bin/chromium`).

## 2. Provide the datasets

The test builds two real OPLA projects using activities from the template datasets, so copy them into the `overwrite` folder:

```bash
mkdir -p overwrite
cp -r datasets-templates overwrite/datasets
```

## 3. Build the test version

```bash
./compile-release.sh test
```

## 4. Run the test

```bash
tests/.venv/bin/python tests/compare/run_test.py
```

No manual preparation is needed: at the start of the run, the test builds a project in OPLA and exports it with **Export project**. From that `lca_study.json`, `tests/compare/make_candidates.py` writes four comparison candidates to `tests/compare/candidates/` (same file format, scaled results, different names and contributors), plus a few files the comparison must refuse.

To inspect the candidates without running the browser test, run the script on any file exported with **Export project**:

```bash
python3 tests/compare/make_candidates.py <path/to/lca_study.json>
```

## 5. Read the results

The last lines show the browser console warnings and errors and the list of failed checks. `ERRORS: []` with exit code `0` means every check passed; otherwise the exit code is `1`. Look at the screenshots in `tests/compare/shots/` to review the UI.

Rebuild (step 3) after every change in `app/` before running the test again. The generated files (`candidates/`, `shots/`, exported projects) are ignored by git.
