# def run():
#     resolve = dvr.scriptapp("Resolve")
#     pm = resolve.GetProjectManager()
#     project = pm.GetCurrentProject()
#     if not project:
#         print("No project open")
#         exit()
#     media_pool = project.GetMediaPool()
# # 👇 Proper sequence definition
# sequence = {
#     "FilePath": "X:/show_root/shows/Raawadi/sequences/CTT/CTT_1010/publishes/plates/original/v001/Raawadi_CTT_CTT_1010_original_v001.%04d.exr",
#     "StartIndex": 1001,
#     "EndIndex": 1100,
# }
# clips = media_pool.ImportMedia([sequence])
# if clips:
#     print("EXR sequence imported correctly")
# else:
#     print("Import failed")
#
## SET IDT
# root_folder = media_pool.GetRootFolder()
# clip_list = root_folder.GetClipList()
# first_clip_properties = clip_list[0].GetClipProperty(propertyName=None)
# clip_list[0].SetClipProperty("IDT", "Sony SLog3 SGamut3")
# timeline = media_pool.CreateTimelineFromClips("Burnin_Timeline", [clip_list[0]])
# settings = {
#     "SelectAllFrames": True,
#     "TargetDir": "X:/renders/output",
#     "CustomName": "burnin_output",
#     "Format": "exr",
#     "VideoCodec": "RGBFloat",  # important for EXR
# }
# project.SetRenderSettings(settings)
import sys
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
import DaVinciResolveScript as dvr

def run():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Resolve Tool")
    window.setGeometry(100, 100, 300, 200)

    button = QPushButton("Click Me", window)
    button.setGeometry(100, 80, 100, 40)
    button.clicked.connect(lambda: print("hello"))

    window.show()
    app.exec()

if __name__ == "__main__":
    run()
