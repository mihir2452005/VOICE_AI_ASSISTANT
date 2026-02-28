from actions.system_actions import get_current_time, open_application, open_website, create_file, create_pdf, create_presentation, check_pc_health
from actions.web_actions import search_web, read_webpage
from actions.memory_actions import remember_fact, recall_facts
from actions.gui_actions import click_on_target, analyze_screen

def get_all_tools():
    """
    Returns a list of all python functions that are available for Gemini to call.
    The google-genai SDK natively accepts a list of callable functions.
    """
    return [
        get_current_time,
        open_application,
        open_website,
        create_file,
        create_pdf,
        create_presentation,
        search_web,
        read_webpage,
        check_pc_health,
        remember_fact,
        recall_facts,
        click_on_target,
        analyze_screen
    ]
