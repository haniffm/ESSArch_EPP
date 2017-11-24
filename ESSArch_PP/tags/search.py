from __future__ import division

import datetime
import math

from django_filters.constants import EMPTY_VALUES

from elasticsearch.exceptions import TransportError
from elasticsearch_dsl import Index, Q, FacetedSearch, TermsFacet, Search

from rest_framework import exceptions
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from six import iteritems

from ESSArch_Core.mixins import PaginatedViewMixin
from ESSArch_Core.search import get_connection, DEFAULT_MAX_RESULT_WINDOW


class TagSearch(FacetedSearch):
    index = 'tags'
    doc_types = None
    fields = ['name', 'reference_code']

    facets = {
        # use bucket aggregations to define facets
        'parents': TermsFacet(field='parents'),
        'type': TermsFacet(field='_type'),
    }

    def __init__(self, *args, **kwargs):
        self.start_date = kwargs.pop('start_date', None)
        self.end_date = kwargs.pop('end_date', None)

        def validate_date(d):
            try:
                return datetime.datetime.strptime(d, '%Y')
            except ValueError:
                try:
                    return datetime.datetime.strptime(d, '%Y-%m')
                except ValueError:
                    try:
                        return datetime.datetime.strptime(d, '%Y-%m-%d')
                    except ValueError:
                        raise exceptions.ParseError('Invalid date format, should be YYYY[-MM-DD]')

        if self.start_date not in EMPTY_VALUES:
            self.start_date = self.start_date.zfill(4)
            self.start_date = validate_date(self.start_date)

        if self.end_date not in EMPTY_VALUES:
            self.end_date = self.end_date.zfill(4)
            self.end_date = validate_date(self.end_date)

        if self.start_date not in EMPTY_VALUES and self.end_date not in EMPTY_VALUES:
            if self.start_date > self.end_date:
                raise exceptions.ParseError('start_date cannot be set to date after end_date')

        super(TagSearch, self).__init__(*args, **kwargs)

    def search(self):
        """
        We override this to add filters on start and end date
        """

        s = super(TagSearch, self).search()

        if self.start_date not in EMPTY_VALUES:
            s = s.filter('range', end_date={'gte': self.start_date})

        if self.end_date not in EMPTY_VALUES:
            s = s.filter('range', start_date={'lte': self.end_date})

        return s

    def aggregate(self, search):
        """
        Add aggregations representing the facets selected, including potential
        filters.

        We override this to also aggregate on fields in `facets`
        """
        for f, facet in iteritems(self.facets):
            agg = facet.get_aggregation()
            agg_filter = Q('match_all')
            for field, filter in iteritems(self._filters):
                agg_filter &= filter
            search.aggs.bucket(
                '_filter_' + f,
                'filter',
                filter=agg_filter
            ).bucket(f, agg)

    def highlight(self, search):
        """
        We override this to set the highlighting options
        """

        pre_tags = ["<strong>"]
        post_tags = ["</strong>"]
        search = search.highlight_options(pre_tags=pre_tags, post_tags=post_tags, require_field_match=True)
        return super(TagSearch, self).highlight(search)


class TagSearchViewSet(ViewSet, PaginatedViewMixin):
    index = TagSearch.index
    lookup_field = 'pk'
    lookup_url_kwarg = None

    def __init__(self, *args, **kwargs):
        get_connection('default')
        super(TagSearchViewSet, self).__init__(*args, **kwargs)

    def get_object(self):
        """
        Returns the object the view is displaying.
        """

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        # Search for object in index by id
        id = self.kwargs[lookup_url_kwarg]
        s = Search(index=self.index).query("match", _id=id)
        res = s.execute()
        try:
            serialized = res.hits[0].to_dict()
            meta = res.hits[0].meta
            serialized['_type'] = meta.doc_type
            serialized['_id'] = meta.id
            serialized['_index'] = meta.index
            return serialized
        except (IndexError, KeyError):
            raise exceptions.NotFound

    def list(self, request):
        params = {key: value[0] for (key, value) in dict(request.query_params).iteritems()}
        query = params.pop('q', '')
        if query:
            query = '%s' % query

        filters = {'type': params.pop('type', None)}

        s = TagSearch(query, filters=filters, start_date=params.get('start_date'), end_date=params.get('end_date'))

        if self.paginator is not None:
            # Paginate in search engine
            number = params.get(self.paginator.pager.page_query_param, 1)
            size = params.get(self.paginator.pager.page_size_query_param, 10)

            try:
                number = int(number)
            except (TypeError, ValueError):
                raise exceptions.NotFound('Invalid page.')
            if number < 1:
                raise exceptions.NotFound('Invalid page.')

            size = int(size)
            offset = (number-1)*size
            max_results = int(Index('tags').get_settings()['tags']['settings']['index'].get('max_result_window', DEFAULT_MAX_RESULT_WINDOW))
            s[offset:offset+size]

        try:
            results = s.execute()
        except TransportError:
            if self.paginator is not None:
                if offset+size > max_results:
                    raise exceptions.ParseError("Can't show more than {max} results".format(max=max_results))

            raise

        if self.paginator is not None:
            if results.hits.total > 0 and number > math.ceil(results.hits.total/size):
                raise exceptions.NotFound('Invalid page.')

        results_dict = results.to_dict()
        r = {
            'hits': results_dict['hits']['hits'],
            'aggregations': results_dict['aggregations'],
        }

        if self.paginator is not None:
            return Response(r, headers={'Count': results.hits.total})

        return Response(r)

    def retrieve(self, request, pk=None):
        return Response(self.get_object())

    @detail_route(methods=['get'])
    def children(self, request, pk=None):
        s = Search(index=self.index).sort('reference_code')

        try:
            tree_id = request.query_params['tree_id']
        except KeyError:
            raise exceptions.ParseError('tree_id parameter missing')

        p = {'parents.%s' % tree_id: {'query': pk, 'operator': 'and'}}
        s = s.query('match', **p)

        if self.paginator is not None:
            # Paginate in search engine
            number = request.query_params.get(self.paginator.pager.page_query_param, 1)
            size = request.query_params.get(self.paginator.pager.page_size_query_param, 10)

            try:
                number = int(number)
            except (TypeError, ValueError):
                raise exceptions.NotFound('Invalid page.')
            if number < 1:
                raise exceptions.NotFound('Invalid page.')

            size = int(size)
            offset = (number-1)*size
            max_results = int(Index('tags').get_settings()['tags']['settings']['index'].get('max_result_window', DEFAULT_MAX_RESULT_WINDOW))
            s = s[offset:offset+size]

        try:
            results = s.execute()
        except TransportError:
            if self.paginator is not None:
                if offset+size > max_results:
                    raise exceptions.ParseError("Can't show more than {max} results".format(max=max_results))

            raise

        if self.paginator is not None:
            if results.hits.total > 0 and number > math.ceil(results.hits.total/size):
                raise exceptions.NotFound('Invalid page.')

        results_dict = results.to_dict()
        r = results_dict['hits']['hits']

        if self.paginator is not None:
            return Response(r, headers={'Count': results.hits.total})

        return Response(r)