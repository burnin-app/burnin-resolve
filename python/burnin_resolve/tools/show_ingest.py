import os
import re
import sys
import time

import burnin
import DaVinciResolveScript as dvr
from burnin.entity.filetype import FileType, Image
from burnin.entity.node import Node
from burnin.entity.surreal import Thing
from burnin.entity.utils import TypeWrapper, node_name_from_component_path
from burnin.entity.version import Version, VersionStatus
from burnin.path import build_path_from_node
from burnin.show.shot import BU_shot
from burnin.utils import rename_file_sequence
from burnin_resolve.resolve import Resolve
from burnin_resolve.ui.widgets import ComboBox, Label
from burnin_resolve.ui.window import MainWindow
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MediaManager(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)  # small outer padding
        self.layout.setSpacing(6)
        self.timeline_name = "IngestExr"

        # root name
        self.roots = dvr._burnin_local_roots
        self.root_id = os.getenv("BURNIN_ROOT_ID")
        self.root_name = os.getenv("BURNIN_ROOT_NAME")
        self.rs = Resolve()

        if self.root_name and self.root_id:
            self.ui()

    def ui(self):
        self.root_name_la = Label("Root Name", self.root_name)
        self.root_id_la = Label("Root Id", self.root_id)
        self.layout.addWidget(self.root_name_la)
        self.layout.addWidget(self.root_id_la)

        self.bu_show = os.getenv("BU_show")
        self.bu_seq = os.getenv("BU_seq")
        self.bu_shot = os.getenv("BU_shot")

        if self.bu_show:
            self.showLa = Label("Show", self.bu_show)
            self.layout.addWidget(self.showLa)
            self.BU_shot = BU_shot(self.root_id, self.bu_show)

            # sequence
            self.BU_shot.load_seq_list()
            self.buSeqListCb = ComboBox("Sequence", self.BU_shot.seq_name_list)
            self.buSeqListCb.currentTextChanged.connect(self.onSeqChanged)
            self.layout.addWidget(self.buSeqListCb)
            selected_seq = self.buSeqListCb.current_text()

            # shot
            self.BU_shot.load_shot_list(selected_seq)
            self.buShotListCb = ComboBox("Shot", self.BU_shot.shot_names_list)
            self.buShotListCb.currentTextChanged.connect(self.onShotChanged)
            self.layout.addWidget(self.buShotListCb)

            # shot entity
            self.buEntityListCb = ComboBox("Entity", ["plates"])
            self.BU_shot.current_entity = self.buEntityListCb.current_text()
            self.buEntityListCb.currentTextChanged.connect(self.onEntityChanged)
            self.layout.addWidget(self.buEntityListCb)

            # components
            self.BU_shot.load_component_list()
            self.buComponentListCb = ComboBox(
                "Component", self.BU_shot.component_name_list
            )
            self.buComponentListCb.currentTextChanged.connect(self.onComponentChanged)
            self.layout.addWidget(self.buComponentListCb)

            self.actionTypeCb = ComboBox("Action", ["Ingest"])
            self.layout.addWidget(self.actionTypeCb)

            self.createIngestTimelineButton = QPushButton("Create Ingest Timeline")
            self.layout.addWidget(self.createIngestTimelineButton)
            self.createIngestTimelineButton.clicked.connect(self.onCreateIngestTimeline)

            self.buildButton = QPushButton("Build")
            self.layout.addWidget(self.buildButton)
            self.buildButton.clicked.connect(self.onBuildClicked)

    def onSeqChanged(self):
        selected_seq = self.buSeqListCb.current_text()
        self.BU_shot.current_seq = selected_seq
        self.BU_shot.load_shot_list(selected_seq)
        self.buShotListCb.set_items(self.BU_shot.shot_names_list)
        self.onShotChanged()

    def onShotChanged(self):
        selected_shot = self.buShotListCb.current_text()
        self.BU_shot.current_shot = selected_shot
        self.updateComponentList()

    def onEntityChanged(self):
        self.BU_shot.current_entity = self.buEntityListCb.current_text()
        self.updateComponentList()

    def updateComponentList(self):
        self.BU_shot.load_component_list()
        self.buComponentListCb.set_items(self.BU_shot.component_name_list)
        self.onComponentChanged()

    def onComponentChanged(self):
        selected_component = self.buComponentListCb.current_text()
        self.BU_shot.current_component = selected_component

    def onBuildClicked(self):
        if self.BU_shot and self.root_id and self.bu_show:
            id: Thing = Thing.from_ids(self.root_id, "@/show:" + self.bu_show)
            id = id.join("sequences")
            id = id.join("seq:" + self.buSeqListCb.current_text())
            id = id.join("shot:" + self.buShotListCb.current_text())
            id = id.join("publishes")
            id = id.join(self.buEntityListCb.current_text())
            id = id.join(self.buComponentListCb.current_text())
            print(id)

            if not self.rs.project:
                print("No project open")
                exit()

            type = self.actionTypeCb.current_text()
            if type == "Ingest":
                self.renderPlateExr(id)

    def get_ingest_timeline(self):
        pass

    def onCreateIngestTimeline(self):
        self.rs.get_timeline(self.timeline_name)
        self.rs.set_current_timeline(self.timeline_name)

    def renderPlateExr(self, component_id: Thing):
        component_id = component_id.join("v000")
        print(component_id)
        self.rs.invoke()
        self.rs.set_current_timeline(self.timeline_name)
        clips = self.rs.get_clips_form_timeline(self.timeline_name)
        if len(clips) > 0:
            clip = clips[0]
            print(clip, "clip0")
            clip = clip.GetMediaPoolItem()
            clip_name = clip.GetName()
            clip_prop = clip.GetClipProperty()
            frames = clip_prop["Frames"]
            print(clip_prop)

            version_node = Node.new_version(component_id, FileType.Image)
            try:
                version_node: Node = (
                    self.BU_shot.burnin_client.create_or_update_component_version(
                        version_node
                    )
                )

                file_path = build_path_from_node(version_node)
                file_name = node_name_from_component_path(version_node.id.id.String)
                print(file_path, file_name)

                self.rs.resolve.OpenPage("deliver")
                settings = {
                    "SelectAllFrames": True,
                    "TargetDir": str(file_path),
                    "CustomName": str(file_name),
                }
                self.rs.set_render_settings(settings)
                # render_codecs = self.rs.project.GetRenderCodecs("EXR")
                self.rs.project.SetCurrentRenderFormatAndCodec("EXR", "RGBHalf")

                job_id = self.rs.add_render_job()
                if not job_id:
                    print("Failed to create render job")
                    exit()
                print(f"Created job: {job_id}")
                self.rs.start_rendering(job_id)

                print("Rendering started...")

                while self.rs.is_rendering_in_progress():
                    time.sleep(1)

                print("✅ Render finished!")

                version_type: Version = version_node.node_type.data
                version_type.comment = "Ingested from Resolve"
                version_type.software = "resolve"
                version_type.head_file = str(file_name) + ".####.exr"
                version_type.status = VersionStatus.Published

                file_type: Image = version_type.file_type.data
                file_type.file_name = str(file_name)
                file_type.file_format = "exr"
                width = self.rs.project.GetSetting("timelineResolutionWidth")
                height = self.rs.project.GetSetting("timelineResolutionHeight")
                file_type.resolution = (int(width), int(height))
                start = 0
                end = 0
                if frames:
                    start = 1001
                    end = start + (int(frames) - 1)

                file_type.frame_range = [start, end, 1]
                file_type.time_dependent = True

                print(file_type)

                version_type.file_type = TypeWrapper(file_type)
                version_node.node_type = TypeWrapper(version_type)
                version_node.created_at = None

                version_node = self.BU_shot.burnin_client.commit_component_version(
                    version_node
                )
                version_node_type: Version = version_node.node_type.data
                print(version_node)
                print(version_node_type)

                rename_file_sequence(str(file_path), str(file_name), 1001, "exr")

            except Exception as e:
                print(str(e))


def run():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = MainWindow()
    window.setWindowTitle("Show Ingest Exr")
    media_manager = MediaManager()
    window.add_widget(media_manager)
    window.show()
    sys.exit(app.exec())


def mp4_render_settings(resolve, project, target_dir, custom_name):
    resolve.OpenPage("deliver")
    settings = {
        "SelectAllFrames": True,
        "TargetDir": target_dir,
        "CustomName": custom_name,
    }

    project.SetRenderSettings(settings)
    render_codecs = project.GetRenderCodecs("MP4")
    render_codec = "H264"
    if "H.264 NVIDIA" in render_codecs.keys():
        render_codec += "_NVIDIA"
    project.SetCurrentRenderFormatAndCodec("MP4", render_codec)
