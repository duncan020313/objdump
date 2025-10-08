from jackson_installer.instrumentation.diff import parse_unified_diff_hunks_both


def test_parse_unified_diff_hunks_both_basic():
    diff = """--- a/A.java\n+++ b/A.java\n@@ -10,2 +10,3 @@\n-line1\n+line1x\n+line2\n"""
    ranges = parse_unified_diff_hunks_both(diff)
    assert ranges["left"] == [(10, 11)]
    assert ranges["right"] == [(10, 12)]


