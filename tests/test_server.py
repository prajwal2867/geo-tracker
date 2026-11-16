import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from geotracker.server import GeoHandler


class GeoHandlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GeoHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post_location(self, body):
        request = Request(
            f"{self.base_url}/location",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        return response.code, json.loads(response.read())

    def test_valid_coordinates_are_accepted(self):
        body = json.dumps(
            {"latitude": 51.5, "longitude": -0.12, "accuracy": 10}
        ).encode()

        with patch("builtins.print"):
            status, payload = self.post_location(body)

        self.assertEqual(status, 200)
        self.assertEqual(payload, {"status": "ok"})

    def test_root_serves_page_with_security_headers(self):
        response = urlopen(self.base_url)

        self.assertEqual(response.status, 200)
        self.assertIn("Content-Security-Policy", response.headers)
        self.assertIn(b"Share your location", response.read())

    def test_malformed_json_is_rejected(self):
        status, payload = self.post_location(b"{")

        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_out_of_range_coordinates_are_rejected(self):
        body = json.dumps(
            {"latitude": 91, "longitude": 0, "accuracy": 1}
        ).encode()

        status, payload = self.post_location(body)

        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_non_finite_coordinates_are_rejected(self):
        status, payload = self.post_location(
            b'{"latitude": NaN, "longitude": 0, "accuracy": 1}'
        )

        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_oversized_body_is_rejected(self):
        body = b" " * 4097

        status, payload = self.post_location(body)

        self.assertEqual(status, 413)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
