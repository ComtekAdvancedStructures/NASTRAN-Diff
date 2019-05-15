import argparse
import datetime
import nastrandiff
import os
import pathlib
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
    args = parser.parse_args()

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