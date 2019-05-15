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

## Contributing
Contributions are welcome. Please discuss proposed changes on the GitHub
Issues page for this project and then submit a Pull Request. Please
include unit tests for any bugs found or new features added.
