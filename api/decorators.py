"""
Decorators for the API
"""

import functools

from flask import current_app, g, jsonify, request, url_for, wrappers

from . import errors
from .models import BucketList


def json(f):
    """
    Modifies result of passed in function to return pretty printed JSON
    Courtesy - Miguel Grinberg
    """
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        response = f(*args, **kwargs)
        status = None

        # extract status code
        if isinstance(response, tuple):
            response, status = response

        # return result if an error occurred
        if isinstance(response, wrappers.Response) and \
                response.status_code > 300:
            return response

        # convert result to json and return
        if not isinstance(response, dict):
            response = response.to_json()
        response = jsonify(response)
        if status is not None:
            response.status_code = status
        return response
    return wrapped


def authorized(f):
    """Verifies that user is authorized to access resource"""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if BucketList.query.get_or_404(kwargs['id']).creator_id == g.user.id:
            return f(*args, **kwargs)
        else:
            return errors.forbidden(
                "You do not have permission to access this resource")
    return wrapped


def paginate():
    """
    Paginates the result of passed in functions and returns as JSON
    courtesy - Miguel Grinberg
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # get the number of the page to be displayed from URL
            page = request.args.get('page', 1, type=int)

            # get the number of items to be displayed per page
            limit = min(request.args.get(
                'limit', current_app.config['DEFAULT_PER_PAGE'], type=int),
                current_app.config['MAX_PER_PAGE'])

            # get query, paginate the query and get content of query
            query = f(*args, **kwargs)
            pagination = query.paginate(page, limit)
            content = pagination.items

            # prepare the meta portion of the json response
            pages = {'page': page, 'limit': limit,
                     'total': pagination.total, 'pages': pagination.pages}
            if pagination.has_prev:
                pages['prev'] = url_for(request.endpoint,
                                        page=pagination.prev_num, limit=limit,
                                        _external=True, **kwargs)
            else:
                pages['prev'] = None

            if pagination.has_next:
                pages['next'] = url_for(request.endpoint,
                                        page=pagination.next_num, limit=limit,
                                        _external=True, **kwargs)
            else:
                pages['next'] = None

            pages['first'] = url_for(request.endpoint, page=1,
                                     limit=limit, _external=True,
                                     **kwargs)
            pages['last'] = url_for(request.endpoint, pages=pagination.pages,
                                    limit=limit, _external=True,
                                    **kwargs)
            return jsonify({
                'meta': pages,
                'bucketlists': [each.to_json() for each in content]
            })
        return wrapped
    return decorator
