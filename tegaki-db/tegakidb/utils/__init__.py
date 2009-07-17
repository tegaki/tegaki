from django.shortcuts import render_to_response
from django.template import RequestContext


def render_to(template_name):
    def renderer(func):
        def wrapper(request, *args, **kw):
            output = func(request, *args, **kw)
            if not isinstance(output, dict):
                return output
            return render_to_response(template_name, output, context_instance = RequestContext(request))
        return wrapper
    return renderer


from tegakidb import settings 
 
#custom template processor that allows us to host the tegaki-db project
#from different locations i.e. http://mydomain.com/tegaki/ or http://tegaki.com/
def base_url(request):
    return {'BASE_URL':settings.BASE_URL}


### Dojango helper for our custom views ###
from django.db import models
from dojango.views import AVAILABLE_OPTS
import operator

#handles the dojango magic for doing queries on models to pass back and forth to dojo
def datagrid_helper(model, request):
     # start with a very broad query set
    target = model.objects.all()

    # modify query set based on the GET params, dont do the start/count splice
    # until after all clauses added
    if request.GET.has_key('sort'):
        target = target.order_by(request.GET['sort'])

    if request.GET.has_key('search') and request.GET.has_key('search_fields'):
        ored = [models.Q(**{str(k).strip(): str(request.GET['search'])} ) for k in request.GET['search_fields'].split(",")]
        target = target.filter(reduce(operator.or_, ored))

    # custom options passed from "query" param in datagrid
    for key in [ d for d in request.GET.keys() if not d in AVAILABLE_OPTS]:
        target = target.filter(**{str(key):request.GET[key]})
    num = target.count()
    # get only the limit number of models with a given offset
    target=target[request.GET['start']:int(request.GET['start'])+int(request.GET['count'])]

    return target, num


#opposite of cgi.escape()
import re
def htmldecode(text):
        """Decode HTML entities in the given text."""
        if type(text) is unicode:
                uchr = unichr
        else:
                uchr = lambda value: value > 255 and unichr(value) or chr(value)
        def entitydecode(match, uchr=uchr):
                entity = match.group(1)
                if entity.startswith('#x'):
                        return uchr(int(entity[2:], 16))
                elif entity.startswith('#'):
                        return uchr(int(entity[1:]))
                elif entity in name2codepoint:
                        return uchr(name2codepoint[entity])
                else:
                        return match.group(0)
        charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')
        return charrefpat.sub(entitydecode, text)

