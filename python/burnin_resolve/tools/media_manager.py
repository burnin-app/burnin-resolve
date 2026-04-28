import os
import re
import sys
import time

import burnin
import DaVinciResolveScript as dvr
from burnin.entity.filetype import FileType, Image, Video
from burnin.entity.node import Node
from burnin.entity.surreal import Thing
from burnin.entity.utils import TypeWrapper, node_name_from_component_path
from burnin.entity.version import Version, VersionStatus
from burnin.path import build_path_from_node
from burnin.show.shot import BU_shot
from burnin.utils import to_printf_pattern
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
            self.buEntityListCb = ComboBox(
                "Entity", self.BU_shot.get_shot_entity_types("resolve")
            )
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

            # version
            self.buVersionListCb = ComboBox("Version", ["Latest", "Atop"])
            self.layout.addWidget(self.buVersionListCb)

            # input transform
            self.setAcesInputTransform = QCheckBox("Set ACES Input Transform")
            self.setAcesInputTransform.setChecked(True)
            self.layout.addWidget(self.setAcesInputTransform)

            self.actionTypeCb = ComboBox(
                "Action", ["Import Media", "Render Delivery Mp4"]
            )
            self.layout.addWidget(self.actionTypeCb)

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
        version_list: list[str] = ["Latest", "Atop"]
        component_version_list: list[str] = self.BU_shot.load_component_version_list()
        if component_version_list:
            version_list = version_list + component_version_list
            self.buVersionListCb.set_items(version_list)

    def getComponentNodeId(self) -> Thing | None:
        if self.root_id and self.bu_show:
            id: Thing = Thing.from_ids(self.root_id, "@/show:" + self.bu_show)
            id = id.join("sequences")
            id = id.join("seq:" + self.buSeqListCb.current_text())
            id = id.join("shot:" + self.buShotListCb.current_text())
            id = id.join("publishes")
            id = id.join(self.buEntityListCb.current_text())
            id = id.join(self.buComponentListCb.current_text())
            return id
        else:
            return None

    def onBuildClicked(self):
        selected_version = self.buVersionListCb.current_text()
        if self.BU_shot:
            component_id = self.getComponentNodeId()
            if component_id:
                version_id = component_id.join(selected_version)
                try:
                    version_node = self.BU_shot.burnin_client.get_version_node(
                        version_id
                    )
                    if not version_node.node_type.variant_name == "Version":
                        raise Exception(
                            f"Invalid node type: {version_node.node_type.variant_name}"
                        )

                    type = self.actionTypeCb.current_text()

                    # self.resolve = dvr.scriptapp("Resolve")
                    # self.pm = self.resolve.GetProjectManager()
                    # self.project = self.pm.GetCurrentProject()
                    self.rs.invoke()

                    if not self.rs.project:
                        print("No project open")
                        exit()
                    if type == "Import Media":
                        self.import_media(version_node)
                    elif type == "Render Delivery Mp4":
                        clip_name = self.import_media(version_node)
                        self.renderDeliveryMp4(clip_name)

                except Exception as e:
                    print(e)

    def import_media(self, version_node: Node):
        node_file_path = build_path_from_node(version_node)
        node_type: Version = version_node.node_type.data
        file_type = node_type.file_type.data
        if isinstance(file_type, Image):
            if node_type.head_file:
                file_path = node_file_path / node_type.head_file
                clip_name = node_type.head_file
                file_path = file_path.as_posix()
                sequence = str(file_path)

                if file_type.time_dependent and file_type.frame_range:
                    file_path = to_printf_pattern(str(file_path))
                    start = int(file_type.frame_range[0])
                    end = int(file_type.frame_range[1])
                    sequence = {
                        "FilePath": file_path,
                        "StartIndex": start,
                        "EndIndex": end,
                    }
                    clip_name = Resolve.resovle_sequence_clip_name(
                        clip_name, start, end
                    )
                    print(clip_name)

                clips = self.rs.importMedia([sequence])
                if clips:
                    print("EXR sequence imported correctly")
                else:
                    print("Import failed")

                print(sequence)
                return clip_name

        else:
            raise Exception(
                f"Node is not an Image Type: {version_node.node_type.variant_name}"
            )

    def renderDeliveryMp4(self, clip_name):
        id: Thing = self.BU_shot.component_node_id
        name = id.get_name_from_id()
        if self.bu_show:
            id.id.String = "@/show:" + self.bu_show
        id = id.join("sequences")
        id = id.join("seq:" + self.buSeqListCb.current_text())
        id = id.join("shot:" + self.buShotListCb.current_text())
        id = id.join("publishes")
        id = id.join("delivery")
        id = id.join(name + "_Mp4")
        component_id = id.join("v000")

        version_node = Node.new_version(component_id, FileType.Video)
        try:
            version_node: Node = (
                self.BU_shot.burnin_client.create_or_update_component_version(
                    version_node
                )
            )

            print(version_node, "VERSION NODe")

            file_path = build_path_from_node(version_node)
            file_name = node_name_from_component_path(version_node.id.id.String)
            print(file_path, file_name)
            self.rs.invoke()
            tl = self.rs.set_current_timeline("Mp4Export")

            clip = self.rs.get_clip_from_name(clip_name)
            if self.setAcesInputTransform.isChecked():
                clip.SetClipProperty("IDT", "ACEScg - CSC")

            self.rs.clear_timeline("Mp4Export")
            self.rs.append_to_timeline([clip])

            mp4_render_settings(self.rs, str(file_path), str(file_name))

            job_id = self.rs.add_render_job()
            if not job_id:
                print("Failed to create render job")
                exit()
            print(f"Created job: {job_id}")
            self.rs.start_rendering(job_id)

            print("Rendering started...")

            # ----------------------------------------
            # 5. Wait until render finishes
            # ----------------------------------------
            while self.rs.is_rendering_in_progress():
                time.sleep(1)

            print("✅ Render finished!")

            version_type: Version = version_node.node_type.data
            version_type.comment = "Auto Convert From Davinci Resolve"
            version_type.software = "resolve"
            version_type.head_file = str(file_name) + ".mp4"
            version_type.status = VersionStatus.Published

            file_type: Video = version_type.file_type.data
            file_type.file_name = str(file_name)
            file_type.file_format = "mp4"
            render_format_codecs = self.rs.project.GetCurrentRenderFormatAndCodec()
            file_type.codec = (
                render_format_codecs["format"] + " - " + render_format_codecs["codec"]
            )
            width = self.rs.project.GetSetting("timelineResolutionWidth")
            height = self.rs.project.GetSetting("timelineResolutionHeight")
            file_type.resolution = (int(width), int(height))
            file_type.has_audio = False
            file_type.frame_rate = self.rs.project.GetSetting("timelineFrameRate")
            file_type.duration = tl.GetEndFrame()

            version_type.file_type = TypeWrapper(file_type)
            version_node.node_type = TypeWrapper(version_type)
            version_node.created_at = None

            version_node = self.BU_shot.burnin_client.commit_component_version(
                version_node
            )
            version_node_type: Version = version_node.node_type.data
            print(version_node)
            print(version_node_type)

        except Exception as e:
            print(str(e))


def run():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = MainWindow()
    window.setWindowTitle("Show Media Manager")
    media_manager = MediaManager()
    window.add_widget(media_manager)
    window.show()
    sys.exit(app.exec())


def mp4_render_settings(rs: Resolve, target_dir, custom_name):
    rs.resolve.OpenPage("deliver")
    settings = {
        "SelectAllFrames": True,
        "TargetDir": target_dir,
        "CustomName": custom_name,
    }

    rs.set_render_settings(settings)
    render_codecs = rs.project.GetRenderCodecs("MP4")
    render_codec = "H264"
    if "H.264 NVIDIA" in render_codecs.keys():
        render_codec += "_NVIDIA"
    rs.project.SetCurrentRenderFormatAndCodec("MP4", render_codec)
