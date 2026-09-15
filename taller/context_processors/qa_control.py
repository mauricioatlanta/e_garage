from taller.qa_control.auth import is_control_tower_user
from taller.qa_control.context import get_qa_control_context, resolve_qa_empresa


def qa_control(request):
    authorized = is_control_tower_user(getattr(request, "user", None))
    context = get_qa_control_context(request) if authorized else None
    return {
        "qa_control_authorized": authorized,
        "qa_control_context": context,
        "qa_control_empresa": resolve_qa_empresa(request) if authorized else None,
    }
