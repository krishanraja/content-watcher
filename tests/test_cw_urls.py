import unittest

from content_watcher import urls
from tests.cw_helpers import FakeOpener


class UrlTests(unittest.TestCase):
    def test_instagram_forms_share_one_key(self):
        for pasted in (
            "https://www.instagram.com/reel/DAbCdEfGhIj/?igsh=MWQ1ZGUxMzBkMA==",
            "instagram.com/reels/DAbCdEfGhIj",
            "https://www.instagram.com/studio.example/reel/DAbCdEfGhIj/?utm_source=ig_web_copy_link",
        ):
            link = urls.parse(pasted)
            self.assertEqual(link.platform, "instagram")
            self.assertEqual(link.url, "https://www.instagram.com/reel/DAbCdEfGhIj/")
            self.assertEqual(link.post_id, "DAbCdEfGhIj")
            self.assertEqual(link.kind, "reel")
        post = urls.parse("https://www.instagram.com/p/CxYzSide01/?img_index=2")
        self.assertEqual((post.url, post.kind), ("https://www.instagram.com/p/CxYzSide01/", "post"))

    def test_tiktok_video_photo_and_short_links(self):
        video = urls.parse("https://www.tiktok.com/@maker.example/video/7430000000000000001?is_from_webapp=1&sender_device=pc")
        self.assertEqual(video.url, "https://www.tiktok.com/@maker.example/video/7430000000000000001")
        self.assertEqual(video.kind, "video")
        photo = urls.parse("https://www.tiktok.com/@slides.example/photo/7430000000000000003?_r=1&_t=abc")
        self.assertEqual(photo.kind, "photo")
        for short in ("https://vm.tiktok.com/ZMabc123/", "https://vt.tiktok.com/ZSxyz/", "https://www.tiktok.com/t/ZTabc/"):
            self.assertTrue(urls.parse(short).needs_resolve, short)

    def test_youtube_forms(self):
        self.assertEqual(urls.parse("https://youtu.be/dQw4w9WgXcQ?si=abc").url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(urls.parse("https://m.youtube.com/watch?v=dQw4w9WgXcQ&feature=share&t=10").url,
                         "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        short = urls.parse("https://youtube.com/shorts/abcdefghijk?si=x")
        self.assertEqual((short.url, short.kind), ("https://www.youtube.com/shorts/abcdefghijk", "short"))

    def test_linkedin_forms(self):
        post = urls.parse("https://www.linkedin.com/posts/pat-example_decks-activity-7250000000000000000-AbCd?utm_source=share&rcm=x")
        self.assertEqual(post.post_id, "7250000000000000000")
        self.assertEqual(post.url, "https://www.linkedin.com/posts/pat-example_decks-activity-7250000000000000000-AbCd/")
        feed = urls.parse("https://www.linkedin.com/feed/update/urn:li:activity:7250000000000000000/")
        self.assertEqual(feed.post_id, "7250000000000000000")
        self.assertTrue(urls.parse("https://lnkd.in/gAbCdEf").needs_resolve)

    def test_resolve_follows_the_landing_url(self):
        opener = FakeOpener({"https://vm.tiktok.com/": b""})
        # FakeOpener reports the requested URL as the landing URL; give it a landing route instead.
        class Landing(FakeOpener):
            def open(self, request, timeout=None):
                response = super().open(request, timeout)
                response._url = "https://www.tiktok.com/@maker.example/video/7430000000000000001?_r=1"
                return response
        link = urls.normalise("https://vm.tiktok.com/ZMabc123/", opener=Landing({"https://vm.tiktok.com/": b""}))
        self.assertEqual(link.url, "https://www.tiktok.com/@maker.example/video/7430000000000000001")
        self.assertEqual(link.post_id, "7430000000000000001")
        self.assertIsNotNone(opener)

    def test_platform_of_others(self):
        self.assertEqual(urls.platform_of("https://x.com/a/status/1"), "x")
        self.assertEqual(urls.platform_of("https://www.threads.net/@a/post/1"), "threads")
        self.assertEqual(urls.platform_of("https://example.com/a"), "web")


if __name__ == "__main__":
    unittest.main()
