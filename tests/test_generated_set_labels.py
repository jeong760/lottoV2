import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui.widgets.generated_sets_widget import GeneratedSetsWidget


def test_generated_set_label_sequence_matches_documented_pattern():
    assert GeneratedSetsWidget._get_alpha_label(None, 0) == "SET A"
    assert GeneratedSetsWidget._get_alpha_label(None, 25) == "SET Z"
    assert GeneratedSetsWidget._get_alpha_label(None, 26) == "SET A0"
    assert GeneratedSetsWidget._get_alpha_label(None, 51) == "SET Z25"
    assert GeneratedSetsWidget._get_alpha_label(None, 52) == "SET A26"
    assert GeneratedSetsWidget._get_alpha_label(None, 53) == "SET B27"
