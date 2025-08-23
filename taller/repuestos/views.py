
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.http import HttpResponse, JsonResponse
import json
import logging

from taller.models.repuesto import Repuesto
from taller.models.tienda import Tienda

from .views_cbv import (
    RepuestoListView, RepuestoDetailView, RepuestoCreateView, RepuestoUpdateView,
)

log = logging.getLogger(__name__)

def lista_repuestos(request, *args, **kwargs):
    log.info("FBV shim: lista_repuestos")
    return RepuestoListView.as_view()(request, *args, **kwargs)

def ver_repuesto(request, *args, **kwargs):
    log.info("FBV shim: ver_repuesto")
    return RepuestoDetailView.as_view()(request, *args, **kwargs)

def crear_repuesto(request, *args, **kwargs):
    log.info("FBV shim: crear_repuesto")
    return RepuestoCreateView.as_view()(request, *args, **kwargs)

def editar_repuesto(request, *args, **kwargs):
    log.info("FBV shim: editar_repuesto")
    return RepuestoUpdateView.as_view()(request, *args, **kwargs)
