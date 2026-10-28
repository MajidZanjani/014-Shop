from django.apps import AppConfig
class AccessConfig(AppConfig):
    name='shop.access'
    def ready(self):
        from django.contrib.auth.signals import user_logged_in
        from .recovery import stamp_session_epoch
        user_logged_in.connect(stamp_session_epoch,dispatch_uid='shop.access.session_epoch',weak=False)
