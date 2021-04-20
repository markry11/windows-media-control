import winrt.windows.media.control as wmc
from datetime import datetime
from windows_media_control import MediaManager
from termcolor import colored

def on_new_source(session):
    if session is not None:
        print_log(f'-- New Source: {session.source_app_user_model_id}', 'red')

def on_removed_source(session):
    if session is not None:
        print_log(f'-- Removed Source: {session.source_app_user_model_id}', 'green')

def on_current_session_changed(session):
    if session is not None:
        print_log(f"Current source: {session.source_app_user_model_id}", 'yellow')

def on_media_properties_change(sender, args):
    print_log(f"{sender.source_app_user_model_id} is now playing {args.title} {'' if not args.artist else f'by {args.artist}'}", 'cyan')

def on_playback_info_changed(sender, args):
    print_log(f"{sender.source_app_user_model_id} is now {to_playback_status_enum(args.playback_status).name}", 'magenta')

def print_log(msg, color = 'white'):
    timestamp = datetime.now().strftime('%H:%M:%S:%f')
    print(colored(f"[{timestamp}] {msg}", color))

def to_playback_status_enum(value):
    try: return wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus(value)
    except: return value

if __name__ == "__main__":
    MediaManager.set_on_new_session(on_new_source)
    MediaManager.set_on_playback_info_changed(on_playback_info_changed)
    MediaManager.set_on_removed_source(on_removed_source)
    MediaManager.set_on_media_properties_changed(on_media_properties_change)
    MediaManager.set_on_current_session_changed(on_current_session_changed)
    MediaManager.start(send_mpc_after_csc = True)
    while True: pass