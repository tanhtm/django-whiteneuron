from unfold.sites import UnfoldAdminSite

from .forms import LoginForm


class BaseAdminSite(UnfoldAdminSite):
    login_form = LoginForm


base_admin_site = BaseAdminSite()
