import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from content_watcher.config import Config
from content_watcher.fetch import apify, base, fetch, gallerydl, linkedin_page, tiktok_page, ytdlp
from content_watcher.fetch.base import FetchFailed
from tests.cw_helpers import FIXTURES, FakeOpener, fake_tool, load, with_path


class ClassifyTests(unittest.TestCase):
    def test_tool_errors_map_to_the_card_classes(self):
        cases = {
            "ERROR: [Instagram] DAbC: Instagram sent an empty media response": "login_wall",
            "ERROR: [Instagram] x: Restricted Video: You must be 18 years old": "login_wall",
            "ERROR: [TikTok] 1: Video not available, status code 10204": "not_found",
            "ERROR: unable to download video data: HTTP Error 403: Forbidden": "blocked",
            "ERROR: HTTP Error 429: Too Many Requests": "blocked",
            "ERROR: [youtube] x: Sign in to confirm you're not a bot": "login_wall",
            "ERROR: File is larger than max-filesize (2.1GiB > 1.5GiB)": "too_big",
            "ERROR: The read operation timed out": "timeout",
            "ERROR: something nobody has seen": "other",
        }
        for text, expected in cases.items():
            self.assertEqual(base.classify(text)[0], expected, text)


class ParserTests(unittest.TestCase):
    def test_ytdlp_info_json(self):
        post = ytdlp.post_from_info(load("ytdlp_instagram.info.json"), "instagram", "https://www.instagram.com/reel/DAbCdEfGhIj/")
        self.assertEqual(post.author, "studio.example")
        self.assertEqual(post.posted_at, "2025-10-23T16:00:00+00:00")
        self.assertEqual(post.counts, {"views": 120345, "likes": 4210, "comments": 88})
        tiktok = ytdlp.post_from_info(load("ytdlp_tiktok.info.json"), "tiktok", "u")
        self.assertEqual(tiktok.author, "maker.example")
        self.assertEqual(tiktok.counts["shares"], 450)

    def test_gallerydl_metadata(self):
        post = gallerydl.post_from_metadata(load("gallerydl_instagram_meta.json"), "instagram", "u")
        self.assertEqual((post.post_id, post.author), ("CxYzSide01", "carousel.example"))
        self.assertEqual(post.posted_at, "2026-10-20T09:00:00+00:00")

    def test_tiktok_page_video_and_photo(self):
        meta, media, music = tiktok_page.parts(tiktok_page.item_struct((FIXTURES / "tiktok_video_page.html").read_text()))
        self.assertEqual(meta["author"], "editor.example")
        self.assertEqual(media, [("https://v16-webapp.tiktok.example/video/abc.mp4?expire=1", ".mp4")])
        self.assertIsNone(music)
        meta, media, music = tiktok_page.parts(tiktok_page.item_struct((FIXTURES / "tiktok_photo_page.html").read_text()))
        self.assertEqual([url for url, _ in media][0], "https://p16.tiktok.example/img/1.jpeg?x=1")
        self.assertEqual(len(media), 3)
        self.assertEqual(meta["counts"]["likes"], 200)
        self.assertTrue(music.endswith(".mp3"))

    def test_tiktok_page_failures(self):
        with self.assertRaises(FetchFailed) as removed:
            tiktok_page.item_struct((FIXTURES / "tiktok_removed_page.html").read_text())
        self.assertEqual(removed.exception.status_class, "not_found")
        with self.assertRaises(FetchFailed) as challenge:
            tiktok_page.item_struct((FIXTURES / "tiktok_challenge_page.html").read_text())
        self.assertEqual(challenge.exception.status_class, "blocked")

    def test_apify_instagram_items_keep_post_order(self):
        meta, media = apify.instagram_parts(load("apify_instagram_sidecar.json")[0])
        self.assertEqual(meta["author"], "carousel.example")
        self.assertEqual([ext for _, ext in media], [".jpg", ".mp4", ".jpg"])
        self.assertIn("s2.mp4", media[1][0])
        meta, media = apify.instagram_parts(load("apify_instagram_reel.json")[0])
        self.assertIn("key-value-stores", media[0][0])
        self.assertNotIn("comments", meta["counts"])  # -1 means hidden, not a count
        with self.assertRaises(FetchFailed) as missing:
            apify.instagram_parts(load("apify_instagram_missing.json")[0])
        self.assertEqual(missing.exception.status_class, "not_found")

    def test_apify_tiktok_items(self):
        meta, media, subtitle, music = apify.tiktok_parts(load("apify_tiktok_slideshow.json")[0])
        self.assertEqual(len(media), 2)
        self.assertIsNotNone(music)
        meta, media, subtitle, music = apify.tiktok_parts(load("apify_tiktok_video.json")[0])
        self.assertIn("video.mp4", media[0][0])
        self.assertEqual(subtitle, "https://api.apify.example/sub.vtt")
        self.assertIsNone(music)

    def test_linkedin_public_page(self):
        found = linkedin_page.parse_page((FIXTURES / "linkedin_post.html").read_text())
        self.assertEqual(found["author"], "Pat Example")
        self.assertIn("One idea a slide", found["text"])
        self.assertEqual(found["images"], ["https://media.licdn.example/one.jpg"])
        with self.assertRaises(FetchFailed) as wall:
            linkedin_page.parse_page((FIXTURES / "linkedin_authwall.html").read_text())
        self.assertEqual(wall.exception.status_class, "login_wall")
        with self.assertRaises(FetchFailed):
            linkedin_page.parse_page("<html></html>", "https://www.linkedin.com/authwall?trk=x")


class ToolRunTests(unittest.TestCase):
    """The yt-dlp and gallery-dl wrappers against fake programs that write what the real ones write."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.folder = self.root / "out"
        self.folder.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_ytdlp_writes_video_info_and_subtitles(self):
        fake_tool(self.bin, "yt-dlp", f"""
out = args[args.index('-o') + 1]
info = json.loads(pathlib.Path({str(FIXTURES / 'ytdlp_tiktok.info.json')!r}).read_text())
base = out.replace('%(id)s', info['id']).rsplit('.', 1)[0]
pathlib.Path(base + '.info.json').write_text(json.dumps(info))
pathlib.Path(base + '.mp4').write_bytes(b'video')
pathlib.Path(base + '.en.vtt').write_text('WEBVTT')
assert '--write-subs' in args
""")
        with mock.patch.dict(os.environ, with_path(self.bin)):
            post = ytdlp.fetch("https://www.tiktok.com/@maker.example/video/7430000000000000001", "tiktok",
                               self.folder, captions="all")
        self.assertEqual(post.media[0].name, "tiktok_7430000000000000001.mp4")
        self.assertEqual(post.captions_file.name, "tiktok_7430000000000000001.en.vtt")
        self.assertEqual(post.method, "ytdlp")
        self.assertFalse(list(self.folder.glob("*.info.json")))

    def test_ytdlp_failure_is_classified(self):
        fake_tool(self.bin, "yt-dlp", "print('ERROR: [Instagram] x: Instagram sent an empty media response', file=sys.stderr); sys.exit(1)")
        with mock.patch.dict(os.environ, with_path(self.bin)), self.assertRaises(FetchFailed) as failure:
            ytdlp.fetch("https://www.instagram.com/reel/x/", "instagram", self.folder)
        self.assertEqual((failure.exception.status_class, failure.exception.detail), ("login_wall", "empty_media_response"))

    def test_gallerydl_slides_in_order_with_sound(self):
        fake_tool(self.bin, "gallery-dl", """
out = pathlib.Path(args[args.index('-D') + 1])
for n in (2, 1, 3):
    (out / f'{n:03}.jpg').write_bytes(b'img%d' % n)
(out / '004.mp3').write_bytes(b'sound')
(out / '001.jpg.json').write_text(json.dumps({'id': '7430000000000000003', 'desc': '5 slides', 'author': {'uniqueId': 'slides.example'}, 'createTime': 1761062400}))
""")
        with mock.patch.dict(os.environ, with_path(self.bin)):
            post = gallerydl.fetch("https://www.tiktok.com/@slides.example/photo/7430000000000000003", "tiktok", self.folder)
        self.assertEqual([p.name for p in post.media], ["001.jpg", "002.jpg", "003.jpg"])
        self.assertEqual(post.audio.name, "004.mp3")
        self.assertEqual(post.author, "slides.example")
        self.assertEqual(post.infer_shape(), "carousel")


class ApifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = mock.patch.dict(os.environ, {"CONTENT_WATCH_HOME": str(self.root / "home"), "APIFY_TOKEN": "test-token"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_no_paid_run_without_a_standing_cap(self):
        opener = FakeOpener({})
        with self.assertRaises(FetchFailed) as failure:
            apify.fetch("https://www.instagram.com/p/CxYzSide01/", "instagram", self.root, Config(), actor_key="instagram_post", opener=opener)
        self.assertEqual(failure.exception.detail, "spend_not_approved")
        self.assertEqual(opener.calls, [])

    def test_cap_reached_stops_before_the_call(self):
        apify.record_spend(4.995)
        opener = FakeOpener({})
        config = Config(apify_enabled=True, apify_monthly_cap_usd=5.0)
        with self.assertRaises(FetchFailed) as failure:
            apify.fetch("https://www.instagram.com/p/x/", "instagram", self.root, config, actor_key="instagram_post", opener=opener)
        self.assertEqual(failure.exception.detail, "spend_cap_reached")
        self.assertEqual(opener.calls, [])

    def test_carousel_run_downloads_every_slide_and_records_spend(self):
        opener = FakeOpener({
            "https://api.apify.com/v2/acts/apify~instagram-scraper/": (FIXTURES / "apify_instagram_sidecar.json").read_bytes(),
            "https://scontent.cdninstagram.example/s1.jpg": b"one",
            "https://scontent.cdninstagram.example/s2.mp4": b"two",
            "https://scontent.cdninstagram.example/s3.jpg": b"three",
        })
        config = Config(apify_enabled=True, apify_monthly_cap_usd=5.0)
        post = apify.fetch("https://www.instagram.com/p/CxYzSide01/", "instagram", self.root, config,
                           actor_key="instagram_post", opener=opener)
        self.assertEqual([p.name for p in post.media],
                         ["instagram_CxYzSide01_01.jpg", "instagram_CxYzSide01_02.mp4", "instagram_CxYzSide01_03.jpg"])
        self.assertEqual(post.media[1].read_bytes(), b"two")
        body = json.loads(opener.calls[0][1])
        self.assertEqual(body, {"directUrls": ["https://www.instagram.com/p/CxYzSide01/"], "resultsType": "posts",
                                "resultsLimit": 1, "addParentData": False})
        self.assertAlmostEqual(apify.month_spend(), 0.01)

    def test_out_of_credit_is_blocked(self):
        opener = FakeOpener({"https://api.apify.com/": 402})
        config = Config(apify_enabled=True, apify_monthly_cap_usd=5.0)
        with self.assertRaises(FetchFailed) as failure:
            apify.fetch("https://www.tiktok.com/@a/video/1", "tiktok", self.root, config, actor_key="tiktok", opener=opener)
        self.assertEqual((failure.exception.status_class, failure.exception.detail), ("blocked", "apify_out_of_credit"))


class ChainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.env = mock.patch.dict(os.environ, {"CONTENT_WATCH_HOME": str(self.root / "home")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_falls_through_to_the_page_and_names_files_by_platform_and_id(self):
        def page(url, folder, timeout=30):
            for n in (1, 2):
                (folder / f"x{n}.jpg").write_bytes(b"slide%d" % n)
            from content_watcher.post import Post
            return Post("tiktok", url, "7430000000000000003", "slides.example",
                        media=[folder / "x1.jpg", folder / "x2.jpg"], method="tiktok_page")

        with mock.patch.object(gallerydl, "fetch", side_effect=FetchFailed("blocked", "refused")), \
                mock.patch.object(tiktok_page, "fetch", side_effect=page) as fallback, \
                mock.patch.object(apify, "fetch") as paid:
            result = fetch("https://www.tiktok.com/@slides.example/photo/7430000000000000003", self.root / "got", Config(), resolve=False)
        self.assertTrue(fallback.called)
        self.assertFalse(paid.called)
        self.assertEqual([a.method for a in result.attempts], ["gallerydl", "tiktok_page"])
        self.assertEqual([p.name for p in result.post.media],
                         ["tiktok_7430000000000000003_01.jpg", "tiktok_7430000000000000003_02.jpg"])
        self.assertTrue((self.root / "got" / "tiktok_7430000000000000003" / "post.json").is_file())

    def test_every_method_failing_reports_the_most_telling_class(self):
        with mock.patch.object(ytdlp, "fetch", side_effect=FetchFailed("login_wall", "empty_media_response")), \
                mock.patch.object(apify, "fetch", side_effect=FetchFailed("blocked", "spend_not_approved")):
            result = fetch("https://www.instagram.com/reel/DAbCdEfGhIj/", self.root / "got", Config(), resolve=False)
        self.assertIsNone(result.post)
        self.assertEqual(result.status_class, "login_wall")
        self.assertEqual([a.outcome for a in result.attempts],
                         ["login_wall:empty_media_response", "blocked:spend_not_approved"])


if __name__ == "__main__":
    unittest.main()
