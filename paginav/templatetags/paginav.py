import re
from django import template
from django.http import HttpRequest, QueryDict
from django.template.loader import render_to_string

RE_URL = re.compile(r'(.*)1(.*)')
register = template.Library()

def page_separator(current, count, adjacent, caps):
    if current < adjacent + 1:
        adjacent += adjacent - current + 1
    elif count - current < adjacent:
        adjacent += adjacent - (count - current)
    bits = []
    if current > (1 + adjacent + caps):
        if caps:
            bits.append(range(1, caps + 1))
        start = current - adjacent
    else:
        start = 1
    if current + adjacent < count - caps:
        end = current + adjacent
    else:
        end = count
    bits.append(range(start, end + 1))
    if end != count:
        if caps:
            bits.append(range(count - caps + 1, count + 1))
    return bits

@register.simple_tag(takes_context=True)
def paginav(context, page, template='paginav.html', adjacent=3, caps=1, url=None, first_url=None, page_var='page'):
    if not page:
        return ''
    num_pages = page.paginator.num_pages
    if num_pages < 2:
        return render_to_string(template, {'num_pages': num_pages})

    current = page.number
    pages = []
    for page_group in page_separator(current, num_pages, adjacent=adjacent, caps=caps):
        group = []
        for number in page_group:
            page_url = build_url(context, number, url, first_url, page_var)
            if not page_url:
                return ''
            group.append({'url': page_url, 'number': number, 'current': current == number})
        pages.append(group)

    context = {
        'num_pages': num_pages,
        'pages': pages,
    }

    if current > 1:
        context['previous_url'] = build_url(context, current - 1, url, first_url, page_var)
    if current < num_pages:
        context['next_url'] = build_url(context, current + 1, url, first_url, page_var)

    return render_to_string(template, context)

def build_url(context, number, url, first_url, page_var):
    if number == 1 and first_url:
        return first_url
    match = url and RE_URL.match(url)
    if match:
        start, end = match.groups()
        return f'{start}{number}{end}'

    request = context.get('request')
    if isinstance(request, HttpRequest):
        querydict = request.GET
    else:
        querydict = QueryDict('')
    qs = querydict.copy()
    if number == 1:
        qs.pop(page_var, None)
    else:
        qs[page_var] = number
    qs = qs.urlencode()
    if qs:
        qs = f'?{qs}'
    if not url and not qs:
        return '.'
    return f'{url or ""}{qs}'
