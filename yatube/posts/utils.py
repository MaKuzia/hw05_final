from django.conf import settings
from django.core.paginator import Paginator


def paginate_posts(request, list_object):
    paginator = Paginator(list_object, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
