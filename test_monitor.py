import os

# Set up dummy environment variables for tests BEFORE importing anything else
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"
os.environ["TELEGRAM_CHAT_ID"] = "dummy_chat"
os.environ["NTFY_TOPIC"] = "dummy_topic"
os.environ["STATE_FILE_PATH"] = "test_state.json"
os.environ["PARIBU_URL"] = "https://www.paribucineverse.com/fantastik-filmleri/orumcek-adam-yepyeni-bir-gun-filmi-izle"
os.environ["BILETINIAL_URL"] = "https://biletinial.com/tr-tr/sinema"
os.environ["BILETINIAL_KEYWORDS"] = "spider,örümcek,orumcek"

import unittest
from unittest.mock import patch, MagicMock
import json

from config import Config
import monitor
from monitor import check_paribu, check_biletinial, load_state, save_state, run_once
from notifier import Notifier

class TestTicketMonitor(unittest.TestCase):

    def setUp(self):
        Config.STATE_FILE_PATH = "test_state.json"
        if os.path.exists("test_state.json"):
            try:
                os.remove("test_state.json")
            except OSError:
                pass
            
    def tearDown(self):
        if os.path.exists("test_state.json"):
            try:
                os.remove("test_state.json")
            except OSError:
                pass

    def test_check_paribu_positive(self):
        html_valid = (
            "<html><body>"
            "<a href='/biletleme/step/session/film/123' class='cgv-btn'>"
            "<span>Hemen Bilet Al</span>"
            "</a>"
            "</body></html>"
        )
        self.assertTrue(check_paribu(html_valid))

    def test_check_paribu_negative(self):
        # Case A: Right text, wrong class
        html_a = "<html><body><a href='/biletleme/123' class='other-btn'>Hemen Bilet Al</a></body></html>"
        self.assertFalse(check_paribu(html_a))

        # Case B: Right class and link, wrong text
        html_b = "<html><body><a href='/biletleme/123' class='cgv-btn'>Detaylı Bilgi</a></body></html>"
        self.assertFalse(check_paribu(html_b))

    def test_check_biletinial_positive(self):
        keywords = ["spider", "örümcek", "orumcek"]
        
        # Matches 'spider'
        self.assertTrue(check_biletinial("some text containing spider-man here", keywords))
        # Matches 'örümcek'
        self.assertTrue(check_biletinial("örümcek adam biletleri satışta", keywords))
        # Matches 'orumcek'
        self.assertTrue(check_biletinial("orumcek adam yakinda", keywords))

    def test_check_biletinial_negative(self):
        keywords = ["spider", "örümcek", "orumcek"]
        # Doesn't match
        self.assertFalse(check_biletinial("demir adam ve yenilmezler sinemada", keywords))

    def test_state_load_save(self):
        # Initially empty dict
        state = load_state()
        self.assertEqual(state, {})
        
        # Save state for paribu
        save_state("paribu", tickets_on_sale=True)
        state = load_state()
        self.assertTrue(state["paribu"]["tickets_on_sale"])
        self.assertIsNotNone(state["paribu"]["last_checked"])
        
        # Save state for biletinial
        save_state("biletinial", tickets_on_sale=False)
        state = load_state()
        self.assertTrue(state["paribu"]["tickets_on_sale"])
        self.assertFalse(state["biletinial"]["tickets_on_sale"])

    @patch("monitor.fetch_page")
    @patch("notifier.Notifier.notify")
    def test_run_once_transitions(self, mock_notify, mock_fetch):
        mock_notify.return_value = True
        
        # Map URL outputs for targets:
        # Paribu URL: Config.PARIBU_URL -> returns page WITHOUT ticket
        # Biletinial URL: Config.BILETINIAL_URL -> returns page WITHOUT keywords
        def side_effect(url):
            if url == Config.PARIBU_URL:
                return "<html><body>Biletler yakında.</body></html>"
            elif url == Config.BILETINIAL_URL:
                return "<html><body>Başka filmler sinemada.</body></html>"
            return None
            
        mock_fetch.side_effect = side_effect
        
        # Run 1: None of the tickets are on sale
        run_once()
        mock_notify.assert_not_called()
        self.assertFalse(load_state()["paribu"]["tickets_on_sale"])
        self.assertFalse(load_state()["biletinial"]["tickets_on_sale"])
        
        # Run 2: Paribu tickets go on sale, Biletinial remains NOT on sale
        def side_effect_run2(url):
            if url == Config.PARIBU_URL:
                return "<html><body><a class='cgv-btn' href='/biletleme/123'>Hemen Bilet Al</a></body></html>"
            elif url == Config.BILETINIAL_URL:
                return "<html><body>Başka filmler sinemada.</body></html>"
            return None
            
        mock_fetch.side_effect = side_effect_run2
        run_once()
        mock_notify.assert_called_once()
        self.assertTrue(load_state()["paribu"]["tickets_on_sale"])
        self.assertFalse(load_state()["biletinial"]["tickets_on_sale"])
        
        # Reset mocks
        mock_notify.reset_mock()
        
        # Run 3: Paribu still on sale, Biletinial now ALSO goes on sale (detects "örümcek")
        def side_effect_run3(url):
            if url == Config.PARIBU_URL:
                return "<html><body><a class='cgv-btn' href='/biletleme/123'>Hemen Bilet Al</a></body></html>"
            elif url == Config.BILETINIAL_URL:
                return "<html><body>Örümcek Adam biletleri biletinial'da!</body></html>"
            return None
            
        mock_fetch.side_effect = side_effect_run3
        run_once()
        mock_notify.assert_called_once() # Should only notify for Biletinial, not Paribu (since Paribu was already on sale)
        self.assertTrue(load_state()["paribu"]["tickets_on_sale"])
        self.assertTrue(load_state()["biletinial"]["tickets_on_sale"])

    @patch("monitor.fetch_page")
    @patch("notifier.Notifier.notify")
    def test_run_once_notifies_when_target_unreachable_once(self, mock_notify, mock_fetch):
        mock_notify.return_value = True
        original_biletinial_url = Config.BILETINIAL_URL
        Config.BILETINIAL_URL = ""

        try:
            mock_fetch.return_value = (None, "Connection timed out")

            run_once()
            mock_notify.assert_called_once()
            state = load_state()["paribu"]
            self.assertTrue(state["site_unreachable"])
            self.assertEqual(state["last_error"], "Connection timed out")

            run_once()
            mock_notify.assert_called_once()

            mock_fetch.return_value = "<html><body>Biletler yakında.</body></html>"
            run_once()
            state = load_state()["paribu"]
            self.assertEqual(mock_notify.call_count, 2)
            self.assertFalse(state["site_unreachable"])
            self.assertFalse(state["tickets_on_sale"])
            self.assertNotIn("last_error", state)
        finally:
            Config.BILETINIAL_URL = original_biletinial_url

    def test_live_supergirl_integration(self):
        """Integration test fetching the real Supergirl page and verifying tickets are on sale."""
        url = "https://www.paribucineverse.com/fantastik-filmleri/supergirl-filmi-izle"
        print(f"\n[TEST INFO] Running live Supergirl integration test against URL: {url}")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        try:
            import requests
            print("[TEST INFO] Fetching live HTML page...")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            html_content = response.text
            
            # Verify check_paribu detects tickets are on sale
            is_on_sale = check_paribu(html_content)
            print(f"[TEST INFO] Tickets on sale detection status: {is_on_sale}")
            self.assertTrue(is_on_sale, "Supergirl tickets should be detected as on sale based on the live page.")
            print("[TEST INFO] Test passed successfully!")
        except Exception as e:
            print(f"[TEST ERROR] Live test failed: {e}")
            self.fail(f"Live request to Supergirl URL failed: {e}")

if __name__ == "__main__":
    unittest.main()
