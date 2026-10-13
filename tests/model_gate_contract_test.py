#!/usr/bin/env python3
"""Offline model ranking contracts. No inference/GPU/network."""
import importlib.util
import io
import json
from pathlib import Path
from unittest import TestCase, main, mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "model_gate.py"
spec = importlib.util.spec_from_file_location("embedding_gate", SCRIPT)
assert spec is not None and spec.loader is not None
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class EmbeddingGateContracts(TestCase):
    def test_shuffled_openai_rows_are_restored_by_index(self):
        data = [
            {"index": 2, "embedding": [0.0, 0.0, 1.0]},
            {"index": 0, "embedding": [1, 0, 0]},
            {"index": 1, "embedding": [0, 1, 0]},
        ]
        self.assertEqual(gate.ordered_embeddings(data, 3), [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])

    def test_duplicate_missing_and_out_of_range_indexes_fail(self):
        for indices in [[0, 0], [0, 2], [None, 1], [False, 1], [0]]:
            data = [{"index": i, "embedding": [1.0]} for i in indices]
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                gate.ordered_embeddings(data, 2)

    def test_malformed_nonfinite_zero_and_mixed_dimensions_fail(self):
        inputs = [
            [[1.0, float("nan")]],
            [[1.0, float("inf")]],
            [[0.0, 0.0]],
            [["1", 0.0]],
            [[True, 1.0]],
            [[]],
        ]
        for embeddings in inputs:
            with self.subTest(embeddings=embeddings), self.assertRaises(ValueError):
                gate.ordered_embeddings([{"index": 0, "embedding": embeddings[0]}], 1)
        with self.assertRaises(ValueError):
            gate.ordered_embeddings([
                {"index": 0, "embedding": [1.0]},
                {"index": 1, "embedding": [0.0, 1.0]},
            ], 2)

    def test_urlopen_response_sorted_without_real_network(self):
        data = {"data": [
            {"index": 1, "embedding": [0.0, 1.0]},
            {"index": 0, "embedding": [1.0, 0.0]},
        ]}
        with mock.patch.object(gate.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())) as url:
            result = gate.embed("http://example.invalid/v1/embeddings", "local", ["A", "B"])
        self.assertEqual(result, [[1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(url.call_count, 1)

    def test_cosine_different_dimensions_and_zero_rejected(self):
        self.assertAlmostEqual(gate.cos([1.0, 0.0], [0.0, 1.0]), 0.0)
        self.assertAlmostEqual(gate.cos([1.0, 0.0], [1.0, 0.0]), 1.0)
        for a, b in [([], []), ([1], [1, 1]), ([0, 0], [1, 0]), ([float("nan")], [1])]:
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                gate.cos(a, b)

    def test_retrieval_recall_one_for_one_hot_queries_and_docs(self):
        vectors = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
        with mock.patch.object(gate, "embed", side_effect=[vectors, vectors]) as mocked:
            result = gate.evaluate("http://example.invalid", "local", pairs=[("q1", "d1"), ("q2", "d2"), ("q3", "d3")])
        self.assertEqual(result["pairs"], 3)
        self.assertEqual(result["recall_at_1"], 1.0)
        self.assertEqual(result["dimension"], 3)
        self.assertEqual(mocked.call_count, 2)

    def test_query_document_dimension_mismatch_rejected(self):
        with mock.patch.object(gate, "embed", side_effect=[[[1.0, 0.0]], [[1.0]]]):
            with self.assertRaisesRegex(ValueError, "dimensions differ"):
                gate.evaluate("http://example.invalid", "local", pairs=[("query", "doc")])

    def test_original_six_bilingual_pairs_retained(self):
        self.assertEqual(len(gate.PAIRS), 6)
        self.assertIn("Proxmox Backup Server", gate.PAIRS[0][1])
        self.assertIn("transcription audio en français", gate.PAIRS[-1][0])


if __name__ == "__main__":
    main(verbosity=2)
