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
            "ERROR: [Instagram] DAbC: Instagram sent an empty media response. Use --cookies": "blocked",
            "ERROR: [Instagram] x: You have exceeded the rate-limit for accessing posts anonymously. Use --cookies": "blocked",
            "ERROR: [Instagram] x: Restricted Video: You must be 18 years old": "login_wall",
            "ERROR: [TikTok] 1: Video not available, status code 10204": "blocked",
            "ERROR: [TikTok] 1: Video not available, status code 10216": "not_found",
            "ERROR: unable to download video data: HTTP Error 403: Forbidden": "blocked",
            "ERROR: HTTP Error 429: Too Many Requests": "blocked",
            "ERROR: [youtube] x: Sign in to confirm you're not a bot": "blocked",
            "ERROR: [youtube] x: Private video. Sign in if you've been granted access": "login_wall",
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
        with self.assertRaises(FetchFailed) as ip:
            tiktok_page.item_struct((FIXTURES / "tiktok_ipblocked_page.html").read_text())
        self.assertEqual((ip.exception.status_class, ip.exception.detail), ("blocked", "ip_blocked"))
        with self.assertRaises(FetchFailed) as challenge:
            tiktok_page.item_struct((FIXTURES / "tiktok_challenge_page.html").read_text())
        self.assertEqual(challenge.exception.status_class, "blocked")

    def test_apify_instagram_items_keep_post_order(self):
        meta, media = apify.instagram_parts(load("apify_instagram_sidecar.json")[0])
        self.assertEqual(meta["author"], "carousel.example")
        self.assertEqual([ext for _, ext in media], [".jpg", ".mp4", ".jpg"])
        self.assertIn("s2.mp4", media[1][0])
        meta, media = apify.instagram_parts(load("apify_instagram_reel.json")[0])
        self.assertEqual(media[0][0], "https://scontent.cdninstagram.example/r.mp4")  # the CDN file, no paid stored copy
        with self.assertRaises(FetchFailed) as wrong:
            apify.instagram_parts(load("apify_instagram_reel.json")[0], expected_id="SomethingElse")
        self.assertEqual(wrong.exception.detail, "apify_wrong_item")
        with self.assertRaises(FetchFailed) as blocked:
            apify.instagram_parts({"requestErrorMessages": ["Error: BLOCKED"]})
        self.assertEqual(blocked.exception.status_class, "blocked")
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
        self.assertEqual(found["text"], "Most decks fail on slide one.")  # the commentary element comes first
        self.assertEqual(len(found["images"]), 1)  # one picture, at its largest size
        self.assertIn("feedshare-shrink_1280", found["images"][0])
        self.assertEqual(found["shape"], "image")
        video = linkedin_page.parse_page((FIXTURES / "linkedin_video_post.html").read_text())
        self.assertEqual(video["author"], "Maker Co")  # a VideoObject's author is its creator
        self.assertEqual(video["posted_at"], "2026-10-18T09:00:00.000Z")  # and its date is uploadDate
        self.assertTrue(video["video"].endswith("mp4-720p?e=2147483647"))  # the largest rendition
        self.assertEqual(video["text"], "The cloud, explained.\nNo jargon.")
        self.assertEqual(video["caption_url"], "https://dms.licdn.example/captions/X.vtt")
        self.assertEqual(video["counts"], {"likes": 120, "comments": 7})
        self.assertEqual(video["shape"], "video")
        with self.assertRaises(FetchFailed) as nobody:
            linkedin_page.parse_page('<html><head><meta property="og:description" content="Sign up"></head></html>')
        self.assertIn(nobody.exception.status_class, ("login_wall", "other"))  # never filed as the post
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
        # Use the stand-in programs on PATH instead of the installed modules.
        self.modules = mock.patch.dict(base.MODULES, clear=True)
        self.modules.start()
        self.addCleanup(self.modules.stop)

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
        self.assertEqual((failure.exception.status_class, failure.exception.detail), ("blocked", "empty_media_response"))

    def test_ytdlp_carousel_keeps_every_slide_in_order(self):
        fake_tool(self.bin, "yt-dlp", """
out = args[args.index('-o') + 1]
assert '--ignore-no-formats-error' in args and '--write-thumbnail' in args and '--no-playlist' not in args
folder = pathlib.Path(out).parent
(folder / 'CxYz_01.jpg').write_bytes(b'one')
(folder / 'CxYz_02.mp4').write_bytes(b'two')
(folder / 'CxYz_02.jpg').write_bytes(b'thumb of two')
(folder / 'CxYz_03.webp').write_bytes(b'three')
(folder / 'CxYz.info.json').write_text(json.dumps({'_type': 'playlist', 'id': 'CxYz', 'playlist_count': 3, 'channel': 'carousel.example', 'description': 'Five ways'}))
""")
        with mock.patch.dict(os.environ, with_path(self.bin)):
            post = ytdlp.fetch_carousel("https://www.instagram.com/p/CxYz/", "instagram", self.folder)
        self.assertEqual([p.name for p in post.media], ["CxYz_01.jpg", "CxYz_02.mp4", "CxYz_03.webp"])
        self.assertEqual(post.shape, "carousel")
        self.assertEqual(post.author, "carousel.example")

    def test_ytdlp_carousel_missing_a_slide_fails_on(self):
        fake_tool(self.bin, "yt-dlp", """
folder = pathlib.Path(args[args.index('-o') + 1]).parent
(folder / 'CxYz_01.jpg').write_bytes(b'one')
(folder / 'CxYz.info.json').write_text(json.dumps({'_type': 'playlist', 'id': 'CxYz', 'playlist_count': 3}))
""")
        with mock.patch.dict(os.environ, with_path(self.bin)), self.assertRaises(FetchFailed) as failure:
            ytdlp.fetch_carousel("https://www.instagram.com/p/CxYz/", "instagram", self.folder)
        self.assertEqual(failure.exception.detail, "ig_missing_slides")

    def test_youtube_asks_for_the_spoken_language_never_a_translation(self):
        fake_tool(self.bin, "yt-dlp", """
assert args[args.index('--sub-langs') + 1] == '.*-orig', args
base = args[args.index('-o') + 1].replace('%(id)s', 'dQw4w9WgXcQ').rsplit('.', 1)[0]
pathlib.Path(base + '.mp4').write_bytes(b'v')
pathlib.Path(base + '.en.vtt').write_text('WEBVTT')
pathlib.Path(base + '.de-orig.vtt').write_text('WEBVTT')
pathlib.Path(base + '.info.json').write_text(json.dumps({'id': 'dQw4w9WgXcQ', 'channel': 'C'}))
""")
        with mock.patch.dict(os.environ, with_path(self.bin)):
            post = ytdlp.fetch("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube", self.folder, captions="youtube")
        self.assertTrue(post.captions_file.name.endswith(".de-orig.vtt"))

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
            apify.fetch("https://www.instagram.com/p/CxYzSide01/", "instagram", self.root, Config(apify_enabled=False),
                        actor_key="instagram_post", opener=opener)
        self.assertEqual(failure.exception.detail, "spend_not_approved")
        self.assertEqual(opener.calls, [])

    def test_the_standing_cap_is_five_dollars(self):
        self.assertTrue(Config().apify_enabled)
        self.assertEqual(Config().apify_monthly_cap_usd, 5.0)

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

    def test_tiktok_runs_are_started_then_polled(self):
        polls = iter([b'{"data": {"id": "run1", "status": "RUNNING"}}',
                      b'{"data": {"id": "run1", "status": "SUCCEEDED", "defaultDatasetId": "ds1"}}'])
        opener = FakeOpener({
            "https://api.apify.com/v2/acts/clockworks~tiktok-video-scraper/runs": b'{"data": {"id": "run1", "status": "READY"}}',
            "https://api.apify.com/v2/actor-runs/run1": lambda request: next(polls),
            "https://api.apify.com/v2/datasets/ds1/items": (FIXTURES / "apify_tiktok_video.json").read_bytes(),
            "https://api.apify.example/v2/key-value-stores/k/records/video.mp4": b"video",
            "https://api.apify.example/sub.vtt": b"WEBVTT",
        })
        config = Config(apify_enabled=True, apify_monthly_cap_usd=5.0)
        with mock.patch.object(apify.time, "sleep"):
            post = apify.fetch("https://www.tiktok.com/@tt.video/video/7430000000000000005", "tiktok", self.root,
                               config, actor_key="tiktok", opener=opener)
        self.assertEqual(post.media[0].read_bytes(), b"video")
        started = json.loads(opener.calls[0][1])
        self.assertNotIn("videoKvStoreIdOrName", started)  # nothing left on his Apify account to delete
        self.assertNotIn("run-sync", opener.calls[0][0])
        self.assertAlmostEqual(apify.month_spend(), 0.01)

    def test_a_run_that_times_out_still_counts_against_the_cap(self):
        opener = FakeOpener({"https://api.apify.com/": 408})
        config = Config(apify_enabled=True, apify_monthly_cap_usd=5.0)
        with self.assertRaises(FetchFailed):
            apify.fetch("https://www.instagram.com/reel/x/", "instagram", self.root, config, actor_key="instagram_reel", opener=opener)
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

    def test_every_method_failing_reports_the_last_steps_class(self):
        with mock.patch.object(ytdlp, "fetch", side_effect=FetchFailed("blocked", "empty_media_response")), \
                mock.patch.object(apify, "fetch", side_effect=FetchFailed("not_found", "apify_not_found")):
            result = fetch("https://www.instagram.com/reel/DAbCdEfGhIj/", self.root / "got", Config(), resolve=False)
        self.assertIsNone(result.post)
        self.assertEqual(result.status_class, "not_found")
        self.assertEqual([a.outcome for a in result.attempts],
                         ["blocked:empty_media_response", "not_found:apify_not_found"])

    def test_chains_follow_the_spec_order(self):
        from content_watcher import urls
        from content_watcher.fetch import _methods
        names = lambda link: [name for name, _ in _methods(urls.parse(link), Config())]
        self.assertEqual(names("https://www.instagram.com/reel/DAbC/"), ["ytdlp", "apify_instagram_reel"])
        self.assertEqual(names("https://www.instagram.com/p/CxYz/"), ["ytdlp_carousel", "apify_instagram_post"])
        self.assertEqual(names("https://www.tiktok.com/@a/video/1"), ["ytdlp", "gallerydl", "tiktok_page", "apify_tiktok"])
        self.assertEqual(names("https://www.tiktok.com/@a/photo/1"), ["gallerydl", "tiktok_page", "apify_tiktok"])
        self.assertEqual(names("https://youtu.be/dQw4w9WgXcQ"), ["ytdlp", "ytdlp_mweb"])
        self.assertEqual(names("https://www.linkedin.com/feed/update/urn:li:activity:7250000000000000000/"), ["linkedin_guest_page"])

    def test_a_link_that_is_not_a_post_stops_at_once(self):
        with mock.patch.object(ytdlp, "fetch") as never:
            result = fetch("https://www.instagram.com/studio.example/", self.root / "got", Config(), resolve=False)
        self.assertFalse(never.called)
        self.assertEqual((result.status_class, result.detail), ("not_found", "unsupported_url"))


if __name__ == "__main__":
    unittest.main()
