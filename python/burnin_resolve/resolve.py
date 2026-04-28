import re

import DaVinciResolveScript as dvr


class Resolve:
    def __init__(self):
        self.invoke()

    def invoke(self):
        self.resolve = dvr.scriptapp("Resolve")
        self.pm = self.resolve.GetProjectManager()
        self.project = self.pm.GetCurrentProject()
        self.media_pool = self.project.GetMediaPool()

    def importMedia(self, sequence: list[str] | list[dict]):
        media_pool = self.project.GetMediaPool()
        clips = media_pool.ImportMedia(sequence)
        return clips

    def reloadMediaPool(self):
        self.media_pool = self.project.GetMediaPool()

    def get_timeline(self, timeline_name: str):
        """
        Creates new timeline if not exists
        """

        timeline = None

        timeline_count = self.project.GetTimelineCount()

        for i in range(1, timeline_count + 1):
            tl = self.project.GetTimelineByIndex(i)
            if tl.GetName() == timeline_name:
                timeline = tl
                break

        if not timeline:
            timeline = self.media_pool.CreateEmptyTimeline(timeline_name)

        return timeline

    def clear_timeline(self, timeline_name: str):
        timeline = self.get_timeline(timeline_name)
        if timeline:
            for track_type in ["video", "audio"]:
                track_count = timeline.GetTrackCount(track_type)

                for i in range(1, track_count + 1):
                    items = timeline.GetItemListInTrack(track_type, i)
                    if items:
                        timeline.DeleteClips(items)

    def set_current_timeline(self, timeline_name: str):
        timeline = self.get_timeline(timeline_name)
        self.project.SetCurrentTimeline(timeline)
        return timeline

    def get_clip_from_name(self, clip_name: str):
        root_folder = self.media_pool.GetRootFolder()
        clip_list = root_folder.GetClipList()
        for clip in clip_list:
            if clip:
                name = clip.GetName()
                if name == clip_name:
                    return clip

        return None

    def get_clips_form_timeline(self, timeline_name: str):
        timeline = self.get_timeline(timeline_name)
        clips = []
        if timeline:
            track_count = timeline.GetTrackCount("video")
            for track_index in range(1, track_count + 1):
                items = timeline.GetItemListInTrack("video", track_index)

                if items:
                    clips.extend(items)
        return clips

    def set_clip_property(self, clip_name: str, key: str, value: str):
        clip = self.get_clip_from_name(clip_name)
        if clip:
            clip.SetClipProperty(key, value)
            return clip
        else:
            return None

    def append_to_timeline(self, clips: list):
        self.media_pool.AppendToTimeline(clips)

    def add_render_job(self) -> str:
        job_id = self.project.AddRenderJob()
        return job_id

    def start_rendering(self, job_id: str):
        self.project.StartRendering(job_id)

    def is_rendering_in_progress(self):
        i = self.project.IsRenderingInProgress()
        return i

    def set_render_settings(self, settings):
        self.project.SetRenderSettings(settings)

    @staticmethod
    def resovle_sequence_clip_name(name: str, start: int, end: int) -> str:
        match = re.search(r"(#+)", name)
        if match:
            hashes = match.group(1)
            range = "[" + str(int(start)) + "-" + str(int(end)) + "]"
            return name.replace(hashes, range)
        return name
