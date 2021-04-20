import winrt.windows.media.control as wmc
from asgiref.sync import async_to_sync

class MediaManager:
    __on_new_source = None
    __on_removed_source = None
    __on_playback_info_changed = None
    __on_media_properties_changed = None
    __on_current_session_changed = None
    __is_started = False
    __current_media_sessions = {}
    __mpc_tokens = {}
    __pic_tokens = {}
    __send_mpc_after_csc = False
    def set_on_new_session(func):
        MediaManager.__on_new_source = func

    def set_on_removed_source(func):
        MediaManager.__on_removed_source = func

    def set_on_playback_info_changed(func):
        MediaManager.__on_playback_info_changed = func

    def set_on_media_properties_changed(func):
        MediaManager.__on_media_properties_changed = func

    def set_on_current_session_changed(func):
        MediaManager.__on_current_session_changed = func

    def start(send_mpc_after_csc = False):
        if not MediaManager.__is_started:
            MediaManager.__send_mpc_after_csc = send_mpc_after_csc
            session_manager = async_to_sync(wmc.GlobalSystemMediaTransportControlsSessionManager.request_async)()
            MediaManager.__on_sessions_changed(session_manager)
            session_manager.add_sessions_changed(MediaManager.__on_sessions_changed)
            if MediaManager.__on_current_session_changed:
                session_manager.add_current_session_changed(MediaManager.__handle_current_session_changed)
            MediaManager.__is_started = True

    def __handle_current_session_changed(sender, args = None):
            session = sender.get_current_session()
            MediaManager.__on_current_session_changed(session)
            if MediaManager.__send_mpc_after_csc:
                MediaManager.MediaSession.on_media_properties_change(session)

    def __on_sessions_changed(sender, args = None):
        sessions = sender.get_sessions()
        idsCurrent = MediaManager.__current_media_sessions.keys()
        ids = list(map(lambda x: x.source_app_user_model_id, sessions))
        idsToRemove = list(filter(lambda x: not any(x == id for id in ids), idsCurrent))
        sessionsToAdd = list(filter(lambda x: x.source_app_user_model_id not in idsCurrent, sessions))
        idsToAdd = list(map(lambda x: x.source_app_user_model_id, sessionsToAdd))
        for id in idsToRemove:
            MediaManager.__remove_session(MediaManager.__current_media_sessions[id].control_session)
        for session in sessionsToAdd:
            media_session = MediaManager.MediaSession(session)
            MediaManager.__current_media_sessions[session.source_app_user_model_id] = media_session
            if MediaManager.__on_new_source:
                MediaManager.__on_new_source(session)
            MediaManager.MediaSession.on_media_properties_change(session)

    def __remove_session(session):
        id = session.source_app_user_model_id
        mpc_token = MediaManager._MediaManager__mpc_tokens.pop(id)
        pic_token = MediaManager._MediaManager__pic_tokens.pop(id)
        session.remove_media_properties_changed(mpc_token)
        session.remove_playback_info_changed(pic_token)
        MediaManager.__current_media_sessions.pop(id)
        if MediaManager.__on_removed_source:
            MediaManager.__on_removed_source(session)

    class MediaSession:
        control_session = None
        __last_song = None
        def __init__(self, control_session):
            self.control_session = control_session
            id = control_session.source_app_user_model_id
            MediaManager._MediaManager__mpc_tokens[id] = control_session.add_media_properties_changed(MediaManager.MediaSession.on_media_properties_change)
            MediaManager._MediaManager__pic_tokens[id] = control_session.add_playback_info_changed(MediaManager.MediaSession.on_playback_info_changed)
        def on_playback_info_changed(session, args = None):
            props = session.get_playback_info()
            if MediaManager._MediaManager__on_playback_info_changed:
                MediaManager._MediaManager__on_playback_info_changed(session, props)
        def on_media_properties_change(session, args = None):
            try:
                props = async_to_sync(session.try_get_media_properties_async)()
                song = f'{props.title} | {props.artist}'
                id = session.source_app_user_model_id
                if MediaManager.MediaSession.__last_song != song and not (props.title is None and props.title.isspace() and props.artist is None and props.artist.isspace()) :
                    MediaManager.MediaSession.__last_song = song
                    if MediaManager._MediaManager__on_media_properties_changed:
                        MediaManager._MediaManager__on_media_properties_changed(session, props)
            except: pass