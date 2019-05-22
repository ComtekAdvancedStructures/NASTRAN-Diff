# This file is part of NASTRAN-Diff.
#
# NASTRAN-Diff is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
#  NASTRAN-Diff is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Foobar.  If not, see <https://www.gnu.org/licenses/>.

__version__ = "1.0.0.9000"

import argparse
import datetime
import nastrandiff
import os
import pathlib
import sys
import time
import webbrowser

# If this file was called from the command line, respond to the arguments passed
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""A utility program for determining the diff between two NASTRAN input
                                     decks. This program understands multi-file input decks that use the INCLUDE
                                     directive.""")
    parser.add_argument("file1", nargs="?", type=argparse.FileType('r'),
                        help="first (left) file to diff")
    parser.add_argument("file2", nargs="?", type=argparse.FileType('r'),
                        help="second (right) file to diff")
    parser.add_argument("--output", nargs="?", type=argparse.FileType('w'),
                        help="the (html) file where the output should be directed. Default: diff-[current-time].html",
                        default="diff-{}.html".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
    parser.add_argument("-C", nargs="?", type=int,
                        help="use context output format, showing 'lines' (integer) lines of context")
    parser.add_argument("-s", action="store_true",
                        help="display field separators in diff")
    parser.add_argument("--time", action='store_true',
                        help="display the wall-time required to execute the diff")
    parser.add_argument("--progress", action="store_true",
                        help="display the progress of the program")
    parser.add_argument("--no-launch-browser", action="store_true",
                        help="don't launch the system default web browser with the results")
    parser.add_argument('--version', action='version',
                        version="NASTRAN-Diff version {version}".format(version=__version__))

    args = None  # fix a linting error

    try:
        args = parser.parse_args()
    except(argparse.ArgumentError, argparse.ArgumentTypeError):
        parser.print_help()
        sys.exit(0)

    if args.file1 is None or args.file2 is None:
        parser.print_help()
        sys.exit(0)

    nd = nastrandiff.NastranDiff()
    nd.file1 = args.file1
    nd.file2 = args.file2
    nd.output = args.output
    nd.context = args.C
    nd.progress = args.progress
    nd.separators = args.s

    start = time.time()
    nd.calculate_diff()
    end = time.time()
    if args.time:
        print("Elapsed time: {}".format(end - start))

    if not args.no_launch_browser:
        url = pathlib.Path(os.path.realpath(nd.output.name)).as_uri()
        print("Launching system browser to open URL {}".format(url))
        webbrowser.open(url)
