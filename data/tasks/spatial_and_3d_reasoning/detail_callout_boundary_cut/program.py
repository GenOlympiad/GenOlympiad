# code: helpers
from genolympiad.task_helpers import count_confirmed_cutouts
# end of helpers

# code: code_carried
def groove_end_agrees(callout_read, detail_read, want):
    """Say yes when the main view and the detail both show the groove end the reference expects."""
    def one(node):
        s = str(((node or {}).get('answers') or [''])[0]).strip().lower()
        return 'stops' if s.startswith('stop') else ('runs-out' if s.startswith('run') else ('none' if s.startswith('non') else ''))
    target = 'runs-out' if str(want).strip().lower().startswith('n') else 'stops'
    main_view, detail_view = one(callout_read), one(detail_read)
    ok = 'yes' if main_view and detail_view and main_view == detail_view and detail_view == target else 'no'
    return {'ok': ok, 'in_main_view': main_view, 'in_detail': detail_view,
            'verdict': 'the top groove inside the window: %s on the main view, %s in the detail'
                       % (main_view or '?', detail_view or '?')}

# end of code_carried
