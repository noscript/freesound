#
# Freesound is (c) MUSIC TECHNOLOGY GROUP, UNIVERSITAT POMPEU FABRA
#
# Freesound is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Freesound is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     See AUTHORS file.
#

from django.core.paginator import Paginator, InvalidPage
from django.core.cache import cache
import hashlib

# count caching solution from http://timtrueman.com/django-pagination-count-caching/
class CachedCountProxy(object):
    ''' This allows us to monkey-patch count() on QuerySets so we can cache it and speed things up.
    '''

    def __init__(self, queryset):
        self._queryset = queryset
        self._queryset._original_count = self._queryset.count
        self._sql = self._queryset.query.get_compiler(self._queryset.db).as_sql()
        self._sql = self._sql[0] % self._sql[1]

    def __call__(self):
        ''' 1. Check cache
            2. Return cache if it's set
            3. If it's not set, call super and get the count
            4. Cache that for X seconds
        '''
        key = "paginator_count_%s" % hashlib.sha224(self._sql).hexdigest()
        count = cache.get(key)
        if count is None:
            count = self._queryset._original_count()
            cache.set(key, count, 300)
        return count

class CountProvidedPaginator(Paginator):
    """ A django Paginator that takes an optional object_count
        which is the length of object_list. This means that count() or
        len() doesn't have to be called """

    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, object_count=None):
        Paginator.__init__(self, object_list, per_page, orphans, allow_empty_first_page)
        self._count = object_count


def paginate(request, qs, items_per_page=20, page_get_name='page', cache_count=False, object_count=None):
    # monkeypatch solution to cache the count for performance
    # disabled for now, causes problems on comments.
    if cache_count:
        qs.count = CachedCountProxy(qs)

    paginator = CountProvidedPaginator(qs, items_per_page, object_count=object_count)
    try:
        current_page = int(request.GET.get(page_get_name, 1))
    except ValueError:
        current_page = 1

    try:
        page = paginator.page(current_page)
    except InvalidPage:
        page = paginator.page(1)
        current_page = 1

    return dict(paginator=paginator, current_page=current_page, page=page)
