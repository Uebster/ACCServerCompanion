import unittest

from acc_data import SESSION_PRESETS, build_session_plan


class SessionPresetTests(unittest.TestCase):
    def test_practice_qualify_race_preset_has_expected_order(self):
        sessions = build_session_plan("practice_qualify_race")
        self.assertEqual([session["sessionType"] for session in sessions], ["P", "Q", "R"])
        self.assertEqual(sessions[0]["sessionDurationMinutes"], 120)
        self.assertEqual(sessions[1]["sessionDurationMinutes"], 10)
        self.assertEqual(sessions[2]["sessionDurationMinutes"], 20)

    def test_race_only_preset_uses_only_race_session(self):
        sessions = build_session_plan("race_only")
        self.assertEqual([session["sessionType"] for session in sessions], ["R"])
        self.assertEqual(sessions[0]["sessionDurationMinutes"], 20)

    def test_session_presets_are_available(self):
        self.assertIn("practice_qualify_race", SESSION_PRESETS)
        self.assertIn("race_only", SESSION_PRESETS)


if __name__ == "__main__":
    unittest.main()
