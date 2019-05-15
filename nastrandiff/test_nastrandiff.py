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

import unittest
from nastrandiff import NastranDiff


class TestNastranDiff(unittest.TestCase):
    def test_include_regex(self):
        nd = NastranDiff()

        res = nd.check_for_include("INCLUDE 'DMIG/stiffness.dmig'")
        self.assertEqual(res, "DMIG/stiffness.dmig")

        res = nd.check_for_include("NOTINCLUDE shouldn't find include")
        self.assertIsNone(res)

    def test_parse_field(self):
        nd = NastranDiff()

        res = nd.parse_field("7.0")
        self.assertEqual(res, 7.0)

        res = nd.parse_field(".7E1")
        self.assertEqual(res, 7.0)

        res = nd.parse_field("0.7+1")
        self.assertEqual(res, 7.0)

        res = nd.parse_field(".70+1")
        self.assertEqual(res, 7.0)

        res = nd.parse_field("7.E+0")
        self.assertEqual(res, 7.0)

        res = nd.parse_field("70.-1")
        self.assertEqual(res, 7.0)

        res = nd.parse_field("800")
        self.assertEqual(res, 800)

        res = nd.parse_field("TEST    ")
        self.assertEqual(res, "TEST")

        res = nd.parse_field("2.193363961D+06")
        self.assertEqual(res, 2.193363961E+06)

    @staticmethod
    def strip_trailing_whitespace(string: str) -> str:
        return "\n".join([line.rstrip() for line in string.split("\n")])

    def test_parse_bulk_data(self):
        nd = NastranDiff()

        # Test single-line MSC format
        bd = ["SPC     101106  880000430       0.0     "]
        res = nd.parse_bulk_data(bd)
        self.assertEqual(
            self.strip_trailing_whitespace(res["SPC  10110688000043"]),
            self.strip_trailing_whitespace("SPC     101106  880000430       0.0     "))

        # test multi-line MSC format
        bd = ["MPC     101106  228711  1       1.      814319  1       -1.     ",
              "                880000440       1.      880000450       -1."]
        res = nd.parse_bulk_data(bd)
        expected_res = """MPC     101106  228711  1       1.0     814319  1       -1.0    
                880000440       1.0     880000450       -1.0    """
        self.assertEqual(
            self.strip_trailing_whitespace(res["MPC  101106  228711"]),
            self.strip_trailing_whitespace(expected_res))

        # test wide format with continuation
        #         –1–       –2–             –3–              –4–              –5–          –6–
        #      $2345678|2345678.......x|2345678.......x|2345678.......x|2345678.......x|2345678
        bd = ["GRID*                  2                             1.0            -2.0+",
              "*                    3.0                             136"]
        res = nd.parse_bulk_data(bd)
        expected_res = """GRID    2               1.0     -2.0    
        3.0             136     """
        self.assertEqual(
            self.strip_trailing_whitespace(res["GRID       2"]),
            self.strip_trailing_whitespace(expected_res))

        # test comments
        bd = ["$Some comment",
              "$Some comment"]
        res = nd.parse_bulk_data(bd)
        self.assertEqual(len(res), 0)

        # test multi-line FEMAP format
        bd = ["RBE3     8000175         1050116  123456      1.     123 1000941 1000935+       ",
              "+        1000942 1000936"]
        res = nd.parse_bulk_data(bd)
        expected_res = """RBE3    8000175         1050116 123456  1.0     123     1000941 1000935 
        1000942 1000936 """
        self.assertEqual(
            self.strip_trailing_whitespace(res["RBE3 8000175"]),
            self.strip_trailing_whitespace(expected_res))

        # test free-field format
        bd = ["GRID,2,,1.0,-2.0,3.0,,136"]
        res = nd.parse_bulk_data(bd)
        expected_res = "GRID    2               1.0     -2.0    3.0             136     "
        self.assertEqual(
            self.strip_trailing_whitespace(res["GRID       2"]),
            self.strip_trailing_whitespace(expected_res))

    def test_format_bde(self):
        nd = NastranDiff()

        cases = {-10.: "-10.0   ",
                 10.: "10.0    ",
                 -0.1: "-0.1    ",
                 0.1: "0.1     ",
                 -0.000001: "-1.0E-06",
                 0.0000001: "1.00E-07",
                 100000.: "1.00E+05",
                 -100000.: "-1.0E+05",
                 100000.2: "1.00E+05",
                 -100000.2: "-1.0E+05",
                 1000000.: "1.00E+06",
                 -1000000.: "-1.0E+06",
                 10000000.: "1.00E+07",
                 -10000000.: "-1.0E+07",
                 0.: "0.0     "
                 }

        for c, er in cases.items():
            res = nd.format_bde("BDE", [c])
            self.assertEqual(len(res), 16)  # there should be two fields: the BDE name (blank) and the field specified
            if type(c) is float:
                self.assertRegex(res, ".")  # floats MUST contain a decimal place, per NASTRAN docs
            self.assertEqual(res, "BDE     {}".format(er))


if __name__ == '__main__':
    unittest.main()
