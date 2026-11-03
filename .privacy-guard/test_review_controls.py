import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("control_gate", HERE / "pre_push.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
POLICY = json.loads((HERE / "presidio-policy.json").read_text())


class ReviewControlTests(unittest.TestCase):
    def fixture(self, *, invalid=False, wrong_path=False):
        row = {
            "identity": "a" * 64,
            "blob_sha256": "b" * 64,
            "entity_index": 0,
            "start": 123456,
            "end": 123459,
            "value_sha256": "c" * 64,
            "reason": "Alice Smith",
            "reviewer": "Bob Jones",
        }
        if invalid:
            row["blob_sha256"] = "Alice Smith"
        text = json.dumps(
            {
                "schemaVersion": 1,
                "policy_sha256": hashlib.sha256(
                    (HERE / "presidio-policy.json").read_bytes()
                ).hexdigest(),
                "findings": [row],
            },
            indent=2,
        )
        raw = text.encode()
        oid = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False
        ).hexdigest()
        path = (
            "other.json"
            if wrong_path
            else ".privacy-guard/presidio-reviewed-findings.json"
        )
        item = {
            "text": text,
            "identity": hashlib.sha256((path + ":" + oid).encode()).hexdigest(),
        }
        return item

    def result(self, item, value, entity="PERSON"):
        start = item["text"].index(value)
        return {
            "start": start,
            "end": start + len(value),
            "entity_index": POLICY["entities"].index(entity),
        }

    def test_only_exact_validated_control_tokens(self):
        item = self.fixture()
        for value in ("a" * 64, "b" * 32, "blob_sha256", "ob_sha256"):
            with self.subTest(value=value):
                self.assertTrue(
                    gate.review_control_number(item, self.result(item, value), POLICY)
                )
        self.assertTrue(
            gate.review_control_number(
                item, self.result(item, "123456", "PHONE_NUMBER"), POLICY
            )
        )
        self.assertFalse(
            gate.review_control_number(item, self.result(item, "123456"), POLICY)
        )

    def test_free_text_names_remain_detected(self):
        item = self.fixture()
        for value in ("Alice Smith", "Bob Jones"):
            self.assertFalse(
                gate.review_control_number(item, self.result(item, value), POLICY)
            )

    def test_unknown_file_and_invalid_schema_never_qualify(self):
        for kwargs in ({"wrong_path": True}, {"invalid": True}):
            item = self.fixture(**kwargs)
            self.assertFalse(
                gate.review_control_number(item, self.result(item, "a" * 64), POLICY)
            )


if __name__ == "__main__":
    unittest.main()
