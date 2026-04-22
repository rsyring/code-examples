from doist import views
from doist.libs.sync import SyncAPI
from doist.libs.testing import mock_patch_obj


class TestViews:
    def test_hello(self, web):
        resp = web.get('/')
        assert resp.text == "'sup yos"

    @mock_patch_obj(views, 'actions')
    def test_hooks_action(sef, m_actions, web):
        web.post_json('/hooks', params='foobar')

        m_actions.on_webhook.assert_called_once_with('foobar')

    def test_healthy_db_ok(self, web):
        resp = web.get('/healthy-db')
        assert resp.status_code == 200
        assert resp.text == 'doist ok'

    @mock_patch_obj(views.sa, 'text')
    def test_healthy_db_failed(self, m_text, web):
        m_text.side_effect = Exception('foo')
        resp = web.get('/healthy-db', status=503)

        assert resp.text == 'failed'

    @mock_patch_obj(SyncAPI, 'user')
    def test_healthy_api_ok(self, m_user, web):
        resp = web.get('/healthy-api')

        assert resp.status_code == 200
        assert resp.text == 'doist api ok'
        m_user.assert_called_once()

    @mock_patch_obj(SyncAPI, 'user')
    def test_healthy_api_failed(self, m_user, web):
        m_user.side_effect = Exception('foo')
        resp = web.get('/healthy-api', status=503)

        assert resp.text == 'failed'
