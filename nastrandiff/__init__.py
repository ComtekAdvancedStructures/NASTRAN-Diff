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

import difflib
import itertools
import os
import re
import typing


class NastranDiff:
    """
    A class that determines a diff between two NASTRAN input decks.

    Members:
    
    - file1: The first file to diff (a TextIOWrapper)
    - file2: The second file to diff (a TextIOWrapper)
    - output: An HTML file to write the output (a TextIOWrapper)
    - context: None to show full files in diff; an integer to show '''context''' lines of context
    - progress: A boolean indicating whether to display progress
    - separators: A boolean indicating whether to insert separators between the bulk data fields in the HTML
    """
    def __init__(self):
        self.file1 = None
        self.file2 = None
        self.output = None
        self.context = None
        self.progress = False
        self.separators = False

    @staticmethod
    def check_for_include(line: str) -> typing.Union[None, str]:
        # We use a regular expression to parse the include statement, but this is fairly slow, so check if the line
        # starts with the word INCLUDE first
        if not line.startswith("INCLUDE"):
            return None
        r = re.match("INCLUDE\\s+(['\"])?(\\S+)(?(1)['\"]|\\s*)", line)
        return None if r is None else r.group(2)

    @staticmethod
    def read_file(f: typing.TextIO, break_at: str) -> str:
        for line in f:
            if line.startswith(break_at):
                break
            include = NastranDiff.check_for_include(line)
            if include is not None:
                include_f = open(os.path.dirname(os.path.realpath(f.name)) + os.path.sep + include, "r")
                yield from NastranDiff.read_file(include_f, break_at)
            else:
                yield line

    @staticmethod
    def parse_field(field: str) -> typing.Union[int, float, str]:
        field = field.strip()  # remove leading and trailing whitespace
        if re.match("[-+.0-9]", field):  # it's integer or real (because it starts with one of those characters
            if "." in field:  # it's real (reals must contain a decimal point per NASTRAN docs)
                field = field.replace("D", "E")  # MSC uses 'D' instead of 'E' for scientific notation
                p = re.compile("([.0-9])([-+])([0-9])")
                field = p.sub("\\1E\\2\\3", field)
                return float(field)
            else:  # it's integer
                return int(field)
        else:  # it's character
            return field

    @staticmethod
    def format_float_nastran(f: float, width: int = 8) -> str:
        txt = ""
        remaining_width = width

        if f < 0.:
            txt += "-"
            remaining_width -= 1
            f *= -1

        if f >= 10 ** (remaining_width - 5):
            txt += "{:<{width}E}".format(f, width=remaining_width)
            if "." not in txt:
                txt = txt.replace("E", ".E")
            else:
                m = re.compile("[0-9]E")
                while len(txt) > width:
                    txt = m.sub("E", txt)  # remove precision
        elif f < 10 ** (-99):
            txt += "0.0"
        elif f < 10 ** (4 - remaining_width):
            txt += "{:<.{width}E}".format(f, width=remaining_width)  # The resulting string will (probably) be too wide
            m = re.compile("[0-9]E")
            while len(txt) > width:
                txt = m.sub("E", txt)  # remove precision
        else:
            txt += "{:<{width}.{width}}".format(f, width=remaining_width - 1)
            if "." not in txt:
                txt = txt.strip() + "."
            txt = txt[:width]

        if len(txt) < width:
            txt += " " * (width - len(txt))

        return txt

    @staticmethod
    def format_bde(bde_name: str, fields: list) -> str:
        txt = "{:<8}".format(bde_name)
        for f in fields:
            if type(f) is float:
                txt += NastranDiff.format_float_nastran(f)
            else:
                txt += "{:<8}".format(f)
        return txt

    @staticmethod
    def parse_fixed_field_format_line(line: str) -> (str, list, bool):
        bde_name = line[0:8]
        if "*" in bde_name:
            field_width = 16
            bde_name = bde_name[0:bde_name.find("*")]  # remove the asterisk that indicates large fields
        else:
            field_width = 8
        bde_name = bde_name.strip()
        if "$" in line:
            line = line.split("$")[0]  # remove the comment, if one exists
        if len(line) < 72:
            line += " " * (72 - len(line))
        # in the following list comprehension, we ignore the continuation field (only read the first 72 characters
        fields = [NastranDiff.parse_field(line[i:i + field_width]) for i in range(8, min(len(line), 72), field_width)]
        continuation = len(bde_name) == 0 or "+" in bde_name
        return bde_name, fields, continuation

    @staticmethod
    def parse_free_field_format_line(line: str) -> (str, list, bool):
        split_line = line.split(",")
        bde_name = split_line[0]
        if "*" in bde_name:
            bde_name = bde_name[0:bde_name.find("*")]  # remove the asterisk that indicates large fields
        bde_name = bde_name.strip()
        fields = [NastranDiff.parse_field(f) for f in split_line[1:]]
        continuation = len(bde_name) == 0 or "+" in bde_name
        return bde_name, fields, continuation

    @staticmethod
    def parse_bulk_data(bulk: iter) -> dict:
        multi_field_keys = {"PLOAD4": [1],
                            "FORCE": [1],
                            "SPC": [1],
                            "SPC1": [2],
                            "TEMP": [1],
                            "MPC": [1],
                            "DMIG": [1, 2]}
        data = {}
        key = ""
        for line in bulk:
            if "$" in line:
                # Remove the comment character and anything after it
                line = line[0:line.find("$")]
            line = line.rstrip()  # remove trailing whitespace
            if len(line) == 0:
                continue
            if "," in line:
                # the format is a free-field format
                bde_name, fields, continuation = NastranDiff.parse_free_field_format_line(line)
            else:
                # the format must be fixed-field format
                bde_name, fields, continuation = NastranDiff.parse_fixed_field_format_line(line)
            if continuation:
                data[key] += "\n" + NastranDiff.format_bde("", fields)
            else:
                key = bde_name + "{:8}".format(fields[0])  # BDE name and the ID
                if bde_name in multi_field_keys:
                    key += "".join(["{:8}".format(fields[i]) for i in multi_field_keys[bde_name]])
                if key in data:
                    print("""Warning: Multiple lines being saved as '{}'. This may indicate a problem in the BDF or a
                          bug in this software""".format(key))
                data[key] = NastranDiff.format_bde(bde_name, fields)
        return data

    @staticmethod
    def remove_continuations(bde: str, width=8) -> str:
        if "\n" not in bde:
            return bde
        lines = bde.split("\n")
        txt = lines[0]
        for l in lines[1:]:
            txt += l[width:]
        return txt

    def compare_bulk(self, bulk1, bulk2) -> (list, list, list, list):
        if self.progress:
            print("Parsing bulk data (file 1)...")
        bulk1 = NastranDiff.parse_bulk_data(bulk1)
        if self.progress:
            print("Parsing bulk data (file 2)...")
        bulk2 = NastranDiff.parse_bulk_data(bulk2)

        file1unique = []
        file2unique = []
        diff1 = []
        diff2 = []

        if self.progress:
            print("Processing bulk data differences...")

        for bde in sorted(bulk1):
            if bde in bulk2:
                b1 = NastranDiff.remove_continuations(bulk1[bde])
                b2 = NastranDiff.remove_continuations(bulk2[bde])
                if b1 != b2:
                    diff1.append(bulk1[bde])
                    diff2.append(bulk2[bde])
            else:
                file1unique.append(bulk1[bde])

        for bde in sorted(bulk2):
            if bde not in bulk1:
                file2unique.append(bulk2[bde])

        return diff1, diff2, file1unique, file2unique

    def format_bde_html(self, bde: str, width: int = 8) -> str:
        if self.separators:
            fmt = '<span class = "bde_sep">{}</span>'
        else:
            fmt = "{}"
        lines = bde.split("\n")
        processed_lines = []
        for l in lines:
            cur_line = ""
            entries = [l[i:i+width] for i in range(0, len(l), width)]
            for e in entries:
                cur_line += fmt.format(e)
            processed_lines.append(cur_line)
        return "<br />".join(processed_lines)

    def generate_html_difference(self, diff1, diff2) -> str:
        fmt_chg = '<tr>' + \
                  '<td nowrap="nowrap"><span class="diff_chg">%s</span></td>' + \
                  '<td nowrap="nowrap"><span class="diff_chg">%s</span></td>' + \
                  '</tr>\n'

        for d1, d2 in zip(diff1, diff2):
            yield fmt_chg % (
                self.format_bde_html(d1),
                self.format_bde_html(d2)
            )

    def generate_html_subtractions(self, unique1) -> str:
        fmt_sub = '<tr>' + \
                  '<td nowrap="nowrap"><span class="diff_sub">%s</span></td>' + \
                  '<td nowrap="nowrap">%s</td>' + \
                  '</tr>\n'

        for u1 in unique1:
            yield fmt_sub % (self.format_bde_html(u1), "")

    def generate_html_additions(self, unique2) -> str:
        fmt_add = '<tr>' + \
                  '<td nowrap="nowrap">%s</td>' + \
                  '<td nowrap="nowrap"><span class="diff_add">%s</span></td>' + \
                  '</tr>\n'

        for u2 in unique2:
            yield fmt_add % ("", self.format_bde_html(u2))

    def make_table_bulk(self, diff1, diff2, unique1, unique2, from_desc, to_desc) -> str:
        header_row = '<thead><tr>%s%s</tr></thead>' % (
            '<th class="diff_header">%s</th>' % from_desc,
            '<th class="diff_header">%s</th>' % to_desc)

        return self._table_template % dict(
            data_rows=''.join(itertools.chain(self.generate_html_difference(diff1, diff2),
                                              self.generate_html_subtractions(unique1),
                                              self.generate_html_additions(unique2))),
            header_row=header_row)

    _file_template = """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
              "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html>
    <head>
        <meta http-equiv="Content-Type"
              content="text/html; charset=ISO-8859-1" />
        <title></title>
        <style type="text/css">%(styles)s
        </style>
    </head>
    <body>
    %(legend)s
        <h2>Executive Control</h2>
        %(table_exec)s
        <h2>Case Control</h2>
        %(table_case)s
        <h2>Bulk Data</h2>
        <p>Note that the bulk data cards may be re-ordered.
        The position of each entry within the following table are very likely meaningless.</p>
        %(table_bulk)s
    </body>
    </html>"""

    _styles = """
    table.diff {font-family:Courier; border:medium;}
    .diff_header {background-color:#e0e0e0}
    td.diff_header {text-align:right}
    .diff_next {background-color:#c0c0c0}
    .diff_add {background-color:#aaffaa; white-space: pre; }
    .diff_chg {background-color:#ffff77; white-space: pre; }
    .diff_sub {background-color:#ffaaaa; white-space: pre; }
    span.bde_sep {border-right: solid #ff0000 1px; white-space: pre; }"""

    _legend = """
        <table class="diff" summary="Legends">
            <tr> <th colspan="2"> Legends </th> </tr>
            <tr> <td> <table border="" summary="Colors">
                          <tr><th> Colors </th> </tr>
                          <tr><td class="diff_add">&nbsp;Added&nbsp;</td></tr>
                          <tr><td class="diff_chg">Changed</td> </tr>
                          <tr><td class="diff_sub">Deleted</td> </tr>
                      </table></td>
                 <td> <table border="" summary="Links">
                          <tr><th colspan="2"> Links </th> </tr>
                          <tr><td>(f)irst change</td> </tr>
                          <tr><td>(n)ext change</td> </tr>
                          <tr><td>(t)op</td> </tr>
                      </table></td> </tr>
        </table>"""

    _table_template = """
        <table class="diff"
               cellspacing="0" cellpadding="0" rules="groups" >
            <colgroup></colgroup> <colgroup></colgroup>
            %(header_row)s
            <tbody>
    %(data_rows)s        </tbody>
        </table>"""

    def calculate_diff(self) -> None:
        df = difflib.HtmlDiff()

        exec1 = self.read_file(self.file1, "CEND")
        exec2 = self.read_file(self.file2, "CEND")
        if self.progress:
            print("Diffing executive control...")
        table_exec = df.make_table(exec1, exec2,
                                   fromdesc=self.file1.name, todesc=self.file2.name,
                                   context=self.context is not None,
                                   numlines=self.context if self.context is not None else 5)

        case1 = self.read_file(self.file1, "BEGIN BULK")
        case2 = self.read_file(self.file2, "BEGIN BULK")
        if self.progress:
            print("Diffing case control...")
        table_case = df.make_table(case1, case2,
                                   fromdesc=self.file1.name, todesc=self.file2.name,
                                   context=self.context is not None,
                                   numlines=self.context if self.context is not None else 5)

        bulk1 = self.read_file(self.file1, "ENDDATA")
        bulk2 = self.read_file(self.file2, "ENDDATA")
        bulk1diff, bulk2diff, bulk1unique, bulk2unique = self.compare_bulk(bulk1, bulk2)

        if self.progress:
            print("Diffing bulk data...")
        table_bulk = self.make_table_bulk(bulk1diff, bulk2diff, bulk1unique, bulk2unique,
                                          from_desc=self.file1.name, to_desc=self.file2.name)

        diff = self._file_template % dict(
            styles=self._styles,
            legend=self._legend,
            table_exec=table_exec,
            table_case=table_case,
            table_bulk=table_bulk)
        self.output.write(diff)
