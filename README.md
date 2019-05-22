# NASTRAN-Diff
The NASTRAN-Diff program allows comparison of two NASTRAN decks.
Comparing the text of two NASTRAN decks using a text comparison tool
(`diff`, etc.) produces many false differences. For example, the order
of bulk data entries within a deck does not matter to the solver and
there are several different formats for specifying bulk data entries
that do not have an affect on the way that the deck is interpreted by
a solver. NASTRAN-Diff addresses this.

The main features of NASTRAN-Diff are:

- Display of differences in an easy to understand HTML file
- Recursively opens parts of the deck specified in INCLUDE statements
- Supports line continuations
- Supports both 8 and 16 character fields

# Installation and Usage
## Windows
A `.zip` file is available on the GitHub releases pages for this project.
Download this file and extract it to a folder on your PC.

You'll need to add the `nastrandiff` folder to your system path. You can
do this permanently by editing the environment variable. Or, you can 
do this temporarily in the command prompt that you are using by typing the
following (substituting the correct path).

```bash
path=%path%;C:\path\to\nastrandiff
```

You can now navigate to the folder containing the decks you wish to compare
and type:

```bash
nastrandiff deck1.bdf deck2.bdf
```

## Other Operating Systems
You can call NASTRAN-Diff with your system Python interpreter using the
following command. You will have to append the appropriate arguments, as
defined in the help message (which should show up when you call it with
no arguments).

```bash
python -m nastrandiff.py
```

## Contributing
Contributions are welcome. Please discuss proposed changes on the GitHub
Issues page for this project and then submit a Pull Request. Please
include unit tests for any bugs found or new features added.

## Development Environment
An Anaconda environment is available for use when developing NASTRAN-Diff.
To install this environment, navigate to the NASTRAN-Diff directory and run:

```bash
conda env create -f environment.yml
```

If you need to update the environment (for example because NASTRAN-Diff now
needs a new package installed), then run:

```bash
conda env export --no-builds > environment.yml
```

You should edit the `environment.yml` file to remove the absolute path in the
`prefix` line. Then, stage/commit the updated `environemnt.yml` file.

## Building for Windows
An exe can be built using `nuitka` using the following command:

```bash
python -m nuitka --standalone --show-progress nastrandiff.py

```

Many files will be created in the `dist` directory. This folder can be zipped and
uploaded to GitHub under the release.
